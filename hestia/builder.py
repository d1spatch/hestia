"""Static site generator — renders all pages to a deployable _site/ directory."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from urllib.parse import quote_plus

import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import catalog as _catalog
from .recipe import compute_nutrition, load_all_recipes
from .renderer import render_html_str

_RECIPES_DIR = Path(__file__).parent.parent / "data" / "recipes"
_CATALOG_PATH = Path(__file__).parent.parent / "data" / "ingredients.yaml"
_TEMPLATES_DIR = Path(__file__).parent / "templates"


def _make_env(base: str) -> Environment:
    def _tojson(v):
        def default(obj):
            if isinstance(obj, (datetime.date, datetime.datetime)):
                return obj.isoformat()
            raise TypeError(f"Not serializable: {type(obj)}")
        return json.dumps(v, default=default)

    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    env.filters["url_encode"] = quote_plus
    env.filters["tojson"] = _tojson
    env.globals["base"] = base
    return env


def build(output_dir: Path, base_url: str = "/") -> None:
    """Generate a complete static site into output_dir.

    Args:
        output_dir: Directory to write the site (will be wiped and recreated).
        base_url: URL prefix for all internal links (e.g. "/hestia/" for GitHub Pages).
    """
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    env = _make_env(base_url)
    all_recipes = load_all_recipes(_RECIPES_DIR)
    all_ingredients = _catalog.list_ingredients(catalog_path=_CATALOG_PATH)

    # --- index ---
    html = env.get_template("index.html.j2").render(
        recipes=all_recipes,
        q="", tag="", ingredient="",
        static=True,
    )
    (output_dir / "index.html").write_text(html, encoding="utf-8")

    # --- recipe pages ---
    for _path, recipe in all_recipes:
        catalog: dict[str, dict] = {}
        for ing in recipe.all_ingredients:
            entry = _catalog.get_ingredient(ing.name, catalog_path=_CATALOG_PATH)
            if entry:
                catalog[ing.name.lower()] = entry
        nutrition = compute_nutrition(recipe, catalog)
        html = render_html_str(recipe, nutrition, show_nav=True, base=base_url)
        recipe_dir = output_dir / "recipe" / recipe.slug
        recipe_dir.mkdir(parents=True, exist_ok=True)
        (recipe_dir / "index.html").write_text(html, encoding="utf-8")

    # --- ingredients list ---
    html = env.get_template("ingredients.html.j2").render(
        ingredients=all_ingredients,
        q="",
        static=True,
    )
    ingredients_dir = output_dir / "ingredients"
    ingredients_dir.mkdir(parents=True)
    (ingredients_dir / "index.html").write_text(html, encoding="utf-8")

    # --- individual ingredient pages ---
    for ing in all_ingredients:
        html = env.get_template("ingredient_detail.html.j2").render(
            ing=ing,
            static=True,
        )
        ing_slug = quote_plus(ing["name"])
        ing_dir = output_dir / "ingredient" / ing_slug
        ing_dir.mkdir(parents=True, exist_ok=True)
        (ing_dir / "index.html").write_text(html, encoding="utf-8")
