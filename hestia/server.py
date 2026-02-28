"""Lightweight WSGI server for the Hestia cookbook web interface."""

from __future__ import annotations

import threading
import webbrowser
from pathlib import Path
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server, WSGIRequestHandler

from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import catalog as _catalog
from .recipe import compute_nutrition, load_all_recipes, load_recipe
from .renderer import render_html_str

_RECIPES_DIR = Path(__file__).parent.parent / "data" / "recipes"
_CATALOG_PATH = Path(__file__).parent.parent / "data" / "ingredients.yaml"
_TEMPLATES_DIR = Path(__file__).parent / "templates"

# ---------------------------------------------------------------------------
# Jinja2 env for web-only templates (index, ingredients, base)
# ---------------------------------------------------------------------------

def _web_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
    )


# ---------------------------------------------------------------------------
# In-memory recipe cache (loaded once at startup)
# ---------------------------------------------------------------------------

_recipe_cache: list | None = None


def _get_recipes():
    global _recipe_cache
    if _recipe_cache is None:
        _recipe_cache = load_all_recipes(_RECIPES_DIR)
    return _recipe_cache


def _build_catalog_for(recipe):
    catalog: dict[str, dict] = {}
    for ing in recipe.ingredients:
        entry = _catalog.get_ingredient(ing.name, catalog_path=_CATALOG_PATH)
        if entry:
            catalog[ing.name.lower()] = entry
    return catalog


# ---------------------------------------------------------------------------
# Route handlers — each returns (status, headers, body_bytes)
# ---------------------------------------------------------------------------

def _html_response(html: str, status: str = "200 OK"):
    return status, [("Content-Type", "text/html; charset=utf-8")], html.encode()


def _handle_index(query: str):
    params = parse_qs(query)
    q          = params.get("q", [""])[0].strip()
    tag        = params.get("tag", [""])[0].strip()
    ingredient = params.get("ingredient", [""])[0].strip()

    all_recipes = _get_recipes()
    filtered = all_recipes

    if q:
        filtered = [(p, r) for p, r in filtered if q.lower() in r.name.lower()]
    if tag:
        filtered = [(p, r) for p, r in filtered if tag.lower() in [t.lower() for t in r.tags]]
    if ingredient:
        filtered = [
            (p, r) for p, r in filtered
            if any(ingredient.lower() in ing.name.lower() for ing in r.ingredients)
        ]

    env = _web_env()
    html = env.get_template("index.html.j2").render(
        recipes=filtered,
        q=q,
        tag=tag,
        ingredient=ingredient,
    )
    return _html_response(html)


def _handle_recipe(slug: str):
    all_recipes = _get_recipes()
    match = next(((p, r) for p, r in all_recipes if r.slug == slug), None)
    if match is None:
        return _handle_404()
    _, recipe = match
    catalog = _build_catalog_for(recipe)
    nutrition = compute_nutrition(recipe, catalog)
    html = render_html_str(recipe, nutrition, show_nav=True)
    return _html_response(html)


def _handle_ingredients(query: str):
    params = parse_qs(query)
    q = params.get("q", [""])[0].strip()

    items = _catalog.list_ingredients(catalog_path=_CATALOG_PATH)
    if q:
        items = [i for i in items if q.lower() in i["name"].lower()]

    env = _web_env()
    html = env.get_template("ingredients.html.j2").render(ingredients=items, q=q)
    return _html_response(html)


def _handle_404():
    html = "<html><body><h1>404 Not Found</h1></body></html>"
    return _html_response(html, "404 Not Found")


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

def _route(environ):
    path = environ.get("PATH_INFO", "/").rstrip("/") or "/"
    query = environ.get("QUERY_STRING", "")
    parts = [p for p in path.strip("/").split("/") if p]

    if not parts:
        return _handle_index(query)
    if parts[0] == "recipe" and len(parts) == 2:
        return _handle_recipe(parts[1])
    if parts[0] == "ingredients" and len(parts) == 1:
        return _handle_ingredients(query)
    if parts[0] == "favicon.ico":
        return "404 Not Found", [], b""
    return _handle_404()


# ---------------------------------------------------------------------------
# WSGI application
# ---------------------------------------------------------------------------

def application(environ, start_response):
    status, headers, body = _route(environ)
    start_response(status, headers)
    return [body]


# ---------------------------------------------------------------------------
# Silent request handler (suppress access log noise)
# ---------------------------------------------------------------------------

class _QuietHandler(WSGIRequestHandler):
    def log_message(self, format, *args):  # noqa: A002
        pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run(host: str = "127.0.0.1", port: int = 8765, open_browser: bool = True) -> None:
    server = make_server(host, port, application, handler_class=_QuietHandler)
    url = f"http://{host}:{port}"
    if open_browser:
        threading.Timer(0.5, webbrowser.open, args=[url]).start()
    print(f"  Hestia running at {url}")
    print("  Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.")
    finally:
        server.server_close()
