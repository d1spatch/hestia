"""SQLite-backed ingredient catalog."""

from __future__ import annotations

import csv
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Default DB location alongside the package's data/ directory.
_DEFAULT_DB = Path(__file__).parent.parent / "data" / "ingredients.db"


def _conn(db_path: Path = _DEFAULT_DB) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    return con


def init_db(db_path: Path = _DEFAULT_DB) -> None:
    """Initialise the database, creating tables if they don't exist.

    Safe to call multiple times — uses `CREATE TABLE IF NOT EXISTS`.

    Args:
        db_path: Path to the SQLite database file. Created automatically if absent.
    """
    with _conn(db_path) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS ingredients (
                id               INTEGER PRIMARY KEY,
                name             TEXT    UNIQUE NOT NULL,
                aliases          TEXT    DEFAULT '[]',
                price_per_kg     REAL,
                currency         TEXT    DEFAULT 'USD',
                calories_per_100g REAL,
                protein_per_100g  REAL,
                carbs_per_100g    REAL,
                fat_per_100g      REAL,
                category         TEXT,
                notes            TEXT,
                updated_at       TEXT
            )
        """)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def add_ingredient(data: dict[str, Any], db_path: Path = _DEFAULT_DB) -> None:
    """Insert a new ingredient into the catalog.

    Args:
        data: Dict of field names to values. `name` is required and must be unique.
            `aliases` may be provided as a Python list — it is serialised to JSON automatically.
        db_path: Path to the SQLite database file.

    Raises:
        ValueError: If an ingredient with the same name already exists.
    """
    init_db(db_path)
    data = {**data, "updated_at": _now()}
    if "aliases" in data and isinstance(data["aliases"], list):
        data["aliases"] = json.dumps(data["aliases"])
    cols = ", ".join(data.keys())
    placeholders = ", ".join("?" for _ in data)
    with _conn(db_path) as con:
        try:
            con.execute(
                f"INSERT INTO ingredients ({cols}) VALUES ({placeholders})",
                list(data.values()),
            )
        except sqlite3.IntegrityError:
            raise ValueError(f"Ingredient '{data['name']}' already exists. Use update instead.")


def update_ingredient(name: str, updates: dict[str, Any], db_path: Path = _DEFAULT_DB) -> None:
    """Update one or more fields on an existing ingredient.

    Args:
        name: Exact canonical name of the ingredient to update.
        updates: Dict of field names to new values. Only the provided fields are changed.
        db_path: Path to the SQLite database file.

    Raises:
        ValueError: If no ingredient with the given name exists.
    """
    init_db(db_path)
    updates = {**updates, "updated_at": _now()}
    if "aliases" in updates and isinstance(updates["aliases"], list):
        updates["aliases"] = json.dumps(updates["aliases"])
    assignments = ", ".join(f"{k} = ?" for k in updates)
    with _conn(db_path) as con:
        cur = con.execute(
            f"UPDATE ingredients SET {assignments} WHERE name = ?",
            [*updates.values(), name],
        )
        if cur.rowcount == 0:
            raise ValueError(f"Ingredient '{name}' not found.")


def get_ingredient(name: str, db_path: Path = _DEFAULT_DB) -> dict[str, Any] | None:
    """Fetch one ingredient by exact name or alias.

    Lookup order:
    1. Exact case-insensitive name match.
    2. Case-insensitive match against any stored alias.

    Args:
        name: Ingredient name or alias to search for.
        db_path: Path to the SQLite database file.

    Returns:
        A dict of all catalog fields, or `None` if not found.
        The `aliases` field is returned as a Python list.
    """
    init_db(db_path)
    with _conn(db_path) as con:
        row = con.execute(
            "SELECT * FROM ingredients WHERE name = ?", (name,)
        ).fetchone()
        if row:
            return _row_to_dict(row)
        # Try aliases
        rows = con.execute("SELECT * FROM ingredients WHERE aliases != '[]'").fetchall()
        for r in rows:
            aliases = json.loads(r["aliases"] or "[]")
            if name.lower() in [a.lower() for a in aliases]:
                return _row_to_dict(r)
    return None


def list_ingredients(
    category: str | None = None,
    db_path: Path = _DEFAULT_DB,
) -> list[dict[str, Any]]:
    """Return all ingredients, sorted by name.

    Args:
        category: If provided, only return ingredients matching this category label.
        db_path: Path to the SQLite database file.

    Returns:
        List of ingredient dicts, each with `aliases` as a Python list.
    """
    init_db(db_path)
    with _conn(db_path) as con:
        if category:
            rows = con.execute(
                "SELECT * FROM ingredients WHERE category = ? ORDER BY name",
                (category,),
            ).fetchall()
        else:
            rows = con.execute("SELECT * FROM ingredients ORDER BY name").fetchall()
    return [_row_to_dict(r) for r in rows]


def import_csv(path: Path, db_path: Path = _DEFAULT_DB) -> tuple[int, int]:
    """Bulk-import ingredients from a CSV file.

    The CSV must have a header row. The `name` column is required; all other
    columns are optional and match the catalog field names exactly.

    Expected columns:
        `name`, `aliases`, `price_per_kg`, `currency`, `calories_per_100g`,
        `protein_per_100g`, `carbs_per_100g`, `fat_per_100g`, `category`, `notes`

    Rows with a missing name, or whose name already exists in the catalog, are
    skipped without raising an error.

    Args:
        path: Path to the CSV file.
        db_path: Path to the SQLite database file.

    Returns:
        A `(inserted, skipped)` tuple of row counts.
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
                add_ingredient(row, db_path)
                inserted += 1
            except ValueError:
                skipped += 1
    return inserted, skipped


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    d["aliases"] = json.loads(d.get("aliases") or "[]")
    return d
