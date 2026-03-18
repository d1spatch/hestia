# Web UI

Hestia includes a full web interface — a browseable recipe and ingredient catalog you can run locally or deploy as a static site.

---

## Local server

```bash
hestia serve
```

Opens a local web server at `http://127.0.0.1:8765` and launches your browser automatically. The interface includes:

- **Recipe index** — searchable and filterable by name, tag, or ingredient
- **Recipe pages** — full recipe with ingredients, instructions, nutrition facts, and cost breakdown
- **Ingredient catalog** — sortable table with macros and price per kg
- **Ingredient detail** — full nutrition panel and price history chart

| Option | Description | Default |
|---|---|---|
| `--host` | Bind address | `127.0.0.1` |
| `--port`, `-p` | Port | `8765` |
| `--no-browser` | Don't auto-open browser | `false` |

```bash
hestia serve --port 9000 --no-browser
```

!!! tip "Docs locally"
    The **Docs** link in the nav bar serves from the pre-built MkDocs output (`site/` directory). Build it once before starting the server:
    ```bash
    python -m mkdocs build
    hestia serve
    ```
    Without a `site/` build the Docs link returns 404.

---

## Static site (GitHub Pages)

`hestia build` generates a fully static version of the web UI — no server required.

```bash
hestia build --base-url /hestia/ --output _site
```

| Option | Description | Default |
|---|---|---|
| `--base-url` | URL prefix for all internal links | `/` |
| `--output` | Output directory | `_site` |

The generated `_site/` directory contains:

| Path | Content |
|---|---|
| `index.html` | Recipe browser |
| `recipe/<slug>/index.html` | Individual recipe pages |
| `ingredients/index.html` | Ingredient catalog |
| `ingredient/<name>/index.html` | Ingredient detail pages |

Search on the static site is handled entirely by client-side JavaScript — no server needed.

---

## GitHub Pages deployment

The included workflow at `.github/workflows/pages.yml` builds and deploys automatically on every push to `main`.

The workflow:

1. Installs Hestia and its dependencies
2. Runs `hestia build` to generate the app static site
3. Runs `mkdocs build` to generate this documentation at `/docs/`
4. Uploads the combined `_site/` directory to GitHub Pages

After enabling GitHub Pages in your repository settings (**Settings → Pages → Source: GitHub Actions**), pushes to `main` will deploy to:

```
https://<username>.github.io/<repo>/        ← recipe web UI
https://<username>.github.io/<repo>/docs/   ← this documentation
```

---

## Templates

The web UI is built from Jinja2 templates in `hestia/templates/`:

| Template | Purpose |
|---|---|
| `base.html.j2` | Shared layout, navigation, and CSS palette |
| `index.html.j2` | Recipe browser / search |
| `recipe.html.j2` | Individual recipe page |
| `ingredients.html.j2` | Ingredient catalog table |
| `ingredient_detail.html.j2` | Ingredient detail with nutrition and price history |

All templates extend `base.html.j2`. The colour palette is defined there as CSS custom properties — see [Rendering Output](rendering.md#html-customisation) for details.
