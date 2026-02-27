# db.py

SQLite-backed ingredient catalog. All functions accept an optional `db_path` argument; omit it to use the default location (`data/ingredients.db`).

---

## Setup

::: hestia.db.init_db

---

## CRUD

::: hestia.db.add_ingredient

::: hestia.db.get_ingredient

::: hestia.db.update_ingredient

::: hestia.db.list_ingredients

---

## Bulk import

::: hestia.db.import_csv
