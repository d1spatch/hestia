"""Hestia CLI — entry point for all commands."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Annotated, Any, Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from . import catalog as _catalog
from . import usda as _usda
from .recipe import Recipe, load_all_recipes, load_recipe, compute_nutrition
from .renderer import compile_pdf, render_html, render_latex
from .server import run as _run_server

app = typer.Typer(
    name="hestia",
    help="Precision cookbook — recipes, ingredients, nutrition, and beautiful output.",
    no_args_is_help=True,
)
recipe_app = typer.Typer(help="Manage recipes.", no_args_is_help=True)
ingredient_app = typer.Typer(help="Manage the ingredient catalog.", no_args_is_help=True)
app.add_typer(recipe_app, name="recipe")
app.add_typer(ingredient_app, name="ingredient")

console = Console()

_RECIPES_DIR = Path(__file__).parent.parent / "data" / "recipes"
_OUTPUT_DIR = Path(__file__).parent.parent / "output"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_catalog(recipe: Recipe) -> dict[str, dict]:
    """Fetch catalog entries for every ingredient in the recipe (case-insensitive)."""
    catalog: dict[str, dict] = {}
    for ing in recipe.all_ingredients:
        entry = _catalog.get_ingredient(ing.name)
        if entry:
            catalog[ing.name.lower()] = entry
    return catalog


def _load_recipe_by_name(name: str) -> tuple[Path, Recipe]:
    """Find and load a recipe YAML by slug or filename stem."""
    candidates = list(_RECIPES_DIR.glob(f"{name}*"))
    if not candidates:
        rprint(f"[red]No recipe found matching '{name}' in {_RECIPES_DIR}[/red]")
        raise typer.Exit(1)
    path = candidates[0]
    try:
        return path, load_recipe(path)
    except Exception as exc:
        rprint(f"[red]Failed to parse {path.name}:[/red] {exc}")
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# Recipe commands
# ---------------------------------------------------------------------------

@recipe_app.command("add")
def recipe_add(
    path: Annotated[Path, typer.Argument(help="Path to a recipe YAML file.")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Overwrite if exists.")] = False,
):
    """Register a YAML recipe by copying it into the data/recipes/ directory."""
    if not path.exists():
        rprint(f"[red]File not found:[/red] {path}")
        raise typer.Exit(1)
    _RECIPES_DIR.mkdir(parents=True, exist_ok=True)
    dest = _RECIPES_DIR / path.name
    if dest.exists() and not force:
        rprint(f"[yellow]Recipe already exists:[/yellow] {dest.name}  (use --force to overwrite)")
        raise typer.Exit(1)
    shutil.copy(path, dest)
    rprint(f"[green]Recipe added:[/green] {dest.name}")


@recipe_app.command("list")
def recipe_list():
    """List all recipes in the catalog."""
    pairs = load_all_recipes(_RECIPES_DIR)
    if not pairs:
        rprint("[yellow]No recipes found.[/yellow]  Add one with: hestia recipe add <path>")
        return
    table = Table(title="Recipes", show_lines=False)
    table.add_column("Name", style="bold")
    table.add_column("Serves")
    table.add_column("Tags")
    table.add_column("File", style="dim")
    for path, recipe in pairs:
        table.add_row(
            recipe.name,
            str(recipe.serves),
            ", ".join(recipe.tags) or "—",
            path.name,
        )
    console.print(table)


@recipe_app.command("show")
def recipe_show(
    name: Annotated[str, typer.Argument(help="Recipe slug or filename stem.")],
):
    """Display a recipe with computed nutrition and cost."""
    _, recipe = _load_recipe_by_name(name)
    catalog = _build_catalog(recipe)
    nutrition = compute_nutrition(recipe, catalog)

    rprint(f"\n[bold cyan]{recipe.name}[/bold cyan]")
    rprint(f"  Serves: [bold]{recipe.serves}[/bold]")
    if recipe.tags:
        rprint(f"  Tags:   {', '.join(recipe.tags)}")

    rprint("\n[bold]Ingredients[/bold]")
    from .recipe import IngredientGroup
    def _ing_table(ings):
        t = Table(show_header=True, header_style="bold magenta", show_lines=False)
        t.add_column("Ingredient")
        t.add_column("Amount", justify="right")
        t.add_column("Unit")
        t.add_column("Note", style="italic dim")
        for ing in ings:
            name = f"{ing.name} [dim](optional)[/dim]" if ing.optional else ing.name
            t.add_row(name, str(ing.amount), ing.unit, ing.note)
        return t
    has_groups = any(isinstance(i, IngredientGroup) for i in recipe.ingredients)
    if has_groups:
        for item in recipe.ingredients:
            if isinstance(item, IngredientGroup):
                rprint(f"  [bold magenta]{item.group}[/bold magenta]")
                console.print(_ing_table(item.items))
            else:
                console.print(_ing_table([item]))
    else:
        console.print(_ing_table(recipe.ingredients))

    rprint("\n[bold]Instructions[/bold]")
    from .recipe import InstructionGroup
    step_num = 1
    for item in recipe.instructions:
        if isinstance(item, InstructionGroup):
            rprint(f"  [bold magenta]{item.section}[/bold magenta]")
            for step in item.steps:
                rprint(f"    [dim]{step_num}.[/dim] {step}")
                step_num += 1
        else:
            rprint(f"  [dim]{step_num}.[/dim] {item}")
            step_num += 1

    if recipe.notes:
        rprint(f"\n[bold]Notes[/bold]\n  [italic]{recipe.notes.strip()}[/italic]")

    rprint(f"\n[bold]Nutrition & Cost[/bold]")
    rprint(f"  Calories      : [bold]{nutrition['calories']} kcal[/bold]")
    rprint(f"  Protein       : {nutrition['protein']} g")
    rprint(f"  Carbohydrates : {nutrition['carbs']} g  (sugar {nutrition['sugar']} g)")
    rprint(f"  Fat           : {nutrition['fat']} g  (saturated {nutrition['saturated_fat']} g)")
    rprint(f"  Fiber         : {nutrition['fiber']} g")
    rprint(f"  Sodium        : {nutrition['sodium_mg']} mg")
    rprint(f"  Cholesterol   : {nutrition['cholesterol_mg']} mg")
    rprint(f"  Potassium     : {nutrition['potassium_mg']} mg")
    rprint(f"  Calcium       : {nutrition['calcium_mg']} mg")
    rprint(f"  Iron          : {nutrition['iron_mg']} mg")
    rprint(f"  Magnesium     : {nutrition['magnesium_mg']} mg")
    rprint(f"  Manganese     : {nutrition['manganese_mg']} mg")
    rprint(f"  Vitamin C     : {nutrition['vitamin_c_mg']} mg")
    rprint(f"  Vitamin D     : {nutrition['vitamin_d_mcg']} mcg")
    rprint(f"  Vitamin K     : {nutrition['vitamin_k_mcg']} mcg")
    rprint(f"  Est. Cost     : [bold]{nutrition['currency']} {nutrition['cost']:.2f}[/bold]")
    if nutrition["missing_ingredients"]:
        rprint(
            f"  [yellow]Warning: Missing catalog data for:[/yellow] "
            f"{', '.join(nutrition['missing_ingredients'])}"
        )
    rprint()


@recipe_app.command("render")
def recipe_render(
    name: Annotated[str, typer.Argument(help="Recipe slug or filename stem.")],
    fmt: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: html | pdf | both"),
    ] = "both",
):
    """Render a recipe to HTML and/or PDF."""
    _, recipe = _load_recipe_by_name(name)
    catalog = _build_catalog(recipe)
    nutrition = compute_nutrition(recipe, catalog)

    fmt = fmt.lower()
    if fmt not in ("html", "pdf", "both"):
        rprint("[red]--format must be html, pdf, or both[/red]")
        raise typer.Exit(1)

    if fmt in ("html", "both"):
        out = render_html(recipe, nutrition, _OUTPUT_DIR)
        rprint(f"[green]HTML[/green] {out}")

    if fmt in ("pdf", "both"):
        tex_path = render_latex(recipe, nutrition, _OUTPUT_DIR)
        rprint(f"[green]LaTeX[/green] {tex_path}")
        try:
            pdf_path = compile_pdf(tex_path, _OUTPUT_DIR)
            rprint(f"[green]PDF[/green] {pdf_path}")
        except RuntimeError as e:
            rprint(f"[red]PDF compilation failed:[/red]\n{e}")


# ---------------------------------------------------------------------------
# Ingredient commands
# ---------------------------------------------------------------------------

_WEIGHT_TO_KG: dict[str, float] = {
    "g": 0.001, "gram": 0.001, "grams": 0.001,
    "kg": 1.0, "kilogram": 1.0, "kilograms": 1.0,
    "oz": 0.0283495, "ounce": 0.0283495, "ounces": 0.0283495,
    "floz": 0.0295735, "flounce": 0.0295735,  # fluid oz (water density approx)
    "lb": 0.453592, "lbs": 0.453592, "pound": 0.453592, "pounds": 0.453592,
    "gal": 3.78541, "gallon": 3.78541, "gallons": 3.78541,
    "qt": 0.946353, "quart": 0.946353, "quarts": 0.946353,
    "pt": 0.473176, "pint": 0.473176, "pints": 0.473176,
    "ml": 0.001, "l": 1.0, "liter": 1.0, "liters": 1.0, "litre": 1.0, "litres": 1.0,
}


def _prompt_float(label: str) -> "Optional[float]":
    """Prompt for an optional float value; returns None if left blank."""
    s = typer.prompt(f"  {label} (blank to skip)", default="")
    return float(s) if s else None


def _parse_grams(s: str) -> float:
    """Parse a serving-size string to grams. Accepts '30', '30g', '1oz', '28.3g', etc."""
    return _parse_weight_kg(s) * 1000.0


def _parse_weight_kg(s: str) -> float:
    """Parse a weight string like '32oz', '2lb', '500g', '1.5kg' into kg.

    A bare number is treated as grams. Raises ValueError on bad input.
    """
    import re
    s = s.strip().lower()
    m = re.match(r"^([\d.]+)\s*([a-z]+)$", s)
    if m:
        value, unit = float(m.group(1)), m.group(2)
        factor = _WEIGHT_TO_KG.get(unit)
        if factor:
            return value * factor
    try:
        return float(s) / 1000.0  # bare number → grams
    except ValueError:
        pass
    raise ValueError(
        f"Cannot parse weight '{s}'. Use formats like '32oz', '2lb', '500g', '1.5kg'."
    )


@ingredient_app.command("add")
def ingredient_add(
    name: Annotated[Optional[str], typer.Option("--name", "-n")] = None,
    package_price: Annotated[Optional[float], typer.Option("--package-price", "-P", help="Price paid for the whole package. Use with --net-weight to compute price/kg automatically.")] = None,
    net_weight: Annotated[Optional[str], typer.Option("--net-weight", "-w", help="Package net weight, e.g. '32oz', '2lb', '500g', '1.5kg'. Used with --package-price to compute price/kg.")] = None,
    price: Annotated[Optional[float], typer.Option("--price", help="Price per kg (alternative to --package-price + --net-weight)")] = None,
    currency: Annotated[str, typer.Option("--currency")] = "USD",
    serving_size: Annotated[Optional[float], typer.Option("--serving-size", "-s", help="Serving size in grams. When set, all nutrient values are treated as per-serving and converted to per-100g. Sodium and cholesterol should be in mg (as on the label).")] = None,
    calories: Annotated[Optional[float], typer.Option("--calories", help="kcal per serving (or per 100g if --serving-size not set)")] = None,
    protein: Annotated[Optional[float], typer.Option("--protein", help="g protein per serving (or per 100g)")] = None,
    carbs: Annotated[Optional[float], typer.Option("--carbs", help="g carbs per serving (or per 100g)")] = None,
    fat: Annotated[Optional[float], typer.Option("--fat", help="g fat per serving (or per 100g)")] = None,
    fiber: Annotated[Optional[float], typer.Option("--fiber", help="g fiber per serving (or per 100g)")] = None,
    sugar: Annotated[Optional[float], typer.Option("--sugar", help="g sugar per serving (or per 100g)")] = None,
    sodium: Annotated[Optional[float], typer.Option("--sodium", help="mg sodium per serving (or g per 100g if --serving-size not set)")] = None,
    saturated_fat: Annotated[Optional[float], typer.Option("--saturated-fat", help="g saturated fat per serving (or per 100g)")] = None,
    cholesterol: Annotated[Optional[float], typer.Option("--cholesterol", help="mg cholesterol per serving (or g per 100g if --serving-size not set)")] = None,
    vitamin_c: Annotated[Optional[float], typer.Option("--vitamin-c", help="mg Vitamin C per serving (or per 100g)")] = None,
    vitamin_d: Annotated[Optional[float], typer.Option("--vitamin-d", help="mcg Vitamin D per serving (or per 100g)")] = None,
    vitamin_k: Annotated[Optional[float], typer.Option("--vitamin-k", help="mcg Vitamin K per serving (or per 100g)")] = None,
    calcium: Annotated[Optional[float], typer.Option("--calcium", help="mg calcium per serving (or per 100g)")] = None,
    iron: Annotated[Optional[float], typer.Option("--iron", help="mg iron per serving (or per 100g)")] = None,
    magnesium: Annotated[Optional[float], typer.Option("--magnesium", help="mg magnesium per serving (or per 100g)")] = None,
    potassium: Annotated[Optional[float], typer.Option("--potassium", help="mg potassium per serving (or per 100g)")] = None,
    manganese: Annotated[Optional[float], typer.Option("--manganese", help="mg manganese per serving (or per 100g)")] = None,
    category: Annotated[Optional[str], typer.Option("--category")] = None,
    aliases: Annotated[Optional[str], typer.Option("--aliases", help="Comma-separated aliases")] = None,
    notes: Annotated[Optional[str], typer.Option("--notes")] = None,
):
    """Add an ingredient to the catalog.

    Designed to match what's printed on a product:

    \b
    Front of package  ->  --net-weight "32oz"  --package-price 8.99
    Nutrition label   ->  --serving-size 30  --calories 110  --protein 4
                          --carbs 19  --fat 2.5  --fiber 1  --sugar 1
                          --sodium 115  --cholesterol 0

    When --serving-size is given, all nutrient values are treated as
    per-serving and scaled to per-100g automatically.
    Sodium and cholesterol are expected in mg (as printed on US labels).
    When --package-price and --net-weight are given, price/kg is computed
    from the package size — no math needed.

    Example:

        hestia ingredient add --name "oat bran" --category grain \\
            --package-price 8.99 --net-weight 32oz \\
            --serving-size 30 \\
            --calories 110 --protein 8 --carbs 19 --fat 3 \\
            --fiber 6 --sugar 1 --sodium 0 --cholesterol 0
    """
    if name is None:
        name = typer.prompt("Ingredient name")

    # --- Price: resolve from package info or prompt ---
    if package_price is not None and net_weight is not None:
        try:
            weight_kg = _parse_weight_kg(net_weight)
        except ValueError as e:
            rprint(f"[red]{e}[/red]")
            raise typer.Exit(1)
        price = round(package_price / weight_kg, 4)
        rprint(f"[dim]Price: {currency} {package_price:.2f} / {net_weight} = {currency} {price:.4f}/kg[/dim]")
    elif package_price is not None or net_weight is not None:
        rprint("[red]Provide both --package-price and --net-weight together.[/red]")
        raise typer.Exit(1)
    elif price is None:
        # Interactive: ask for package info (natural) or price/kg (advanced)
        pkg_str = typer.prompt("Package price (leave blank to enter price/kg directly)", default="")
        if pkg_str:
            package_price = float(pkg_str)
            wt_str = typer.prompt("Net weight (e.g. 32oz, 2lb, 500g, 1.5kg)", default="")
            if wt_str:
                try:
                    weight_kg = _parse_weight_kg(wt_str)
                    price = round(package_price / weight_kg, 4)
                    rprint(f"[dim]Price: {currency} {package_price:.2f} / {wt_str} = {currency} {price:.4f}/kg[/dim]")
                except ValueError as e:
                    rprint(f"[red]{e}[/red]")
                    raise typer.Exit(1)
        else:
            price_str = typer.prompt("Price per kg (leave blank to skip)", default="")
            price = float(price_str) if price_str else None

    # --- Nutrition: interactive label-walk or per-100g fallback ---
    _no_nutrition = all(x is None for x in [
        calories, protein, carbs, fat, fiber, sugar, sodium, saturated_fat, cholesterol,
        vitamin_c, vitamin_d, vitamin_k, calcium, iron, magnesium, potassium, manganese,
    ])

    if serving_size is None and _no_nutrition:
        # Interactive: ask for serving size first, then walk the label fields
        ss_str = typer.prompt("Serving size in grams (blank to enter per-100g values instead)", default="")
        if ss_str:
            serving_size = _parse_grams(ss_str)
            rprint("  Enter nutrition facts per serving (blank to skip any field):")
            calories      = _prompt_float("Calories (kcal)")
            fat           = _prompt_float("Total Fat (g)")
            saturated_fat = _prompt_float("  Saturated Fat (g)")
            cholesterol   = _prompt_float("Cholesterol (mg)")
            sodium        = _prompt_float("Sodium (mg)")
            carbs         = _prompt_float("Total Carbohydrate (g)")
            fiber         = _prompt_float("  Dietary Fiber (g)")
            sugar         = _prompt_float("  Total Sugars (g)")
            protein       = _prompt_float("Protein (g)")
            rprint("  Vitamins & minerals (blank to skip):")
            vitamin_d  = _prompt_float("Vitamin D (mcg)")
            calcium    = _prompt_float("Calcium (mg)")
            iron       = _prompt_float("Iron (mg)")
            potassium  = _prompt_float("Potassium (mg)")
            vitamin_c  = _prompt_float("Vitamin C (mg)")
            vitamin_k  = _prompt_float("Vitamin K (mcg)")
            magnesium  = _prompt_float("Magnesium (mg)")
            manganese  = _prompt_float("Manganese (mg)")
        else:
            cal_str = typer.prompt("Calories per 100g (blank to skip)", default="")
            calories = float(cal_str) if cal_str else None
    elif serving_size is None and calories is None:
        cal_str = typer.prompt("Calories per 100g (blank to skip)", default="")
        calories = float(cal_str) if cal_str else None

    # --- Scale per-serving values to per-100g ---
    if serving_size is not None:
        if serving_size <= 0:
            rprint("[red]--serving-size must be greater than 0[/red]")
            raise typer.Exit(1)
        factor = 100.0 / serving_size
        if calories is not None:
            calories = round(calories * factor, 2)
        if protein is not None:
            protein = round(protein * factor, 2)
        if carbs is not None:
            carbs = round(carbs * factor, 2)
        if fat is not None:
            fat = round(fat * factor, 2)
        if fiber is not None:
            fiber = round(fiber * factor, 2)
        if sugar is not None:
            sugar = round(sugar * factor, 2)
        if saturated_fat is not None:
            saturated_fat = round(saturated_fat * factor, 2)
        # Sodium and cholesterol: labels show mg/serving → store as g/100g
        if sodium is not None:
            sodium = round((sodium / 1000) * factor, 4)
        if cholesterol is not None:
            cholesterol = round((cholesterol / 1000) * factor, 4)
        # Vitamins & minerals: stored as mg/100g or mcg/100g (no unit conversion)
        if vitamin_c is not None:
            vitamin_c = round(vitamin_c * factor, 4)
        if vitamin_d is not None:
            vitamin_d = round(vitamin_d * factor, 4)
        if vitamin_k is not None:
            vitamin_k = round(vitamin_k * factor, 4)
        if calcium is not None:
            calcium = round(calcium * factor, 4)
        if iron is not None:
            iron = round(iron * factor, 4)
        if magnesium is not None:
            magnesium = round(magnesium * factor, 4)
        if potassium is not None:
            potassium = round(potassium * factor, 4)
        if manganese is not None:
            manganese = round(manganese * factor, 4)
        rprint(f"[dim]Nutrition: serving size {serving_size}g, scaled to per-100g[/dim]")

    from datetime import date as _today_date
    data: dict = {"name": name, "currency": currency}
    if price is not None:
        data["price_per_kg"] = price
        history_entry: dict = {"date": _today_date.today().isoformat(), "price_per_kg": price}
        if package_price is not None:
            history_entry["package_price"] = package_price
        if net_weight is not None:
            history_entry["net_weight"] = net_weight
        data["price_history"] = [history_entry]
    if calories is not None:
        data["calories_per_100g"] = calories
    if protein is not None:
        data["protein_per_100g"] = protein
    if carbs is not None:
        data["carbs_per_100g"] = carbs
    if fat is not None:
        data["fat_per_100g"] = fat
    if fiber is not None:
        data["fiber_per_100g"] = fiber
    if sugar is not None:
        data["sugar_per_100g"] = sugar
    if sodium is not None:
        data["sodium_per_100g"] = sodium
    if saturated_fat is not None:
        data["saturated_fat_per_100g"] = saturated_fat
    if cholesterol is not None:
        data["cholesterol_per_100g"] = cholesterol
    if vitamin_c is not None:
        data["vitamin_c_per_100g"] = vitamin_c
    if vitamin_d is not None:
        data["vitamin_d_per_100g"] = vitamin_d
    if vitamin_k is not None:
        data["vitamin_k_per_100g"] = vitamin_k
    if calcium is not None:
        data["calcium_per_100g"] = calcium
    if iron is not None:
        data["iron_per_100g"] = iron
    if magnesium is not None:
        data["magnesium_per_100g"] = magnesium
    if potassium is not None:
        data["potassium_per_100g"] = potassium
    if manganese is not None:
        data["manganese_per_100g"] = manganese
    if category:
        data["category"] = category
    if aliases:
        data["aliases"] = [a.strip() for a in aliases.split(",")]
    if notes:
        data["notes"] = notes

    try:
        _catalog.add_ingredient(data)
        rprint(f"[green]Added:[/green] {name}")
    except ValueError as e:
        rprint(f"[red]{e}[/red]")
        raise typer.Exit(1)


@ingredient_app.command("list")
def ingredient_list(
    category: Annotated[Optional[str], typer.Option("--category", "-c")] = None,
):
    """List all ingredients in the catalog."""
    items = _catalog.list_ingredients(category=category)
    if not items:
        rprint("[yellow]No ingredients found.[/yellow]  Add one with: hestia ingredient add")
        return
    table = Table(title="Ingredient Catalog", show_lines=False)
    table.add_column("Name", style="bold")
    table.add_column("Category")
    table.add_column("Price/kg", justify="right")
    table.add_column("Ccy")
    table.add_column("Cal/100g", justify="right")
    for ing in items:
        table.add_row(
            ing["name"],
            ing.get("category") or "—",
            f"{ing['price_per_kg']:.2f}" if ing.get("price_per_kg") is not None else "—",
            ing.get("currency") or "USD",
            f"{ing['calories_per_100g']:.0f}" if ing.get("calories_per_100g") is not None else "—",
        )
    console.print(table)


def _iprompt(label: str, current: "Any") -> str:
    """Prompt showing the current value; blank input means no change."""
    cur = str(current) if current is not None else ""
    display = f"[{cur}]" if cur else "[blank]"
    return typer.prompt(f"  {label} {display}", default="")


@ingredient_app.command("update")
def ingredient_update(
    name: Annotated[str, typer.Argument(help="Ingredient name to update.")],
    price: Annotated[Optional[float], typer.Option("--price")] = None,
    package_price: Annotated[Optional[float], typer.Option("--package-price", "-P", help="Package price. Use with --net-weight.")] = None,
    net_weight: Annotated[Optional[str], typer.Option("--net-weight", "-w", help="Package net weight, e.g. '32oz', '2lb', '500g'.")] = None,
    currency: Annotated[Optional[str], typer.Option("--currency")] = None,
    serving_size: Annotated[Optional[float], typer.Option("--serving-size", "-s", help="Serving size in grams. Scales all nutrient flags to per-100g.")] = None,
    calories: Annotated[Optional[float], typer.Option("--calories")] = None,
    protein: Annotated[Optional[float], typer.Option("--protein")] = None,
    carbs: Annotated[Optional[float], typer.Option("--carbs")] = None,
    fat: Annotated[Optional[float], typer.Option("--fat")] = None,
    fiber: Annotated[Optional[float], typer.Option("--fiber")] = None,
    sugar: Annotated[Optional[float], typer.Option("--sugar")] = None,
    sodium: Annotated[Optional[float], typer.Option("--sodium")] = None,
    saturated_fat: Annotated[Optional[float], typer.Option("--saturated-fat")] = None,
    cholesterol: Annotated[Optional[float], typer.Option("--cholesterol")] = None,
    vitamin_c: Annotated[Optional[float], typer.Option("--vitamin-c", help="mg Vitamin C per serving (or per 100g)")] = None,
    vitamin_d: Annotated[Optional[float], typer.Option("--vitamin-d", help="mcg Vitamin D per serving (or per 100g)")] = None,
    vitamin_k: Annotated[Optional[float], typer.Option("--vitamin-k", help="mcg Vitamin K per serving (or per 100g)")] = None,
    calcium: Annotated[Optional[float], typer.Option("--calcium", help="mg calcium per serving (or per 100g)")] = None,
    iron: Annotated[Optional[float], typer.Option("--iron", help="mg iron per serving (or per 100g)")] = None,
    magnesium: Annotated[Optional[float], typer.Option("--magnesium", help="mg magnesium per serving (or per 100g)")] = None,
    potassium: Annotated[Optional[float], typer.Option("--potassium", help="mg potassium per serving (or per 100g)")] = None,
    manganese: Annotated[Optional[float], typer.Option("--manganese", help="mg manganese per serving (or per 100g)")] = None,
    category: Annotated[Optional[str], typer.Option("--category")] = None,
    notes: Annotated[Optional[str], typer.Option("--notes")] = None,
):
    """Update an ingredient's properties.

    Run without flags to enter interactive mode — shows current values and
    prompts for each field (blank = keep current).
    """
    # Look up the ingredient first so we can show current values interactively
    existing = _catalog.get_ingredient(name)
    if existing is None:
        rprint(f"[red]Ingredient '{name}' not found.[/red]")
        raise typer.Exit(1)

    _no_flags = all(x is None for x in [
        price, package_price, net_weight, currency, serving_size,
        calories, protein, carbs, fat, fiber, sugar, sodium,
        saturated_fat, cholesterol,
        vitamin_c, vitamin_d, vitamin_k, calcium, iron, magnesium, potassium, manganese,
        category, notes,
    ])

    if _no_flags:
        # --- Interactive mode ---
        rprint(f"\n[bold cyan]{name}[/bold cyan]  (blank = keep current)\n")

        # Price
        rprint("[bold]Pricing[/bold]")
        pkg_str = _iprompt("Package price", existing.get("price_per_kg") and f"current $/kg={existing['price_per_kg']}")
        if pkg_str:
            package_price = float(pkg_str)
            wt_str = typer.prompt("  Net weight (e.g. 32oz, 2lb, 500g, 1.5kg)", default="")
            if wt_str:
                try:
                    _wkg = _parse_weight_kg(wt_str)
                    price = round(package_price / _wkg, 4)
                    net_weight = wt_str
                    rprint(f"  [dim]=> {existing.get('currency','USD')} {price:.4f}/kg[/dim]")
                except ValueError as e:
                    rprint(f"[red]{e}[/red]")
                    raise typer.Exit(1)
            else:
                rprint("[red]Net weight is required when entering package price.[/red]")
                raise typer.Exit(1)
        else:
            ppkg_str = _iprompt("Price per kg (or blank to skip)", existing.get("price_per_kg"))
            if ppkg_str:
                price = float(ppkg_str)

        cur_str = _iprompt("Currency", existing.get("currency", "USD"))
        if cur_str:
            currency = cur_str

        # Nutrition
        rprint("\n[bold]Nutrition[/bold]  (enter per-serving values if you provide a serving size)")
        ss_str = _iprompt("Serving size in grams (blank = enter per-100g directly)", existing.get("_serving_size"))
        if ss_str:
            serving_size = _parse_grams(ss_str)
            rprint("  Enter per-serving values (blank = keep current):")
            def _pfs(label: str, cur_100g: "Optional[float]") -> "Optional[float]":
                cur_srv = round(cur_100g * serving_size / 100, 4) if cur_100g is not None else None
                s = typer.prompt(f"    {label} [{cur_srv if cur_srv is not None else 'blank'}]", default="")
                return float(s) if s else None
            calories      = _pfs("Calories (kcal)", existing.get("calories_per_100g"))
            fat           = _pfs("Total Fat (g)", existing.get("fat_per_100g"))
            saturated_fat = _pfs("  Saturated Fat (g)", existing.get("saturated_fat_per_100g"))
            _chol_cur = existing["cholesterol_per_100g"] * 1000 if existing.get("cholesterol_per_100g") else None
            cholesterol   = _pfs("Cholesterol (mg)", _chol_cur)
            _sod_cur = existing["sodium_per_100g"] * 1000 if existing.get("sodium_per_100g") else None
            sodium        = _pfs("Sodium (mg)", _sod_cur)
            carbs         = _pfs("Total Carbohydrate (g)", existing.get("carbs_per_100g"))
            fiber         = _pfs("  Dietary Fiber (g)", existing.get("fiber_per_100g"))
            sugar         = _pfs("  Total Sugars (g)", existing.get("sugar_per_100g"))
            protein       = _pfs("Protein (g)", existing.get("protein_per_100g"))
            rprint("  Vitamins & minerals (blank = keep current):")
            vitamin_d  = _pfs("Vitamin D (mcg)", existing.get("vitamin_d_per_100g"))
            calcium    = _pfs("Calcium (mg)", existing.get("calcium_per_100g"))
            iron       = _pfs("Iron (mg)", existing.get("iron_per_100g"))
            potassium  = _pfs("Potassium (mg)", existing.get("potassium_per_100g"))
            vitamin_c  = _pfs("Vitamin C (mg)", existing.get("vitamin_c_per_100g"))
            vitamin_k  = _pfs("Vitamin K (mcg)", existing.get("vitamin_k_per_100g"))
            magnesium  = _pfs("Magnesium (mg)", existing.get("magnesium_per_100g"))
            manganese  = _pfs("Manganese (mg)", existing.get("manganese_per_100g"))
        else:
            def _p100(label: str, field: str) -> "Optional[float]":
                s = _iprompt(label, existing.get(field))
                return float(s) if s else None
            calories      = _p100("Calories per 100g", "calories_per_100g")
            fat           = _p100("Fat per 100g (g)", "fat_per_100g")
            saturated_fat = _p100("Saturated fat per 100g (g)", "saturated_fat_per_100g")
            cholesterol   = _p100("Cholesterol per 100g (g)", "cholesterol_per_100g")
            sodium        = _p100("Sodium per 100g (g)", "sodium_per_100g")
            carbs         = _p100("Carbs per 100g (g)", "carbs_per_100g")
            fiber         = _p100("Fiber per 100g (g)", "fiber_per_100g")
            sugar         = _p100("Sugar per 100g (g)", "sugar_per_100g")
            protein       = _p100("Protein per 100g (g)", "protein_per_100g")
            rprint("  Vitamins & minerals (blank = keep current):")
            vitamin_d  = _p100("Vitamin D per 100g (mcg)", "vitamin_d_per_100g")
            calcium    = _p100("Calcium per 100g (mg)", "calcium_per_100g")
            iron       = _p100("Iron per 100g (mg)", "iron_per_100g")
            potassium  = _p100("Potassium per 100g (mg)", "potassium_per_100g")
            vitamin_c  = _p100("Vitamin C per 100g (mg)", "vitamin_c_per_100g")
            vitamin_k  = _p100("Vitamin K per 100g (mcg)", "vitamin_k_per_100g")
            magnesium  = _p100("Magnesium per 100g (mg)", "magnesium_per_100g")
            manganese  = _p100("Manganese per 100g (mg)", "manganese_per_100g")

        # Category / notes
        rprint("\n[bold]Other[/bold]")
        cat_str = _iprompt("Category", existing.get("category"))
        if cat_str:
            category = cat_str
        notes_str = _iprompt("Notes", existing.get("notes"))
        if notes_str:
            notes = notes_str

    # --- Resolve package price → price/kg (non-interactive flag path) ---
    if package_price is not None and net_weight is not None and price is None:
        try:
            _wkg = _parse_weight_kg(net_weight)
        except ValueError as e:
            rprint(f"[red]{e}[/red]")
            raise typer.Exit(1)
        price = round(package_price / _wkg, 4)
        rprint(f"[dim]Price: {currency or 'USD'} {package_price:.2f} / {net_weight} = {currency or 'USD'} {price:.4f}/kg[/dim]")
    elif (package_price is not None) != (net_weight is not None) and price is None:
        rprint("[red]Provide both --package-price and --net-weight together.[/red]")
        raise typer.Exit(1)

    # --- Scale per-serving to per-100g ---
    if serving_size is not None and serving_size > 0:
        factor = 100.0 / serving_size
        if calories is not None:
            calories = round(calories * factor, 2)
        if protein is not None:
            protein = round(protein * factor, 2)
        if carbs is not None:
            carbs = round(carbs * factor, 2)
        if fat is not None:
            fat = round(fat * factor, 2)
        if fiber is not None:
            fiber = round(fiber * factor, 2)
        if sugar is not None:
            sugar = round(sugar * factor, 2)
        if saturated_fat is not None:
            saturated_fat = round(saturated_fat * factor, 2)
        if sodium is not None:
            sodium = round((sodium / 1000) * factor, 4)
        if cholesterol is not None:
            cholesterol = round((cholesterol / 1000) * factor, 4)
        if vitamin_c is not None:
            vitamin_c = round(vitamin_c * factor, 4)
        if vitamin_d is not None:
            vitamin_d = round(vitamin_d * factor, 4)
        if vitamin_k is not None:
            vitamin_k = round(vitamin_k * factor, 4)
        if calcium is not None:
            calcium = round(calcium * factor, 4)
        if iron is not None:
            iron = round(iron * factor, 4)
        if magnesium is not None:
            magnesium = round(magnesium * factor, 4)
        if potassium is not None:
            potassium = round(potassium * factor, 4)
        if manganese is not None:
            manganese = round(manganese * factor, 4)

    updates: dict = {}
    if price is not None:
        updates["price_per_kg"] = price
    if currency is not None:
        updates["currency"] = currency
    if calories is not None:
        updates["calories_per_100g"] = calories
    if protein is not None:
        updates["protein_per_100g"] = protein
    if carbs is not None:
        updates["carbs_per_100g"] = carbs
    if fat is not None:
        updates["fat_per_100g"] = fat
    if fiber is not None:
        updates["fiber_per_100g"] = fiber
    if sugar is not None:
        updates["sugar_per_100g"] = sugar
    if sodium is not None:
        updates["sodium_per_100g"] = sodium
    if saturated_fat is not None:
        updates["saturated_fat_per_100g"] = saturated_fat
    if cholesterol is not None:
        updates["cholesterol_per_100g"] = cholesterol
    if vitamin_c is not None:
        updates["vitamin_c_per_100g"] = vitamin_c
    if vitamin_d is not None:
        updates["vitamin_d_per_100g"] = vitamin_d
    if vitamin_k is not None:
        updates["vitamin_k_per_100g"] = vitamin_k
    if calcium is not None:
        updates["calcium_per_100g"] = calcium
    if iron is not None:
        updates["iron_per_100g"] = iron
    if magnesium is not None:
        updates["magnesium_per_100g"] = magnesium
    if potassium is not None:
        updates["potassium_per_100g"] = potassium
    if manganese is not None:
        updates["manganese_per_100g"] = manganese
    if category is not None:
        updates["category"] = category
    if notes is not None:
        updates["notes"] = notes

    if not updates:
        rprint("[yellow]Nothing to update.[/yellow]")
        raise typer.Exit(0)

    try:
        _catalog.update_ingredient(name, updates)
        rprint(f"[green]Updated:[/green] {name}")
    except ValueError as e:
        rprint(f"[red]{e}[/red]")
        raise typer.Exit(1)


@ingredient_app.command("import")
def ingredient_import(
    csv_path: Annotated[Path, typer.Argument(help="Path to CSV file.")],
):
    """Bulk-import ingredients from a CSV file."""
    if not csv_path.exists():
        rprint(f"[red]File not found:[/red] {csv_path}")
        raise typer.Exit(1)
    inserted, skipped = _catalog.import_csv(csv_path)
    rprint(f"[green]Imported {inserted}[/green] ingredient(s), skipped {skipped}.")


@ingredient_app.command("lookup-usda")
def ingredient_lookup(
    query: Annotated[str, typer.Argument(help="Search term (ingredient name).")],
    limit: Annotated[int, typer.Option("--limit", "-n", help="Max results.")] = 10,
):
    """Search USDA FoodData Central and list matching foods with their FDC IDs.

    \b
    Typical workflow:
        hestia ingredient lookup-usda "oat bran"
        hestia ingredient import-usda <fdc_id> --name "oat bran" --category grain
        hestia ingredient update-price "oat bran" -P 8.99 -w 32oz -s Costco

    Set USDA_API_KEY in .env for full rate limits (free key at fdc.nal.usda.gov).
    """
    try:
        results = _usda.search(query, page_size=limit)
    except RuntimeError as e:
        rprint(f"[red]{e}[/red]")
        raise typer.Exit(1)

    if not results:
        rprint("[yellow]No results found.[/yellow]")
        return

    table = Table(title=f"USDA FDC results for '{query}'", show_lines=False)
    table.add_column("FDC ID", style="bold cyan", justify="right")
    table.add_column("Description")
    table.add_column("Type", style="dim")
    for r in results:
        table.add_row(str(r["fdc_id"]), r["description"], r["data_type"])
    console.print(table)
    rprint("[dim]Import with: hestia ingredient import-usda <fdc_id> --name \"<name>\"  (then add a price with: hestia ingredient update-price <name>)[/dim]")


@ingredient_app.command("import-usda")
def ingredient_import_usda(
    fdc_id: Annotated[int, typer.Argument(help="USDA FoodData Central ID.")],
    name: Annotated[Optional[str], typer.Option("--name", "-n", help="Catalog name (defaults to FDC description).")] = None,
    category: Annotated[Optional[str], typer.Option("--category", "-c")] = None,
    update: Annotated[bool, typer.Option("--update", help="Merge into existing entry instead of failing.")] = False,
):
    """Import full nutrition data from USDA FoodData Central by FDC ID.

    Populates macros, micronutrients, and source attribution automatically.
    Use --update to merge nutrition into an ingredient that already exists.

    \b
    Example:
        hestia ingredient lookup-usda "bread flour"
        hestia ingredient import-usda 169761 --name "bread flour" --category grain
        hestia ingredient update-price "bread flour" -P 5.99 -w 5lb -s "Whole Foods"
    """
    try:
        data = _usda.fetch(fdc_id)
    except RuntimeError as e:
        rprint(f"[red]{e}[/red]")
        raise typer.Exit(1)

    usda_desc = data["source"]["description"].lower()
    if name:
        ingredient_name = name
    else:
        suggested = usda_desc
        rprint(f"[dim]USDA description:[/dim] {usda_desc}")
        entered = typer.prompt(f"Save as", default=suggested)
        ingredient_name = entered.strip() or suggested
    data["name"] = ingredient_name
    if category:
        data["category"] = category

    existing = _catalog.get_ingredient(ingredient_name)
    if existing and not update:
        rprint(
            f"[yellow]'{ingredient_name}' already exists.[/yellow] "
            "Use --update to merge nutrition data into it."
        )
        raise typer.Exit(1)

    if existing and update:
        updates = {k: v for k, v in data.items() if k != "name"}
        _catalog.update_ingredient(ingredient_name, updates)
        rprint(f"[green]Updated:[/green] {ingredient_name}  (source: USDA FDC {fdc_id})")
    else:
        _catalog.add_ingredient(data)
        rprint(f"[green]Added:[/green] {ingredient_name}  (source: USDA FDC {fdc_id})")

    # Show what was imported
    fields = [k for k in data if k.endswith("_per_100g") and data[k] is not None]
    rprint(f"  Fields populated: [dim]{', '.join(fields)}[/dim]")


@ingredient_app.command("update-price")
def ingredient_price_update(
    name: Annotated[str, typer.Argument(help="Ingredient name.")],
    package_price: Annotated[Optional[float], typer.Option("--package-price", "-P", help="Price paid for the whole package. Use with --net-weight to compute price/kg automatically.")] = None,
    net_weight: Annotated[Optional[str], typer.Option("--net-weight", "-w", help="Package net weight, e.g. '32oz', '2lb', '500g', '1.5kg'.")] = None,
    price: Annotated[Optional[float], typer.Option("--price", "-p", help="Price per kg (alternative to --package-price + --net-weight).")] = None,
    store: Annotated[Optional[str], typer.Option("--store", "-s", help="Store or retailer name.")] = None,
    currency: Annotated[str, typer.Option("--currency", help="Currency code (default: USD).")] = "USD",
    record_date: Annotated[Optional[str], typer.Option("--date", "-d", help="Date of purchase as YYYY-MM-DD. Defaults to today.")] = None,
):
    """Record a new price observation for an ingredient.

    Appends to the ingredient's price_history and updates its current price/kg.
    Pass package price and net weight from the store label — price/kg is computed automatically.

    \b
    Examples:
        hestia ingredient update-price "bread flour" -P 8.99 -w 5lb -s Costco
        hestia ingredient update-price "bread flour" --price 1.98 --store "Whole Foods"
    """
    if package_price is not None and net_weight is not None:
        try:
            weight_kg = _parse_weight_kg(net_weight)
        except ValueError as e:
            rprint(f"[red]{e}[/red]")
            raise typer.Exit(1)
        price = round(package_price / weight_kg, 4)
        rprint(f"[dim]Price: {currency} {package_price:.2f} / {net_weight} = {currency} {price:.4f}/kg[/dim]")
    elif package_price is not None or net_weight is not None:
        rprint("[red]Provide both --package-price and --net-weight together.[/red]")
        raise typer.Exit(1)
    elif price is None:
        # Interactive: ask for package info (natural) or price/kg (advanced)
        pkg_str = typer.prompt("Package price (leave blank to enter price/kg directly)", default="")
        if pkg_str:
            package_price = float(pkg_str)
            wt_str = typer.prompt("Net weight (e.g. 32oz, 2lb, 500g, 1.5kg)", default="")
            if wt_str:
                try:
                    weight_kg = _parse_weight_kg(wt_str)
                    price = round(package_price / weight_kg, 4)
                    rprint(f"[dim]Price: {currency} {package_price:.2f} / {wt_str} = {currency} {price:.4f}/kg[/dim]")
                except ValueError as e:
                    rprint(f"[red]{e}[/red]")
                    raise typer.Exit(1)
            else:
                rprint("[red]Net weight is required when entering package price.[/red]")
                raise typer.Exit(1)
        else:
            price_str = typer.prompt("Price per kg", default="")
            if not price_str:
                rprint("[red]A price is required.[/red]")
                raise typer.Exit(1)
            price = float(price_str)
        if not store:
            store_str = typer.prompt("Store (leave blank to skip)", default="")
            store = store_str or None

    try:
        _catalog.record_price(
            name, price,
            currency=currency,
            store=store,
            record_date=record_date,
            package_price=package_price,
            net_weight=net_weight,
        )
    except ValueError as e:
        rprint(f"[red]{e}[/red]")
        raise typer.Exit(1)
    date_label = record_date or "today"
    store_label = f" @ {store}" if store else ""
    rprint(f"[green]Price recorded:[/green] {name}  {currency} {price:.4f}/kg{store_label}  [{date_label}]")


# ---------------------------------------------------------------------------
# Web server
# ---------------------------------------------------------------------------

@app.command("serve")
def serve(
    host: Annotated[str, typer.Option("--host", help="Bind address.")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port", "-p", help="Port to listen on.")] = 8765,
    no_browser: Annotated[bool, typer.Option("--no-browser", help="Don't auto-open browser.")] = False,
):
    """Start the Hestia web interface (recipe browser + ingredient catalog)."""
    _run_server(host=host, port=port, open_browser=not no_browser)


@app.command("build")
def build_site(
    output: Annotated[Path, typer.Option("--output", "-o", help="Output directory.")] = Path("_site"),
    base_url: Annotated[str, typer.Option("--base-url", help="Base URL path (e.g. /hestia/ for GitHub Pages).")] = "/",
):
    """Build a static site for deployment to GitHub Pages or any static host."""
    from .builder import build as _build
    rprint(f"[bold]Building static site[/bold] → [cyan]{output}[/cyan]  (base: {base_url})")
    _build(output, base_url=base_url)
    pages = sum(1 for _ in output.rglob("*.html"))
    rprint(f"[green]✓ Done.[/green] {pages} pages written to {output}/")
