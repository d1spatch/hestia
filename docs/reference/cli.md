# CLI Reference

All commands follow the pattern:

```
hestia <group> <command> [arguments] [options]
```

Run `hestia --help`, `hestia recipe --help`, or `hestia ingredient --help` at any time for built-in help.

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
hestia recipe render sourdough_bread --format both
```

---

## `hestia ingredient`

### `ingredient add`

Add an ingredient to the catalog.

```
hestia ingredient add [options]
```

| Option | Description |
|---|---|
| `--name`, `-n` | Ingredient name (prompted if omitted) |
| `--price` | Price per kg (prompted if omitted) |
| `--currency` | Currency code (default: `USD`) |
| `--calories` | Calories per 100 g (prompted if omitted) |
| `--protein` | Protein per 100 g |
| `--carbs` | Carbohydrates per 100 g |
| `--fat` | Fat per 100 g |
| `--category` | Category label (e.g. `grain`, `dairy`) |
| `--aliases` | Comma-separated alternative names |
| `--notes` | Freeform notes |

**Examples:**
```bash
# Interactive
hestia ingredient add

# Fully specified
hestia ingredient add \
  --name "whole milk" \
  --price 1.10 \
  --calories 61 \
  --protein 3.2 \
  --carbs 4.8 \
  --fat 3.3 \
  --category dairy \
  --aliases "full fat milk,milk"
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

Update one or more fields of an existing ingredient.

```
hestia ingredient update <name> [options]
```

| Argument / Option | Description |
|---|---|
| `name` | Exact ingredient name (required) |
| `--price` | New price per kg |
| `--currency` | New currency |
| `--calories` | New calories per 100 g |
| `--protein` | New protein per 100 g |
| `--carbs` | New carbs per 100 g |
| `--fat` | New fat per 100 g |
| `--category` | New category |
| `--notes` | New notes |

**Examples:**
```bash
hestia ingredient update "bread flour" --price 1.35
hestia ingredient update "olive oil" --calories 884 --category fat
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
