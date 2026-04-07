# Hestia

A precision cookbook CLI. Store recipes as YAML, catalog ingredients with prices and macros, render to HTML or PDF.

## Environment

- **Python**: always use `uv run python`, never bare `python`
- **Run CLI**: `uv run python -m hestia <command>`
- **Docs**: `uv run python -m mkdocs serve` (from project root)
- **Install (editable)**: `uv pip install -e .`
- **PDF output** requires MiKTeX (`pdflatex` on PATH)

## Key Commands

```bash
hestia serve
hestia recipe show <name>
hestia recipe render <name> --format html|pdf|both
hestia recipe add <path>
hestia recipe list
hestia ingredient add --name "..." --package-price 8.99 --net-weight 32oz --serving-size 30 --calories 110
hestia ingredient list [--category ...]
hestia ingredient update <name> [--price ...] [--calories ...]
hestia ingredient update-price <name> [-P <price> -w <weight> -s <store>]
hestia ingredient lookup-usda <query>
hestia ingredient import-usda <fdc_id> --name "..." --category <cat>
hestia ingredient import <csv_path>
```

## Project Layout

```text
hestia/
|-- hestia/
|   |-- cli.py          # Typer entry points, Rich output
|   |-- catalog.py      # YAML-backed ingredient catalog
|   |-- recipe.py       # Pydantic models, YAML parsing, nutrition math
|   |-- renderer.py     # Jinja2 to HTML / LaTeX / PDF; DEBUG_NUTRITION toggle here
|   |-- server.py       # Local web interface (hestia serve)
|   |-- usda.py         # USDA FoodData Central API client
|   `-- templates/      # recipe.html.j2, index.html.j2, base.html.j2, etc.
|-- data/
|   |-- ingredients.yaml
|   `-- recipes/
`-- output/
```

## Data Formats

Recipe YAML lives in `data/recipes/<slug>.yaml`; ingredient catalog data lives in `data/ingredients.yaml`.

## Conventions

- Ingredient lookup is case-insensitive and checks aliases
- Non-weight units are skipped in nutrition and cost math by design
- `catalog.py` is the active backend - all ingredient reads and writes go through it
- `renderer.py` has a `DEBUG_NUTRITION = False` toggle for per-ingredient breakdowns
- Use `pathlib.Path` throughout
- CLI errors exit with `typer.Exit(1)`
- No test suite exists - test manually via CLI

## Dependencies

`typer[all]`, `pydantic>=2.0`, `pyyaml`, `jinja2`, `rich`
Docs: `mkdocs`, `mkdocs-material`, `mkdocstrings[python]`
