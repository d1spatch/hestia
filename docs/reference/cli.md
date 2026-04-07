# CLI Reference

All commands follow the pattern:

```
hestia <group> <command> [arguments] [options]
```

Run `hestia --help`, `hestia recipe --help`, or `hestia ingredient --help` at any time for built-in help.

---

## `hestia serve`

Start the web interface — a local recipe browser and ingredient catalog.

```
hestia serve [options]
```

| Option | Description | Default |
|---|---|---|
| `--host` | Bind address | `127.0.0.1` |
| `--port`, `-p` | Port to listen on | `8765` |
| `--no-browser` | Don't auto-open browser | `false` |

**Example:**
```bash
hestia serve
hestia serve --port 9000 --no-browser
```

---

## `hestia build`

Generate a complete static site for deployment (e.g. GitHub Pages).

```
hestia build [--base-url URL] [--output DIR]
```

| Option | Description | Default |
|---|---|---|
| `--base-url` | URL prefix for all internal links | `/` |
| `--output` | Output directory (wiped and recreated) | `_site` |

Renders every recipe page, the ingredient catalog, and individual ingredient detail pages as static HTML.

**Examples:**
```bash
# Local preview
hestia build

# GitHub Pages (repo name = hestia)
hestia build --base-url /hestia/ --output _site
```

---

## `hestia recipe`

### `recipe add`

Copy a YAML file into `data/recipes/`.

```
hestia recipe add <path> [--force]
```

| Argument / Option | Description |
|---|---|
| `path` | Path to the recipe YAML file (required) |
| `--force`, `-f` | Overwrite if a file with the same name already exists |

**Example:**
```bash
hestia recipe add ~/my_recipes/bolognese.yaml
hestia recipe add bolognese.yaml --force
```

---

### `recipe list`

List all recipes in `data/recipes/`.

```
hestia recipe list
```

Displays: name, serves, tags, filename.

---

### `recipe show`

Display a recipe in the terminal with computed nutrition and cost.

```
hestia recipe show <name>
```

| Argument | Description |
|---|---|
| `name` | Recipe slug — the filename stem without `.yaml` |

**Example:**
```bash
hestia recipe show sourdough_bread
hestia recipe show bolognese
```

---

### `recipe render`

Render a recipe to HTML and/or PDF.

```
hestia recipe render <name> [--format FORMAT]
```

| Argument / Option | Description | Default |
|---|---|---|
| `name` | Recipe slug | (required) |
| `--format`, `-f` | `html`, `pdf`, or `both` | `both` |

Output is written to `output/<slug>.html` and/or `output/<slug>.pdf`.

**Examples:**
```bash
hestia recipe render sourdough_bread
hestia recipe render sourdough_bread --format html
hestia recipe render sourdough_bread --format pdf
```

---

## `hestia ingredient`

### `ingredient add`

Add an ingredient to the catalog. Designed to match what's printed on a product.

```
hestia ingredient add [options]
```

| Option | Description |
|---|---|
| `--name`, `-n` | Ingredient name (prompted if omitted) |
| `--package-price`, `-P` | Price paid for the whole package. Use with `--net-weight` to compute price/kg automatically |
| `--net-weight`, `-w` | Package net weight, e.g. `32oz`, `2lb`, `500g`, `1.5kg`. Use with `--package-price` |
| `--price` | Price per kg (alternative to `--package-price` + `--net-weight`) |
| `--currency` | Currency code (default: `USD`) |
| `--serving-size`, `-s` | Serving size in grams. When set, all nutrient values are treated as per-serving and scaled to per-100g. Sodium and cholesterol should be in mg (as on the label) |
| `--calories` | kcal per serving (or per 100g if `--serving-size` not set) |
| `--protein` | g protein |
| `--carbs` | g carbohydrates |
| `--fat` | g total fat |
| `--fiber` | g dietary fiber |
| `--sugar` | g total sugars |
| `--sodium` | mg sodium per serving (or g per 100g if `--serving-size` not set) |
| `--saturated-fat` | g saturated fat |
| `--cholesterol` | mg cholesterol per serving (or g per 100g if `--serving-size` not set) |
| `--vitamin-c` | mg Vitamin C |
| `--vitamin-d` | mcg Vitamin D |
| `--vitamin-k` | mcg Vitamin K |
| `--calcium` | mg calcium |
| `--iron` | mg iron |
| `--magnesium` | mg magnesium |
| `--potassium` | mg potassium |
| `--manganese` | mg manganese |
| `--category` | Category label, e.g. `grain`, `dairy` |
| `--aliases` | Comma-separated alternative names |
| `--notes` | Freeform notes |

**Examples:**
```bash
# From a nutrition label — serving size + package price
hestia ingredient add \
  --name "oat bran" --category grain \
  --package-price 8.99 --net-weight 32oz \
  --serving-size 30 \
  --calories 110 --protein 8 --carbs 19 --fat 3 \
  --fiber 6 --sugar 1 --sodium 0 --cholesterol 0

# Interactive
hestia ingredient add

# Per-100g values (e.g. from a reference database)
hestia ingredient add \
  --name "whole milk" --price 1.10 \
  --calories 61 --protein 3.2 --carbs 4.8 --fat 3.3 \
  --category dairy
```

---

### `ingredient list`

List all ingredients in the catalog.

```
hestia ingredient list [--category CATEGORY]
```

| Option | Description |
|---|---|
| `--category`, `-c` | Filter by category |

**Examples:**
```bash
hestia ingredient list
hestia ingredient list --category grain
```

---

### `ingredient update`

Update one or more fields of an existing ingredient. Run without flags for interactive mode.

```
hestia ingredient update <name> [options]
```

| Argument / Option | Description |
|---|---|
| `name` | Exact ingredient name (required) |
| `--package-price`, `-P` | Package price. Use with `--net-weight` to compute price/kg |
| `--net-weight`, `-w` | Package net weight, e.g. `32oz`, `2lb`, `500g` |
| `--price` | New price per kg |
| `--currency` | New currency code |
| `--serving-size`, `-s` | Serving size in grams — scales all nutrient flags to per-100g |
| `--calories` | New calories |
| `--protein` | New protein |
| `--carbs` | New carbohydrates |
| `--fat` | New fat |
| `--fiber` | New fiber |
| `--sugar` | New sugar |
| `--sodium` | New sodium |
| `--saturated-fat` | New saturated fat |
| `--cholesterol` | New cholesterol |
| `--vitamin-c` | New Vitamin C (mg) |
| `--vitamin-d` | New Vitamin D (mcg) |
| `--vitamin-k` | New Vitamin K (mcg) |
| `--calcium` | New calcium (mg) |
| `--iron` | New iron (mg) |
| `--magnesium` | New magnesium (mg) |
| `--potassium` | New potassium (mg) |
| `--manganese` | New manganese (mg) |
| `--category` | New category |
| `--notes` | New notes |

**Examples:**
```bash
# Interactive (shows current values, blank = keep)
hestia ingredient update "bread flour"

# Specific fields
hestia ingredient update "bread flour" --price 1.35
hestia ingredient update "olive oil" --calories 884 --category fat
```

---

### `ingredient update-price`

Record a new price observation for an ingredient. Appends to `price_history` and updates `price_per_kg`.

```
hestia ingredient update-price <name> [options]
```

| Argument / Option | Description |
|---|---|
| `name` | Ingredient name (required) |
| `--package-price`, `-P` | Price paid for the whole package. Use with `--net-weight` |
| `--net-weight`, `-w` | Package net weight, e.g. `32oz`, `2lb`, `500g`, `1.5kg` |
| `--price`, `-p` | Price per kg (alternative to `--package-price` + `--net-weight`) |
| `--store`, `-s` | Store or retailer name |
| `--currency` | Currency code (default: `USD`) |
| `--date`, `-d` | Date of purchase as `YYYY-MM-DD` (default: today) |

**Examples:**
```bash
hestia ingredient update-price "bread flour" -P 5.99 -w 5lb -s Costco
hestia ingredient update-price "bread flour" --price 1.32 --store "Whole Foods"
hestia ingredient update-price "olive oil" -P 12.99 -w 1l -d 2026-03-01 -s "Trader Joe's"
```

---

### `ingredient lookup-usda`

Search USDA FoodData Central and list matching foods with their FDC IDs.

```
hestia ingredient lookup-usda <query> [--limit N]
```

| Argument / Option | Description | Default |
|---|---|---|
| `query` | Search term | (required) |
| `--limit`, `-n` | Max results to return | `10` |

!!! tip "API key"
    Set `USDA_API_KEY` in `.env` for full rate limits. Free key at [fdc.nal.usda.gov](https://fdc.nal.usda.gov/api-key-signup.html). Without a key, the `DEMO_KEY` fallback allows ~30 requests/hour.

**Example:**
```bash
hestia ingredient lookup-usda "oat bran"
hestia ingredient lookup-usda "whole milk" --limit 5
```

---

### `ingredient import-usda`

Import full nutrition data from USDA FoodData Central by FDC ID.

```
hestia ingredient import-usda <fdc_id> [options]
```

| Argument / Option | Description |
|---|---|
| `fdc_id` | USDA FoodData Central ID (required) |
| `--name`, `-n` | Catalog name (defaults to the FDC description) |
| `--category`, `-c` | Category label |
| `--update` | Merge nutrition data into an existing entry instead of failing |

Populates macros, micronutrients, conversion data such as `g_per_tbsp`, `g_per_ml`, and `g_per_unit`, plus a `source` attribution block automatically.

**Example:**
```bash
# Full workflow
hestia ingredient lookup-usda "oat bran"
hestia ingredient import-usda 169762 --name "oat bran" --category grain
hestia ingredient update-price "oat bran" -P 8.99 -w 32oz -s Costco

# Update nutrition on an existing ingredient
hestia ingredient import-usda 169762 --name "oat bran" --update
```

---

### `ingredient import`

Bulk-import ingredients from a CSV file.

```
hestia ingredient import <csv_path>
```

| Argument | Description |
|---|---|
| `csv_path` | Path to the CSV file (required) |

The CSV must have a header row. The `name` column is required; all others are optional. Existing names are skipped.

**Example:**
```bash
hestia ingredient import ingredients.csv
```

See the [Ingredients guide](../guide/ingredients.md#bulk-import-from-csv) for the expected CSV format.
