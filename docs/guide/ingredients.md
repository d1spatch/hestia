# Ingredients

The ingredient catalog is a SQLite database (`data/ingredients.db`) that stores nutritional data, pricing, and aliases for every ingredient you use.

---

## Catalog fields

| Field | Description |
|---|---|
| `name` | Canonical ingredient name (unique, required) |
| `aliases` | Alternative names that recipes can use to refer to this ingredient |
| `price_per_kg` | Cost per kilogram in the given currency |
| `currency` | Currency code, e.g. `USD`, `GBP`, `EUR` (default: `USD`) |
| `calories_per_100g` | Kilocalories per 100 g |
| `protein_per_100g` | Grams of protein per 100 g |
| `carbs_per_100g` | Grams of carbohydrates per 100 g |
| `fat_per_100g` | Grams of fat per 100 g |
| `category` | Freeform category, e.g. `grain`, `dairy`, `vegetable` |
| `notes` | Freeform notes |

All fields except `name` are optional. Omitted nutrition fields are simply excluded from calculations.

---

## Commands

### Add an ingredient

```bash
# All fields via flags (scriptable, good for automation)
hestia ingredient add \
  --name "bread flour" \
  --price 1.20 \
  --calories 364 \
  --protein 12.0 \
  --carbs 72.0 \
  --fat 1.5 \
  --category grain \
  --aliases "plain flour,all-purpose flour" \
  --notes "Strong white flour, 12-13% protein"
```

Omit any flag to be prompted interactively:

```bash
hestia ingredient add
# > Ingredient name: bread flour
# > Price per kg: 1.20
# > Calories per 100g: 364
```

### List ingredients

```bash
# All ingredients
hestia ingredient list

# Filter by category
hestia ingredient list --category grain
```

### Update an ingredient

Update any field without re-entering everything:

```bash
hestia ingredient update "bread flour" --price 1.35
hestia ingredient update "olive oil" --calories 884 --category fat
```

---

## Bulk import from CSV

For adding many ingredients at once, prepare a CSV file and import it:

```bash
hestia ingredient import ingredients.csv
```

### CSV format

The first row must be a header. Column names match the catalog fields exactly. Only `name` is required; all other columns are optional.

```csv
name,category,price_per_kg,currency,calories_per_100g,protein_per_100g,carbs_per_100g,fat_per_100g,notes
bread flour,grain,1.20,USD,364,12.0,72.0,1.5,Strong white flour
whole milk,dairy,1.10,USD,61,3.2,4.8,3.3,Full fat
olive oil,fat,8.50,USD,884,0,0,100,Extra virgin
salt,seasoning,0.50,USD,0,0,0,0,
```

!!! tip "Skipped rows"
    Rows with a missing or empty `name` are skipped. Rows where the name already exists in the catalog are also skipped (not overwritten). The command reports how many were imported and how many were skipped.

---

## Tips

- **Aliases** — add common alternative names so your recipe YAML files are flexible. For example, storing `["AP flour", "plain flour"]` as aliases for `bread flour` means any of those names will match in a recipe.
- **Currency** — each ingredient stores its own currency. If a recipe mixes currencies, cost totals may be inaccurate. Keep a consistent currency across your catalog.
- **Nutritional data sources** — [USDA FoodData Central](https://fdc.nal.usda.gov/) is a free, comprehensive source of per-100g nutrition data.
