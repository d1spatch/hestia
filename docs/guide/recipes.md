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

instructions:                  # (required) Ordered list of steps
  - Mix flour and water.
  - Add starter and salt.

notes: |                       # (optional) Freeform notes, multiline
  Hydration: 75%.
  Starter should be active and bubbly.
```

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
| `ml` | millilitres | 1 g (water density) |
| `l` | litres | 1000 g |
| `cl` | centilitres | 10 g |
| `dl` | decilitres | 100 g |

!!! note "Non-weight units"
    Units like `tsp`, `tbsp`, `cup`, or `piece` are stored and displayed correctly but cannot be converted to grams, so those ingredients are excluded from nutrition and cost calculations.

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
