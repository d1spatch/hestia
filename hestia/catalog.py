"""YAML-backed ingredient catalog.

The catalog is a single human-editable file at ``data/ingredients.yaml``.
Keys are ingredient names; values are dicts of optional fields.

Example entry::

    bread flour:
      category: grain
      price_per_kg: 1.20
      currency: USD
      calories_per_100g: 364.0
      protein_per_100g: 12.0
      carbs_per_100g: 72.0
      fat_per_100g: 1.5
      aliases: [plain flour, all-purpose flour]
      notes: Strong white flour, ~12% protein
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import yaml

_DEFAULT_CATALOG = Path(__file__).parent.parent / "data" / "ingredients.yaml"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load(catalog_path: Path) -> dict[str, dict[str, Any]]:
    """Read the catalog file. Returns an empty dict if the file doesn't exist."""
    if not catalog_path.exists():
        return {}
    with open(catalog_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def _save(catalog: dict[str, dict[str, Any]], catalog_path: Path) -> None:
    """Write the catalog back to disk, sorted by ingredient name."""
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    sorted_catalog = dict(sorted(catalog.items(), key=lambda x: x[0].lower()))
    with open(catalog_path, "w", encoding="utf-8") as f:
        yaml.dump(sorted_catalog, f, default_flow_style=False, allow_unicode=True)


def _to_row(name: str, data: dict[str, Any]) -> dict[str, Any]:
    """Normalise a catalog entry into a flat dict with a 'name' key."""
    row = {"name": name, **data}
    if "aliases" not in row:
        row["aliases"] = []
    elif isinstance(row["aliases"], str):
        row["aliases"] = [a.strip() for a in row["aliases"].split(",")]
    return row


# ---------------------------------------------------------------------------
# Public API  (same signatures as the old db.py)
# ---------------------------------------------------------------------------

def add_ingredient(
    data: dict[str, Any],
    catalog_path: Path = _DEFAULT_CATALOG,
) -> None:
    """Add a new ingredient to the catalog.

    Args:
        data: Dict of fields. ``name`` is required and must be unique.
            ``aliases`` may be a list or a comma-separated string.
        catalog_path: Path to ``ingredients.yaml``. Created if absent.

    Raises:
        ValueError: If an ingredient with the same name already exists.
    """
    name = data.get("name")
    if not name:
        raise ValueError("'name' is required.")
    catalog = _load(catalog_path)
    if name in catalog:
        raise ValueError(f"Ingredient '{name}' already exists. Use update instead.")
    entry = {k: v for k, v in data.items() if k != "name" and v is not None}
    if "aliases" in entry and isinstance(entry["aliases"], str):
        entry["aliases"] = [a.strip() for a in entry["aliases"].split(",")]
    catalog[name] = entry
    _save(catalog, catalog_path)


def update_ingredient(
    name: str,
    updates: dict[str, Any],
    catalog_path: Path = _DEFAULT_CATALOG,
) -> None:
    """Update one or more fields on an existing ingredient.

    Args:
        name: Exact ingredient name to update.
        updates: Fields to change. Only provided keys are modified.
        catalog_path: Path to ``ingredients.yaml``.

    Raises:
        ValueError: If the ingredient is not found.
    """
    catalog = _load(catalog_path)
    if name not in catalog:
        raise ValueError(f"Ingredient '{name}' not found.")
    entry = catalog[name]
    for k, v in updates.items():
        if k == "name":
            continue
        if v is None:
            entry.pop(k, None)
        else:
            entry[k] = v
    _save(catalog, catalog_path)


def get_ingredient(
    name: str,
    catalog_path: Path = _DEFAULT_CATALOG,
) -> dict[str, Any] | None:
    """Fetch one ingredient by exact name or alias.

    Lookup order:
    1. Exact name match (case-sensitive, matching the YAML key).
    2. Case-insensitive alias match.

    Args:
        name: Ingredient name or alias to search for.
        catalog_path: Path to ``ingredients.yaml``.

    Returns:
        A dict with a ``name`` key plus all stored fields, or ``None`` if not found.
    """
    catalog = _load(catalog_path)
    if name in catalog:
        return _to_row(name, catalog[name])
    # Case-insensitive name fallback
    for key, entry in catalog.items():
        if key.lower() == name.lower():
            return _to_row(key, entry)
        aliases = entry.get("aliases") or []
        if isinstance(aliases, str):
            aliases = [a.strip() for a in aliases.split(",")]
        if name.lower() in [a.lower() for a in aliases]:
            return _to_row(key, entry)
    return None


def list_ingredients(
    category: str | None = None,
    catalog_path: Path = _DEFAULT_CATALOG,
) -> list[dict[str, Any]]:
    """Return all ingredients, sorted by name.

    Args:
        category: If provided, only return ingredients matching this category.
        catalog_path: Path to ``ingredients.yaml``.

    Returns:
        List of dicts, each with a ``name`` key plus all stored fields.
    """
    catalog = _load(catalog_path)
    rows = [_to_row(name, entry) for name, entry in catalog.items()]
    if category:
        rows = [r for r in rows if r.get("category") == category]
    return sorted(rows, key=lambda r: r["name"].lower())


def import_csv(
    path: Path,
    catalog_path: Path = _DEFAULT_CATALOG,
) -> tuple[int, int]:
    """Bulk-import ingredients from a CSV file.

    The CSV must have a header row. The ``name`` column is required; all
    other columns are optional and match the catalog field names exactly.

    Expected columns:
        ``name``, ``aliases``, ``price_per_kg``, ``currency``,
        ``calories_per_100g``, ``protein_per_100g``, ``carbs_per_100g``,
        ``fat_per_100g``, ``category``, ``notes``

    Rows with a missing name, or whose name already exists, are skipped.

    Args:
        path: Path to the CSV file.
        catalog_path: Path to ``ingredients.yaml``.

    Returns:
        A ``(inserted, skipped)`` tuple of row counts.
    """
    inserted = skipped = 0
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row = {k.strip(): v.strip() for k, v in row.items() if v and v.strip()}
            if not row.get("name"):
                skipped += 1
                continue
            for float_col in ("price_per_kg", "calories_per_100g", "protein_per_100g",
                               "carbs_per_100g", "fat_per_100g"):
                if float_col in row:
                    try:
                        row[float_col] = float(row[float_col])
                    except ValueError:
                        del row[float_col]
            try:
                add_ingredient(row, catalog_path)
                inserted += 1
            except ValueError:
                skipped += 1
    return inserted, skipped
