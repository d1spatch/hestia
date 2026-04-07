# Recipes

Recipes in Hestia are plain YAML files. They are human-readable, easy to edit, and work naturally with version control.

---

## YAML format

```yaml
name: Sourdough Bread          # (required) Display name
serves: 1 loaf (900g)          # (optional) Serving description — string, int, or float
tags: [bread, fermented]       # (optional) Freeform tags for organisation

ingredients:                   # (required) List of ingredients
  - name: bread flour          # Must match a catalog entry name or alias
    amount: 500                # Numeric quantity
    unit: g                    # See supported units below
    optional: false            # (optional) Mark ingredient as optional
    note: ""                   # (optional) Short note shown next to ingredient
    nutrition_pct: 100         # (optional) % of ingredient counted toward nutrition (default 100)

instructions:                  # (required) Ordered list of steps
  - Mix flour and water.
  - Add starter and salt.

notes: |                       # (optional) Freeform notes, multiline
  Hydration: 75%.
  Starter should be active and bubbly.
```

In the HTML recipe page, notes support clickable links using either Markdown
link syntax like `[Serious Eats](https://example.com)` or bare `https://` URLs.

---

## Supported units

Hestia converts quantities to grams for nutrition and cost calculations.

| Unit | Description | Grams equivalent |
|---|---|---|
| `g` | grams | 1 g |
| `kg` | kilograms | 1000 g |
| `mg` | milligrams | 0.001 g |
| `oz` | ounces | 28.35 g |
| `lb` | pounds | 453.59 g |
| `ml` | millilitres | depends on `g_per_ml` (water = 1 g/mL) |
| `l` | litres | same, ×1000 |
| `cl` | centilitres | same, ×10 |
| `dl` | decilitres | same, ×100 |
| `tsp` | teaspoons | requires `g_per_tbsp` on the ingredient |
| `tbsp` | tablespoons | requires `g_per_tbsp` on the ingredient |
| `cup` | cups | requires `g_per_tbsp` on the ingredient |
| `pinch` | pinch | 2 g |

!!! note "Volume and cooking units"
    Cooking volume units (`tsp`, `tbsp`, `cup`) are converted to grams using the ingredient's `g_per_tbsp` catalog field (set automatically by `import-usda` or manually). Without it, those ingredients are excluded from nutrition and cost calculations. Liquid volume units (`ml`, `l`) use `g_per_ml` if set, otherwise assume water density (1 g/mL).

!!! note "Count units"
    `piece`, `whole`, and similar count units cannot be converted and are always excluded from calculations.

---

## Ingredient name matching

When rendering or showing a recipe, Hestia looks up each ingredient by name in the catalog:

1. **Exact name match** (case-insensitive)
2. **Alias match** — if you stored `["plain flour", "AP flour"]` as aliases for `bread flour`, any of those names will resolve

If an ingredient is not found, it is listed as missing — the recipe still renders, but that ingredient contributes no nutrition or cost data.

---

## Commands

### Add a recipe

```bash
hestia recipe add path/to/my_recipe.yaml
```

Copies the file into `data/recipes/`. Use `--force` to overwrite an existing file with the same name:

```bash
hestia recipe add my_recipe.yaml --force
```

You can also drop YAML files directly into `data/recipes/` without using the command.

### List all recipes

```bash
hestia recipe list
```

Displays name, serving size, tags, and filename for every recipe in `data/recipes/`.

### Show a recipe

```bash
hestia recipe show <name>
```

Where `<name>` is the filename stem (no `.yaml` extension). Displays the full recipe with computed nutrition and cost.

```bash
hestia recipe show sourdough_bread
```

### Render a recipe

```bash
hestia recipe render <name> --format html|pdf|both
```

See the [Rendering guide](rendering.md) for full details.

---

## Tips

- **File naming** — use `snake_case` filenames. The filename stem becomes the recipe slug used in all commands.
- **Version control** — the `data/recipes/` directory is just a folder of text files. Add it to git to track changes over time.
- **Bulk recipes** — you can add multiple YAML files at once by dropping them into `data/recipes/` directly.
