# Hestia

A cost/nutrition oriented cookbook

## Features

- **Recipe YAML files** — human-editable, version-control friendly
- **Ingredient catalog** — YAML file with price per kg, calories, macros
- **Computed nutrition & cost** — automatically calculated per recipe
- **HTML output** — print-ready, styled, opens in any browser
- **PDF output** — typeset via LaTeX (requires MiKTeX)

## Installation

```bash
pip install -e .
```

> **PDF output** requires [MiKTeX](https://miktex.org/download). Install it and ensure `pdflatex` is on your PATH.

## Quick Start

```bash
# Add an ingredient to the catalog
hestia ingredient add --name "bread flour" --price 1.20 --calories 364

# List your catalog
hestia ingredient list

# Drop a recipe YAML in data/recipes/, then show it
hestia recipe show sourdough_bread

# Render to HTML + PDF
hestia recipe render sourdough_bread --format both
```

## Recipe Format

```yaml
name: Sourdough Bread
serves: 1 loaf
tags: [bread, fermented]

ingredients:
  - name: bread flour
    amount: 500
    unit: g
  - name: water
    amount: 375
    unit: ml

instructions:
  - Mix flour and water. Rest 30 minutes.
  - Add starter and salt. Bulk ferment 4-6 hours.

notes: |
  Hydration: 75%.
```

## Documentation

Full documentation is available in the `docs/` folder or via the live site:

```bash
pip install -r requirements-docs.txt
mkdocs serve
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Project Layout

```
hestia/
├── hestia/           # Python package
│   ├── cli.py        # All CLI commands (Typer)
│   ├── catalog.py    # Ingredient catalog (YAML)
│   ├── recipe.py     # YAML parsing + nutrition math
│   ├── renderer.py   # Jinja2 → HTML / LaTeX / PDF
│   └── templates/    # recipe.html.j2, recipe.tex.j2
├── data/
│   ├── ingredients.yaml
│   └── recipes/      # Put your .yaml recipe files here
└── output/           # Generated HTML and PDF files
```