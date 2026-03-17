# Ingredients

The ingredient catalog is stored in `data/ingredients.yaml` — a plain YAML file you can view and edit directly. It holds nutritional data, pricing history, and aliases for every ingredient you use.

---

## Catalog fields

| Field | Description |
|---|---|
| `name` | Canonical ingredient name (unique, required) |
| `aliases` | Alternative names recipes can use to refer to this ingredient |
| `price_per_kg` | Current price per kilogram (auto-updated by `update-price`) |
| `currency` | Currency code, e.g. `USD`, `GBP`, `EUR` (default: `USD`) |
| `price_history` | List of dated price observations (appended by `update-price`) |
| `calories_per_100g` | Kilocalories per 100 g |
| `protein_per_100g` | Grams of protein per 100 g |
| `carbs_per_100g` | Grams of carbohydrates per 100 g |
| `fat_per_100g` | Grams of fat per 100 g |
| `fiber_per_100g` | Grams of dietary fiber per 100 g |
| `sugar_per_100g` | Grams of sugar per 100 g |
| `sodium_per_100g` | Grams of sodium per 100 g (stored as g, labels show mg) |
| `saturated_fat_per_100g` | Grams of saturated fat per 100 g |
| `cholesterol_per_100g` | Grams of cholesterol per 100 g (stored as g, labels show mg) |
| `calcium_per_100g` | Milligrams of calcium per 100 g |
| `iron_per_100g` | Milligrams of iron per 100 g |
| `magnesium_per_100g` | Milligrams of magnesium per 100 g |
| `potassium_per_100g` | Milligrams of potassium per 100 g |
| `manganese_per_100g` | Milligrams of manganese per 100 g |
| `vitamin_c_per_100g` | Milligrams of Vitamin C per 100 g |
| `vitamin_d_per_100g` | Micrograms of Vitamin D per 100 g |
| `vitamin_k_per_100g` | Micrograms of Vitamin K per 100 g |
| `category` | Freeform category, e.g. `grain`, `dairy`, `vegetable` |
| `source` | Provenance block (auto-populated by `import-usda`) |
| `notes` | Freeform notes |

All fields except `name` are optional. Omitted nutrition fields are excluded from calculations.

---

## Adding ingredients

### From a nutrition label (recommended)

The `--serving-size` flag lets you enter values exactly as printed on a US nutrition label — no math needed. Hestia converts everything to per-100g automatically. Sodium and cholesterol are expected in mg (as on the label).

```bash
hestia ingredient add \
  --name "oat bran" \
  --package-price 8.99 --net-weight 32oz \
  --category grain \
  --serving-size 30 \
  --calories 110 --protein 8 --carbs 19 --fat 3 \
  --fiber 6 --sugar 1 --sodium 0 --cholesterol 0
```

`--package-price` + `--net-weight` computes price/kg automatically from the store label — no math needed.

### Interactive mode

Omit any or all flags to be prompted step by step:

```bash
hestia ingredient add
# > Ingredient name: oat bran
# > Package price: 8.99
# > Net weight: 32oz
# > Serving size in grams: 30
# > Calories (kcal): 110
# ...
```

### Manual per-100g entry

If you already have per-100g values (e.g. from a database):

```bash
hestia ingredient add \
  --name "whole milk" \
  --price 1.10 \
  --calories 61 --protein 3.2 --carbs 4.8 --fat 3.3 \
  --category dairy
```

---

## Importing from USDA FoodData Central

The fastest way to get complete nutrition data for whole foods.

### Step 1 — Search for the food

```bash
hestia ingredient lookup-usda "oat bran"
```

Returns a table of matching foods with their FDC IDs and data types.

### Step 2 — Import by FDC ID

```bash
hestia ingredient import-usda 169762 --name "oat bran" --category grain
```

Populates all available macros, micronutrients, and a `source` attribution block automatically.

Use `--update` to merge nutrition data into an ingredient that already exists in the catalog:

```bash
hestia ingredient import-usda 169762 --name "oat bran" --update
```

### Step 3 — Add a price

USDA data doesn't include pricing. Add it separately:

```bash
hestia ingredient update-price "oat bran" -P 8.99 -w 32oz -s Costco
```

---

## Updating prices

Use `update-price` to record a new price observation. Each call appends to the ingredient's `price_history` and updates `price_per_kg` to the latest value.

```bash
# From a store label (price/kg computed automatically)
hestia ingredient update-price "bread flour" -P 5.99 -w 5lb -s Costco

# Direct price/kg
hestia ingredient update-price "bread flour" --price 1.32 --store "Whole Foods"

# With a specific date
hestia ingredient update-price "bread flour" -P 5.49 -w 5lb -d 2026-01-15
```

Run without flags to be prompted interactively.

---

## Updating other fields

Update any field without re-entering everything:

```bash
hestia ingredient update "bread flour" --price 1.35
hestia ingredient update "olive oil" --calories 884 --category fat
```

Run without flags for interactive mode — shows current values and prompts for each field (blank = keep current):

```bash
hestia ingredient update "bread flour"
```

---

## Listing ingredients

```bash
# All ingredients
hestia ingredient list

# Filter by category
hestia ingredient list --category grain
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
    Rows with a missing or empty `name` are skipped. Rows where the name already exists are also skipped (not overwritten). The command reports how many were imported and how many were skipped.

---

## Tips

- **Aliases** — add common alternative names so recipe YAML files are flexible. For example, storing `["AP flour", "plain flour"]` as aliases for `bread flour` means any of those names will match.
- **Currency** — each ingredient stores its own currency. Keep a consistent currency across your catalog for accurate recipe cost totals.
- **USDA import vs manual** — use `import-usda` for whole foods; use `ingredient add` with `--serving-size` for packaged products with a nutrition label.
