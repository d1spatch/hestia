"""Recipe YAML parsing, validation, and nutrition/cost computation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, field_validator, model_validator
from rich import print as rprint


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class RecipeIngredient(BaseModel):
    """A single ingredient line in a recipe.

    Attributes:
        name: Ingredient name. Must match a catalog entry name or alias for
            nutrition/cost to be computed.
        amount: Numeric quantity (must be > 0).
        unit: Unit of measurement, e.g. `g`, `ml`, `kg`, `tsp`, `piece`.
    """

    name: str
    amount: float
    unit: str  # g, ml, kg, L, tsp, tbsp, cup, piece, etc.
    optional: bool = False
    note: str = ""
    nutrition_pct: float = 100.0  # % of ingredient that counts toward nutrition (not cost)

    @field_validator("amount")
    @classmethod
    def positive_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("amount must be positive")
        return v


class InstructionGroup(BaseModel):
    """A named section of instructions (e.g. 'Crust', 'Filling')."""

    section: str
    steps: list[str]


class IngredientGroup(BaseModel):
    """A named group of ingredients (e.g. 'Crust', 'Filling')."""

    group: str
    items: list[RecipeIngredient]


class Recipe(BaseModel):
    """A complete recipe parsed from a YAML file.

    Attributes:
        name: Display name of the recipe.
        serves: Serving description — can be a string (e.g. `"1 loaf"`), int, or float.
        tags: Freeform tags for organisation.
        ingredients: Flat or grouped ingredient list.
        instructions: Ordered list of instruction steps.
        notes: Freeform notes (multiline text).
    """

    name: str
    serves: str | int | float = 1
    total_recipe_grams: float | None = None  # override computed ingredient sum (e.g. accounts for cooking loss)
    tags: list[str] = []
    ingredients: list[IngredientGroup | RecipeIngredient] = []
    instructions: list[InstructionGroup | str] = []
    notes: str = ""

    @model_validator(mode="before")
    @classmethod
    def normalize_instructions(cls, data: Any) -> Any:
        instr = data.get("instructions")
        if isinstance(instr, dict):
            data["instructions"] = [
                {"section": k, "steps": v} for k, v in instr.items()
            ]
        return data

    @property
    def all_ingredients(self) -> list[RecipeIngredient]:
        """Flat list of all ingredients regardless of grouping."""
        result: list[RecipeIngredient] = []
        for item in self.ingredients:
            if isinstance(item, IngredientGroup):
                result.extend(item.items)
            else:
                result.append(item)
        return result

    @property
    def slug(self) -> str:
        """Filesystem-safe identifier derived from the recipe name.

        Lowercases the name, replaces spaces with underscores and slashes with hyphens.
        Used as the base filename for rendered output.
        """
        return self.name.lower().replace(" ", "_").replace("/", "-")


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def load_recipe(path: Path) -> Recipe:
    """Parse and validate a single YAML recipe file.

    Args:
        path: Path to the `.yaml` / `.yml` recipe file.

    Returns:
        A validated `Recipe` instance.

    Raises:
        ValidationError: If the YAML structure doesn't match the recipe schema.
        FileNotFoundError: If the file doesn't exist.
    """
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return Recipe.model_validate(data)


def load_all_recipes(recipes_dir: Path) -> list[tuple[Path, Recipe]]:
    """Load every `*.yaml` / `*.yml` file in a directory.

    Files that fail to parse are skipped with a warning printed to stdout.

    Args:
        recipes_dir: Directory to search for recipe files.

    Returns:
        List of `(path, recipe)` tuples, sorted by filename.
    """
    results: list[tuple[Path, Recipe]] = []
    for p in sorted(recipes_dir.glob("*.y*ml")):
        try:
            results.append((p, load_recipe(p)))
        except Exception as exc:
            # Surface parse errors without crashing the whole list
            rprint(f"[yellow][warn][/yellow] Could not load {p.name}: {exc}")
    return results


# ---------------------------------------------------------------------------
# Computation helpers
# ---------------------------------------------------------------------------

# Exact weight-unit conversions to grams.
_GRAM_CONVERSIONS: dict[str, float] = {
    "g": 1.0,
    "kg": 1000.0,
    "mg": 0.001,
    "oz": 28.3495,
    "lb": 453.592,
}

# Metric volume units — multiplier to get mL from the given unit.
# Grams = mL * g_per_ml (defaults to water density 1.0 if not in catalog).
_ML_CONVERSIONS: dict[str, float] = {
    "ml": 1.0,
    "l": 1000.0,
    "cl": 10.0,
    "dl": 100.0,
}

# Ratios relative to tbsp for cooking volume units.
_TBSP_RATIOS: dict[str, float] = {
    "tsp": 1 / 3,
    "tbsp": 1.0,
    "cup": 16.0,
}


def to_grams(
    amount: float,
    unit: str,
    g_per_tbsp: float | None = None,
    g_per_ml: float | None = None,
    unit_sizes: dict[str, float] | None = None,
    g_per_unit: float | None = None,
) -> float | None:
    """Convert an ingredient quantity to grams.

    Handles weight units (`g`, `kg`, `mg`, `oz`, `lb`), metric volume units
    that approximate water density (`ml`, `l`, `cl`, `dl`), cooking volume
    units (`tsp`, `tbsp`, `cup`) when *g_per_tbsp* is supplied, named natural
    units (e.g. `whole`, `clove`, `square`) when *unit_sizes* is supplied, and
    the generic `unit` unit when *g_per_unit* is supplied.

    Args:
        amount: Numeric quantity.
        unit: Unit string (case-insensitive).
        g_per_tbsp: Grams per tablespoon (catalog field). Converts tsp/tbsp/cup
            via fixed ratios (1 tbsp = 3 tsp = 1/16 cup).
        g_per_ml: Grams per mL (catalog field). Converts ml/l/cl/dl. Falls back
            to water density (1.0 g/mL) if not provided.
        unit_sizes: Dict mapping unit name → grams per unit (catalog field).
            E.g. ``{"whole": 100.0, "clove": 5.0, "square": 30.0}``.
        g_per_unit: Grams per generic unit (catalog field). Used when unit is
            ``"unit"`` (e.g. ``amount: 2, unit: unit`` for 2 average limes).

    Returns:
        Equivalent mass in grams, or `None` if the unit cannot be converted.
    """
    u = unit.lower()
    weight_factor = _GRAM_CONVERSIONS.get(u)
    if weight_factor is not None:
        return amount * weight_factor
    ml_factor = _ML_CONVERSIONS.get(u)
    if ml_factor is not None:
        return amount * ml_factor * (g_per_ml if g_per_ml is not None else 1.0)
    if g_per_tbsp is not None:
        ratio = _TBSP_RATIOS.get(u)
        if ratio is not None:
            return amount * ratio * g_per_tbsp
    if u == "unit" and g_per_unit is not None:
        return amount * g_per_unit
    if unit_sizes and u in unit_sizes:
        return amount * unit_sizes[u]
    return None


def compute_nutrition(
    recipe: Recipe,
    catalog: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Compute total cost and calories for a recipe from the ingredient catalog.

    Ingredients whose unit cannot be converted to grams (e.g. `piece`, `tsp`)
    are included in `missing_ingredients` for informational purposes but do not
    cause an error.

    Args:
        recipe: A validated `Recipe` instance.
        catalog: Mapping of lowercase ingredient name to catalog dict
            (as returned by `db.get_ingredient`).

    Returns:
        A dict with keys:

        - `cost` (`float`): Total estimated cost in the catalog currency.
        - `currency` (`str`): Currency code of the first matched ingredient.
        - `calories` (`float`): Total kilocalories for the recipe.
        - `missing_ingredients` (`list[str]`): Names with no catalog entry.
    """
    total_cost = 0.0
    missing: list[str] = []
    currency = "USD"
    cost_breakdown: list[dict] = []
    ingredient_breakdown: list[dict] = []

    # Macro/micro totals — keyed by catalog field name
    _nutrient_fields = (
        "calories_per_100g",
        "protein_per_100g",
        "carbs_per_100g",
        "fat_per_100g",
        "fiber_per_100g",
        "sugar_per_100g",
        "sodium_per_100g",
        "saturated_fat_per_100g",
        "cholesterol_per_100g",
        # Vitamins & minerals (mg or mcg per 100g)
        "vitamin_c_per_100g",
        "vitamin_d_per_100g",
        "vitamin_k_per_100g",
        "calcium_per_100g",
        "iron_per_100g",
        "magnesium_per_100g",
        "potassium_per_100g",
        "manganese_per_100g",
    )
    totals: dict[str, float] = {f: 0.0 for f in _nutrient_fields}
    
    #print("recipe:")
    #print(recipe.all_ingredients)#JK
    #print("catalog:")
    #print(catalog.get('sugar'))
    for ing in recipe.all_ingredients:
        entry = catalog.get(ing.name.lower())
        if entry is None:
            print(f"Missing Price info Ingredient:{ing.name}")
            missing.append(ing.name)
            continue

        grams = to_grams(ing.amount, ing.unit, entry.get("g_per_tbsp"), entry.get("g_per_ml"), entry.get("unit_sizes"), entry.get("g_per_unit"))
        if grams is None:
            g_per_unit = entry.get("g_per_unit")
            if g_per_unit is not None:
                print(f"{ing.name}: Unrecognized unit '{ing.unit}', falling back to g_per_unit ({g_per_unit}g)")
                grams = ing.amount * g_per_unit
            else:
                print(f"{ing.name}: Unrecognized unit '{ing.unit}', no gram conversion available")
                continue

        ing_cost: float | None = None
        if entry.get("price_per_kg") is not None:
            print(f"{entry['name']}: {entry['price_per_kg']}")
            _ic: float = float(entry["price_per_kg"]) * (grams / 1000.0)
            total_cost += _ic
            ing_cost = _ic
            currency = entry.get("currency", "USD")
            cost_breakdown.append({"name": ing.name, "cost": round(_ic, 4)})
        else:
            print(f"{entry['name']}: No price available")

        nutrition_scale = (grams / 100.0) * (ing.nutrition_pct / 100.0)
        ing_nutrients: dict[str, float] = {}
        for field in _nutrient_fields:
            if entry.get(field) is not None:
                value = entry[field] * nutrition_scale
                totals[field] += value
                ing_nutrients[field] = value

        ingredient_breakdown.append({
            "name": ing.name,
            "grams": round(grams, 2),
            "cost": round(ing_cost, 4) if ing_cost is not None else None,
            "calories": round(ing_nutrients.get("calories_per_100g", 0), 1),
            "protein": round(ing_nutrients.get("protein_per_100g", 0), 1),
            "carbs": round(ing_nutrients.get("carbs_per_100g", 0), 1),
            "fat": round(ing_nutrients.get("fat_per_100g", 0), 1),
            "fiber": round(ing_nutrients.get("fiber_per_100g", 0), 1),
            "sugar": round(ing_nutrients.get("sugar_per_100g", 0), 1),
            "sodium_mg": round(ing_nutrients.get("sodium_per_100g", 0) * 1000, 1),
            "saturated_fat": round(ing_nutrients.get("saturated_fat_per_100g", 0), 1),
            "cholesterol_mg": round(ing_nutrients.get("cholesterol_per_100g", 0) * 1000, 1),
            "calcium_mg": round(ing_nutrients.get("calcium_per_100g", 0), 1),
            "iron_mg": round(ing_nutrients.get("iron_per_100g", 2), 2),
            "potassium_mg": round(ing_nutrients.get("potassium_per_100g", 0), 1),
            "magnesium_mg": round(ing_nutrients.get("magnesium_per_100g", 0), 1),
        })

    # Parse serves into a numeric count for per-serving math
    import re as _re
    serves_raw = recipe.serves
    serves_count: float = 1.0
    if isinstance(serves_raw, (int, float)):
        serves_count = float(serves_raw)
    else:
        m = _re.search(r"[\d.]+", str(serves_raw))
        if m:
            serves_count = float(m.group())
    if serves_count <= 0:
        serves_count = 1.0

    ingredient_grams = sum(i["grams"] for i in ingredient_breakdown)
    total_grams = recipe.total_recipe_grams if recipe.total_recipe_grams is not None else ingredient_grams

    grams_per_serving = total_grams / serves_count
    # Scale factor: what fraction of total recipe nutrients go into one serving
    serving_scale = grams_per_serving / ingredient_grams if ingredient_grams > 0 else (1.0 / serves_count)

    return {
        "cost": round(total_cost, 2),
        "serves_count": serves_count,
        "total_grams": round(ingredient_grams, 1),
        "grams_per_serving": round(grams_per_serving, 1),
        "serving_scale": serving_scale,
        "currency": currency,
        "cost_breakdown": cost_breakdown,
        "ingredient_breakdown": ingredient_breakdown,
        "calories": round(totals["calories_per_100g"], 1),
        "protein": round(totals["protein_per_100g"], 1),
        "carbs": round(totals["carbs_per_100g"], 1),
        "fat": round(totals["fat_per_100g"], 1),
        "fiber": round(totals["fiber_per_100g"], 1),
        "sugar": round(totals["sugar_per_100g"], 1),
        "sodium_mg": round(totals["sodium_per_100g"] * 1000, 1),
        "saturated_fat": round(totals["saturated_fat_per_100g"], 1),
        "cholesterol_mg": round(totals["cholesterol_per_100g"] * 1000, 1),
        # Vitamins & minerals
        "vitamin_c_mg": round(totals["vitamin_c_per_100g"], 2),
        "vitamin_d_mcg": round(totals["vitamin_d_per_100g"], 2),
        "vitamin_k_mcg": round(totals["vitamin_k_per_100g"], 2),
        "calcium_mg": round(totals["calcium_per_100g"], 1),
        "iron_mg": round(totals["iron_per_100g"], 2),
        "magnesium_mg": round(totals["magnesium_per_100g"], 1),
        "potassium_mg": round(totals["potassium_per_100g"], 1),
        "manganese_mg": round(totals["manganese_per_100g"], 3),
        "missing_ingredients": missing,
    }
