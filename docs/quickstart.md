# Quickstart

## Installation

Clone or open the project, then install in editable mode:

```bash
pip install -e .
```

This installs all dependencies and makes the `hestia` command available in your terminal.

!!! note "PDF output"
    PDF rendering requires **MiKTeX** (Windows) or **TeX Live** (Linux/macOS).
    See [Rendering Output](guide/rendering.md#pdf-output) for setup instructions.

---

## Step 1 — Add ingredients to the catalog

Ingredients are stored in a central SQLite database. Add them one by one with flags, or interactively:

```bash
# With flags (scriptable)
hestia ingredient add \
  --name "bread flour" \
  --price 1.20 \
  --calories 364 \
  --protein 12.0 \
  --carbs 72.0 \
  --fat 1.5 \
  --category grain

# Interactive mode (omit the flags you want to be prompted for)
hestia ingredient add
```

Verify the catalog:

```bash
hestia ingredient list
```

---

## Step 2 — Write a recipe

Create a YAML file anywhere on your system. For example, `my_recipe.yaml`:

```yaml
name: Sourdough Bread
serves: 1 loaf (900g)
tags: [bread, fermented, baking]

ingredients:
  - name: bread flour
    amount: 500
    unit: g
  - name: water
    amount: 375
    unit: ml
  - name: sourdough starter
    amount: 100
    unit: g
  - name: salt
    amount: 10
    unit: g

instructions:
  - Combine flour and 350ml water. Rest 30 minutes (autolyse).
  - Add starter and salt. Stretch-and-fold for 2 hours.
  - Bulk ferment 2-4 hours until risen ~50%.
  - Shape, place in banneton, cold-proof overnight.
  - Bake at 250°C in a Dutch oven: 20 min covered, 25 min uncovered.
  - Cool 1 hour before slicing.

notes: |
  Hydration: 75%. Feed your starter 8-12 hours before mixing.
```

Ingredient names in the recipe must match names (or aliases) in your catalog.

---

## Step 3 — Add the recipe to Hestia

```bash
hestia recipe add my_recipe.yaml
```

This copies the file to `data/recipes/`. You can also drop YAML files directly into that folder.

---

## Step 4 — View the recipe

```bash
hestia recipe show sourdough_bread
```

Hestia displays the recipe with computed calories and estimated cost based on your ingredient catalog.

---

## Step 5 — Render output

```bash
# HTML only
hestia recipe render sourdough_bread --format html

# PDF only (requires pdflatex)
hestia recipe render sourdough_bread --format pdf

# Both
hestia recipe render sourdough_bread --format both
```

Output files are written to the `output/` directory.

---

## Next steps

- [Recipes guide](guide/recipes.md) — full YAML format reference, units, tags
- [Ingredients guide](guide/ingredients.md) — bulk import from CSV, updating prices
- [Rendering guide](guide/rendering.md) — PDF setup, template customisation
- [CLI Reference](reference/cli.md) — complete command reference
