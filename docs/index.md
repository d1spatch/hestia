# Hestia

**A precision cookbook CLI for people who care about exactly what goes into their food.**

Hestia lets you store recipes with exact weights and measurements, build an ingredient catalog with prices and nutritional data, and render beautiful output as HTML or typeset PDF.

---

## Why Hestia?

Most recipe apps trade precision for convenience. Hestia is built differently:

- **Exact weights** — every ingredient is specified in grams, millilitres, or whatever unit you choose. No "a handful of" or "to taste."
- **Ingredient catalog** — a central database of ingredients with price per kg, calories, and macros. Add a recipe and instantly see its cost and calorie count.
- **Plain-text recipes** — recipes live as YAML files that you can read, edit, diff, and version-control with git.
- **Beautiful output** — render any recipe to a print-ready HTML page or a typeset PDF via LaTeX.

---

## At a glance

```bash
# Add ingredients to the catalog
hestia ingredient add --name "bread flour" --price 1.20 --calories 364

# Show a recipe with computed cost and nutrition
hestia recipe show sourdough_bread

# Render to HTML and PDF
hestia recipe render sourdough_bread --format both
```

---

## Navigation

| Section | What's inside |
|---|---|
| [Quickstart](quickstart.md) | Install, add your first recipe, render output |
| [Recipes](guide/recipes.md) | YAML format, adding and listing recipes |
| [Ingredients](guide/ingredients.md) | Catalog management, bulk CSV import |
| [Rendering](guide/rendering.md) | HTML and PDF output, MiKTeX setup |
| [CLI Reference](reference/cli.md) | Every command and option |
| [API Reference](reference/recipe.md) | Python module documentation |
