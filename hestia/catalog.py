"""YAML-backed ingredient catalog.

The catalog is a single human-editable file at ``data/ingredients.yaml``.
Keys are ingredient names; values are structured dicts with three optional sections.

Example entry::

    bread flour:
      nutrition:
        calories_per_100g: 364.0
        protein_per_100g: 12.0
        carbs_per_100g: 72.0
        fat_per_100g: 1.5
        fiber_per_100g: 2.7
        sugar_per_100g: 0.3
        sodium_per_100g: 0.002
        saturated_fat_per_100g: 0.2
        cholesterol_per_100g: 0.0
        source:
          type: usda
          fdc_id: 169761
          description: "Flour, wheat, bread"
          retrieved: 2026-03-14
      pricing:
        currency: USD
        price_per_kg: 1.20
        price_history:
          - date: 2026-01-01
            price_per_kg: 1.15
            store: Costco
          - date: 2026-03-14
            price_per_kg: 1.20
            store: Whole Foods
      user_defined:
        category: grain
        aliases: [plain flour, all-purpose flour]
        g_per_tbsp: 8.0
        notes: Strong white flour, ~12% protein

Internally all entries are flattened to plain dicts for compatibility with
recipe.py, cli.py, and usda.py. The nested structure is only on disk.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import yaml

_DEFAULT_CATALOG = Path(__file__).parent.parent / "data" / "ingredients.yaml"

# Fields that belong in each section on disk.
_NUTRITION_FIELDS = frozenset({
    "calories_per_100g", "protein_per_100g", "carbs_per_100g", "fat_per_100g",
    "fiber_per_100g", "sugar_per_100g", "sodium_per_100g", "saturated_fat_per_100g",
    "cholesterol_per_100g", "vitamin_c_per_100g", "vitamin_d_per_100g",
    "vitamin_k_per_100g", "calcium_per_100g", "iron_per_100g", "magnesium_per_100g",
    "potassium_per_100g", "manganese_per_100g", "g_per_tbsp", "g_per_ml", "g_per_unit", "source",
    "unit_sizes",  # dict mapping unit name → grams per unit (e.g. {whole: 100.0, clove: 5.0})
})
_PRICING_FIELDS = frozenset({"currency", "price_per_kg", "price_history"})
_USER_DEFINED_FIELDS = frozenset({"category", "aliases", "notes"})


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load(catalog_path: Path) -> dict[str, dict[str, Any]]:
    """Read the catalog file and return flat entries. Returns {} if absent.

    Handles both the current nested format (nutrition/pricing/user_defined
    sections) and the legacy flat format transparently.
    """
    if not catalog_path.exists():
        return {}
    with open(catalog_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    for name, entry in data.items():
        flat: dict[str, Any] = {}
        for section in ("nutrition", "pricing", "user_defined"):
            section_data = entry.pop(section, None)
            if isinstance(section_data, dict):
                flat.update(section_data)
        flat.update(entry)  # remaining top-level fields (legacy flat or unknowns)
        # Migrate unit_conversions: {tbsp: X} → g_per_tbsp: X
        uc = flat.pop("unit_conversions", None)
        if isinstance(uc, dict) and "tbsp" in uc and "g_per_tbsp" not in flat:
            flat["g_per_tbsp"] = uc["tbsp"]
        data[name] = flat
    return data


def _structure(flat_entry: dict[str, Any]) -> dict[str, Any]:
    """Convert a flat entry dict into the nested section format for YAML storage."""
    nutrition = {k: v for k, v in flat_entry.items() if k in _NUTRITION_FIELDS}
    pricing = {k: v for k, v in flat_entry.items() if k in _PRICING_FIELDS}
    user_defined = {k: v for k, v in flat_entry.items() if k in _USER_DEFINED_FIELDS}
    other = {k: v for k, v in flat_entry.items()
             if k not in _NUTRITION_FIELDS | _PRICING_FIELDS | _USER_DEFINED_FIELDS}
    structured: dict[str, Any] = {}
    structured.update(other)
    if nutrition:
        structured["nutrition"] = nutrition
    if pricing:
        structured["pricing"] = pricing
    if user_defined:
        structured["user_defined"] = user_defined
    return structured


def _save(catalog: dict[str, dict[str, Any]], catalog_path: Path) -> None:
    """Write the catalog back to disk in nested section format, sorted by name."""
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    sorted_catalog = dict(sorted(catalog.items(), key=lambda x: x[0].lower()))
    structured_catalog = {name: _structure(entry) for name, entry in sorted_catalog.items()}
    with open(catalog_path, "w", encoding="utf-8") as f:
        yaml.dump(structured_catalog, f, default_flow_style=False, allow_unicode=True)


def _to_row(name: str, data: dict[str, Any]) -> dict[str, Any]:
    """Normalise a catalog entry into a flat dict with a 'name' key."""
    row = {"name": name, **data}
    if "aliases" not in row:
        row["aliases"] = []
    elif isinstance(row["aliases"], str):
        row["aliases"] = [a.strip() for a in row["aliases"].split(",")]
    return row


def preserve_existing_fields(
    existing: dict[str, Any],
    updates: dict[str, Any],
    fields: set[str] | frozenset[str],
) -> dict[str, Any]:
    """Return updates with selected keys omitted when the existing entry has values.

    This is useful for merge-style imports where some fields may have been
    curated manually and should not be overwritten automatically.
    """
    filtered = dict(updates)
    for field in fields:
        if existing.get(field) is not None:
            filtered.pop(field, None)
    return filtered


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
            for float_col in (
                "price_per_kg", "calories_per_100g", "protein_per_100g",
                "carbs_per_100g", "fat_per_100g", "fiber_per_100g",
                "sugar_per_100g", "sodium_per_100g", "saturated_fat_per_100g",
                "cholesterol_per_100g",
            ):
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


def record_price(
    name: str,
    price: float,
    currency: str = "USD",
    store: str | None = None,
    record_date: str | None = None,
    package_price: float | None = None,
    net_weight: str | None = None,
    catalog_path: Path = _DEFAULT_CATALOG,
) -> None:
    """Append a price observation to an ingredient's price_history and update price_per_kg.

    Args:
        name: Exact ingredient name (case-insensitive fallback).
        price: Price per kg (used for nutrition/cost math).
        currency: Currency code (default ``USD``).
        store: Optional store/retailer name.
        record_date: ISO date string (``YYYY-MM-DD``). Defaults to today.
        package_price: What you paid for the package (stored for reference).
        net_weight: Package net weight string, e.g. ``"32oz"`` (stored for reference).
        catalog_path: Path to ``ingredients.yaml``.

    Raises:
        ValueError: If the ingredient is not found.
    """
    from datetime import date as _date

    catalog = _load(catalog_path)

    # Exact match first, then case-insensitive fallback
    if name not in catalog:
        for key in catalog:
            if key.lower() == name.lower():
                name = key
                break
        else:
            raise ValueError(f"Ingredient '{name}' not found.")

    entry = catalog[name]
    observation: dict[str, Any] = {
        "date": record_date or _date.today().isoformat(),
        "price_per_kg": price,
    }
    if package_price is not None:
        observation["package_price"] = package_price
    if net_weight is not None:
        observation["net_weight"] = net_weight
    if store:
        observation["store"] = store

    entry.setdefault("price_history", [])
    entry["price_history"].append(observation)
    entry["price_per_kg"] = price
    entry["currency"] = currency
    _save(catalog, catalog_path)
