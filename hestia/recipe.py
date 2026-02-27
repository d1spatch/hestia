"""Recipe YAML parsing, validation, and nutrition/cost computation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, field_validator


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

    @field_validator("amount")
    @classmethod
    def positive_amount(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("amount must be positive")
        return v


class Recipe(BaseModel):
    """A complete recipe parsed from a YAML file.

    Attributes:
        name: Display name of the recipe.
        serves: Serving description — can be a string (e.g. `"1 loaf"`), int, or float.
        tags: Freeform tags for organisation.
        ingredients: Ordered list of ingredients with amounts and units.
        instructions: Ordered list of instruction steps.
        notes: Freeform notes (multiline text).
    """

    name: str
    serves: str | int | float = 1
    tags: list[str] = []
    ingredients: list[RecipeIngredient]
    instructions: list[str]
    notes: str = ""

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
            print(f"[warn] Could not load {p.name}: {exc}")
    return results


# ---------------------------------------------------------------------------
# Computation helpers
# ---------------------------------------------------------------------------

# Unit conversion to grams (for weight-based nutrients/cost).
# For non-weight units we return None and skip the computation.
_GRAM_CONVERSIONS: dict[str, float] = {
    "g": 1.0,
    "kg": 1000.0,
    "mg": 0.001,
    "oz": 28.3495,
    "lb": 453.592,
    "ml": 1.0,   # approximate: water density = 1 g/ml
    "l": 1000.0,
    "cl": 10.0,
    "dl": 100.0,
}


def to_grams(amount: float, unit: str) -> float | None:
    """Convert an ingredient quantity to grams.

    Handles weight units (`g`, `kg`, `mg`, `oz`, `lb`) and volume units that
    approximate water density (`ml`, `l`, `cl`, `dl`).

    Args:
        amount: Numeric quantity.
        unit: Unit string (case-insensitive).

    Returns:
        Equivalent mass in grams, or `None` if the unit cannot be converted
        (e.g. `tsp`, `piece`, `cup`).
    """
    factor = _GRAM_CONVERSIONS.get(unit.lower())
    if factor is None:
        return None
    return amount * factor


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
    total_calories = 0.0
    missing: list[str] = []
    currency = "USD"

    for ing in recipe.ingredients:
        entry = catalog.get(ing.name.lower())
        if entry is None:
            missing.append(ing.name)
            continue

        grams = to_grams(ing.amount, ing.unit)
        if grams is None:
            # Can't compute nutrition for non-weight units (e.g. "1 piece")
            continue

        if entry.get("price_per_kg") is not None:
            total_cost += entry["price_per_kg"] * (grams / 1000.0)
            currency = entry.get("currency", "USD")

        if entry.get("calories_per_100g") is not None:
            total_calories += entry["calories_per_100g"] * (grams / 100.0)

    return {
        "cost": round(total_cost, 2),
        "currency": currency,
        "calories": round(total_calories, 1),
        "missing_ingredients": missing,
    }
