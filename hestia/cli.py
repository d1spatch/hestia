"""Hestia CLI — entry point for all commands."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from . import catalog as _db
from .recipe import Recipe, load_all_recipes, load_recipe, compute_nutrition
from .renderer import compile_pdf, render_html, render_latex

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
    for ing in recipe.ingredients:
        entry = _db.get_ingredient(ing.name)
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
    import shutil
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
    ing_table = Table(show_header=True, header_style="bold magenta", show_lines=False)
    ing_table.add_column("Ingredient")
    ing_table.add_column("Amount", justify="right")
    ing_table.add_column("Unit")
    for ing in recipe.ingredients:
        ing_table.add_row(ing.name, str(ing.amount), ing.unit)
    console.print(ing_table)

    rprint("\n[bold]Instructions[/bold]")
    for i, step in enumerate(recipe.instructions, 1):
        rprint(f"  [dim]{i}.[/dim] {step}")

    if recipe.notes:
        rprint(f"\n[bold]Notes[/bold]\n  [italic]{recipe.notes.strip()}[/italic]")

    rprint(f"\n[bold]Nutrition & Cost[/bold]")
    rprint(f"  Calories : [bold]{nutrition['calories']} kcal[/bold]")
    rprint(f"  Est. Cost: [bold]{nutrition['currency']} {nutrition['cost']:.2f}[/bold]")
    if nutrition["missing_ingredients"]:
        rprint(
            f"  [yellow]⚠ Missing catalog data for:[/yellow] "
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

@ingredient_app.command("add")
def ingredient_add(
    name: Annotated[Optional[str], typer.Option("--name", "-n")] = None,
    price: Annotated[Optional[float], typer.Option("--price", help="Price per kg")] = None,
    currency: Annotated[str, typer.Option("--currency")] = "USD",
    calories: Annotated[Optional[float], typer.Option("--calories", help="kcal per 100g")] = None,
    protein: Annotated[Optional[float], typer.Option("--protein", help="g protein per 100g")] = None,
    carbs: Annotated[Optional[float], typer.Option("--carbs", help="g carbs per 100g")] = None,
    fat: Annotated[Optional[float], typer.Option("--fat", help="g fat per 100g")] = None,
    category: Annotated[Optional[str], typer.Option("--category")] = None,
    aliases: Annotated[Optional[str], typer.Option("--aliases", help="Comma-separated aliases")] = None,
    notes: Annotated[Optional[str], typer.Option("--notes")] = None,
):
    """Add an ingredient to the catalog (interactive if name not provided)."""
    if name is None:
        name = typer.prompt("Ingredient name")
    if price is None:
        price_str = typer.prompt("Price per kg (leave blank to skip)", default="")
        price = float(price_str) if price_str else None
    if calories is None:
        cal_str = typer.prompt("Calories per 100g (leave blank to skip)", default="")
        calories = float(cal_str) if cal_str else None

    data: dict = {"name": name, "currency": currency}
    if price is not None:
        data["price_per_kg"] = price
    if calories is not None:
        data["calories_per_100g"] = calories
    if protein is not None:
        data["protein_per_100g"] = protein
    if carbs is not None:
        data["carbs_per_100g"] = carbs
    if fat is not None:
        data["fat_per_100g"] = fat
    if category:
        data["category"] = category
    if aliases:
        data["aliases"] = [a.strip() for a in aliases.split(",")]
    if notes:
        data["notes"] = notes

    try:
        _db.add_ingredient(data)
        rprint(f"[green]Added:[/green] {name}")
    except ValueError as e:
        rprint(f"[red]{e}[/red]")
        raise typer.Exit(1)


@ingredient_app.command("list")
def ingredient_list(
    category: Annotated[Optional[str], typer.Option("--category", "-c")] = None,
):
    """List all ingredients in the catalog."""
    items = _db.list_ingredients(category=category)
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


@ingredient_app.command("update")
def ingredient_update(
    name: Annotated[str, typer.Argument(help="Ingredient name to update.")],
    price: Annotated[Optional[float], typer.Option("--price")] = None,
    currency: Annotated[Optional[str], typer.Option("--currency")] = None,
    calories: Annotated[Optional[float], typer.Option("--calories")] = None,
    protein: Annotated[Optional[float], typer.Option("--protein")] = None,
    carbs: Annotated[Optional[float], typer.Option("--carbs")] = None,
    fat: Annotated[Optional[float], typer.Option("--fat")] = None,
    category: Annotated[Optional[str], typer.Option("--category")] = None,
    notes: Annotated[Optional[str], typer.Option("--notes")] = None,
):
    """Update an ingredient's properties."""
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
    if category is not None:
        updates["category"] = category
    if notes is not None:
        updates["notes"] = notes

    if not updates:
        rprint("[yellow]Nothing to update — provide at least one option.[/yellow]")
        raise typer.Exit(1)

    try:
        _db.update_ingredient(name, updates)
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
    inserted, skipped = _db.import_csv(csv_path)
    rprint(f"[green]Imported {inserted}[/green] ingredient(s), skipped {skipped}.")
