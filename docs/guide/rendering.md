# Rendering Output

Hestia can render any recipe to **HTML** (no extra tools needed) or **PDF** (requires LaTeX).

---

## The render command

```bash
hestia recipe render <name> --format html|pdf|both
```

Output files are written to the `output/` directory, named after the recipe slug (e.g. `sourdough_bread.html`, `sourdough_bread.pdf`).

---

## HTML output

HTML rendering works out of the box with no extra dependencies.

```bash
hestia recipe render sourdough_bread --format html
```

The generated file (`output/sourdough_bread.html`) is self-contained — all styles are embedded. Open it in any browser, or print it directly from the browser with **Ctrl+P**.

### What's included

- Recipe title, serves, and tags
- Ingredient table with amounts and units
- Numbered instructions
- Notes block
- Nutrition and cost summary
- Warning if any ingredients are missing from the catalog

---

## PDF output

PDF rendering uses LaTeX for professional typesetting. It requires `pdflatex` to be installed and on your PATH.

```bash
hestia recipe render sourdough_bread --format pdf
```

This generates two files:

- `output/sourdough_bread.tex` — the LaTeX source
- `output/sourdough_bread.pdf` — the compiled PDF

### Setting up pdflatex on Windows (MiKTeX)

1. Download and install [MiKTeX](https://miktex.org/download) — choose the **Basic MiKTeX Installer**.
2. During installation, set "Install missing packages on-the-fly" to **Yes**.
3. After installation, open the **MiKTeX Console**, go to **Updates**, and update all packages.
4. Open a new terminal and verify:

```bash
pdflatex --version
```

On first run, MiKTeX will automatically download any missing LaTeX packages (requires internet).

### Setting up pdflatex on Linux/macOS (TeX Live)

=== "Ubuntu/Debian"
    ```bash
    sudo apt install texlive-latex-recommended texlive-fonts-recommended
    ```

=== "macOS (Homebrew)"
    ```bash
    brew install --cask mactex
    ```

---

## Rendering both formats

```bash
hestia recipe render sourdough_bread --format both
```

Generates HTML, `.tex`, and `.pdf` in one step.

---

## Customising templates

The Jinja2 templates live in `hestia/templates/`:

| File | Description |
|---|---|
| `recipe.html.j2` | HTML template with embedded CSS |
| `recipe.tex.j2` | LaTeX template |

Both templates receive two variables:

- `recipe` — a `Recipe` object with fields: `name`, `serves`, `tags`, `ingredients`, `instructions`, `notes`
- `nutrition` — a dict with keys: `calories`, `cost`, `currency`, `missing_ingredients`

### HTML customisation

Edit `recipe.html.j2` directly. The CSS is in a `<style>` block at the top. Colours are controlled via CSS custom properties:

```css
:root {
  --accent: #5c4033;   /* headings, borders */
  --light:  #fdf6ec;   /* page background  */
  --border: #d4b896;   /* table borders    */
  --text:   #2c1f14;   /* body text        */
}
```

### LaTeX customisation

Edit `recipe.tex.j2`. The template uses custom Jinja2 delimiters (`\VAR{...}` and `\BLOCK{...}`) to avoid conflicts with LaTeX braces. Standard LaTeX packages (`booktabs`, `geometry`, `xcolor`, `titlesec`) are used and can be adjusted freely.

!!! warning "LaTeX special characters"
    Inside the template, use the `| latex` filter on any variable that may contain characters like `&`, `%`, `$`, `_` — the filter escapes them automatically.

    ```
    \VAR{ recipe.name | latex }
    ```
