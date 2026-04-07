# Hestia — Claude Context

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

```
hestia/
├── hestia/
│   ├── cli.py          # Typer entry points, Rich output
│   ├── catalog.py      # YAML-backed ingredient catalog
│   ├── recipe.py       # Pydantic models, YAML parsing, nutrition math
│   ├── renderer.py     # Jinja2 → HTML / LaTeX / PDF; DEBUG_NUTRITION toggle here
│   ├── server.py       # Local web interface (hestia serve)
│   ├── usda.py         # USDA FoodData Central API client
│   └── templates/      # recipe.html.j2, index.html.j2, base.html.j2, etc.
├── data/
│   ├── ingredients.yaml    # Human-editable ingredient catalog
│   └── recipes/            # User recipe YAML files go here
└── output/                 # Generated HTML/PDF files (named by recipe slug)
```

## Data Formats

**Recipe YAML** (`data/recipes/<slug>.yaml`):
```yaml
name: Sourdough Bread
serves: 1 loaf
tags: [bread, fermented]
ingredients:
  - name: bread flour
    amount: 500
    unit: g   # weight units: g, kg, mg, oz, lb; volume: ml, l, cl, dl
instructions:
  - Step one.
notes: |
  Optional notes.
```

**Ingredient catalog** (`data/ingredients.yaml`):
```yaml
bread flour:
  category: grain
  price_per_kg: 1.20
  currency: USD
  calories_per_100g: 364.0
  protein_per_100g: 12.0
  carbs_per_100g: 72.0
  fat_per_100g: 1.5
  aliases: [strong flour, white flour]
  notes: Optional text.
```

## Conventions

- Ingredient lookup is **case-insensitive** and checks aliases
- Non-weight units (tsp, cup, piece) are skipped in nutrition/cost math — this is intentional
- `catalog.py` is the active backend — all ingredient reads/writes go through it
- `renderer.py` has a `DEBUG_NUTRITION = False` toggle — set to `True` to show per-ingredient breakdown on recipe pages
- Use `pathlib.Path` throughout (no raw string paths)
- CLI errors exit with `typer.Exit(1)`
- No test suite exists — test manually via CLI

## Dependencies

`typer[all]`, `pydantic>=2.0`, `pyyaml`, `jinja2`, `rich`
Docs: `mkdocs`, `mkdocs-material`, `mkdocstrings[python]`

## Checkpoint

After every response where meaningful work was done, overwrite `notes/checkpoint.md`:

```
## YYYY-MM-DD HH:MM
**Last query:** [one-line summary of what was asked]
**Status:** done | in-progress | blocked
**Resume here:** [exact next action if restarting mid-session]
```

One entry only — always overwrite, never append.

## Large Output

When generating large files, datasets, or multi-section documents: write and save after each logical unit (section, record batch, chapter). Never buffer the entire output before saving.

## Session Log

Append to `PROJECT_LOG.md` at end of each session. Keep last 5 entries only.
