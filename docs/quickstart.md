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

Ingredients are stored in `data/ingredients.yaml` — a plain human-editable file. Add them with flags or interactively:

```bash
# With flags (scriptable)
hestia ingredient add \
  --name "bread flour" \
  --package-price 5.99 --net-weight 5lb \
  --serving-size 30 \
  --calories 110 --protein 4 --carbs 22 --fat 0.5 \
  --category grain

# Interactive mode (omit any flag to be prompted)
hestia ingredient add
```

Or import nutritional data directly from the USDA FoodData Central database:

```bash
hestia ingredient lookup-usda "bread flour"
hestia ingredient import-usda 169761 --name "bread flour" --category grain
hestia ingredient update-price "bread flour" -P 5.99 -w 5lb -s "Whole Foods"
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

Hestia displays the recipe with computed nutrition and estimated cost based on your ingredient catalog.

---

## Step 5 — Browse in the web UI

```bash
hestia serve
```

Opens a local web interface at `http://127.0.0.1:8765` with a recipe browser and ingredient catalog.

---

## Step 6 — Render output

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

- [Recipes guide](guide/recipes.md) — full YAML format reference, units, grouped ingredients
- [Ingredients guide](guide/ingredients.md) — USDA import, pricing, bulk CSV import
- [Rendering guide](guide/rendering.md) — PDF setup, template customisation
- [CLI Reference](reference/cli.md) — complete command reference
