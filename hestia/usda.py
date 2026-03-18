"""USDA FoodData Central API client.

API key: free from https://fdc.nal.usda.gov/api-key-signup.html
Set via the USDA_API_KEY environment variable.
Falls back to DEMO_KEY (rate-limited to 30 requests/hour).
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any

_BASE = "https://api.nal.usda.gov/fdc/v1"

# FDC nutrient IDs → catalog field names (values per 100g)
_NUTRIENT_MAP: dict[int, str] = {
    1008: "calories_per_100g",       # kcal
    1003: "protein_per_100g",        # g
    1004: "fat_per_100g",            # g
    1005: "carbs_per_100g",          # g
    1079: "fiber_per_100g",          # g
    2000: "sugar_per_100g",          # g
    1093: "sodium_per_100g",         # mg in FDC → stored as g
    1258: "saturated_fat_per_100g",  # g
    1253: "cholesterol_per_100g",    # mg in FDC → stored as g
    # Vitamins & minerals — stored in their natural label units
    1162: "vitamin_c_per_100g",      # mg
    1114: "vitamin_d_per_100g",      # mcg
    1185: "vitamin_k_per_100g",      # mcg
    1087: "calcium_per_100g",        # mg
    1089: "iron_per_100g",           # mg
    1090: "magnesium_per_100g",      # mg
    1092: "potassium_per_100g",      # mg
    1101: "manganese_per_100g",      # mg
}

# FDC reports these in mg; we convert to g for consistency with other fields
_MG_TO_G = {"sodium_per_100g", "cholesterol_per_100g"}

# FDC abbreviation → multiplier to normalise that unit's gramWeight to g-per-tbsp.
_TO_TBSP: dict[str, float] = {
    "tsp": 3.0,        # 1 tbsp = 3 tsp
    "teaspoon": 3.0,
    "tbsp": 1.0,
    "tablespoon": 1.0,
    "cup": 1 / 16,     # 1 cup = 16 tbsp
}

# FDC abbreviation → multiplier to normalise that unit's gramWeight to g-per-mL.
_TO_ML: dict[str, float] = {
    "ml": 1.0,
    "milliliter": 1.0,
    "milliliters": 1.0,
    "fl oz": 1 / 29.5735,   # 1 fl oz = 29.5735 mL
    "floz": 1 / 29.5735,
}


def _load_dotenv() -> None:
    """Load .env from the project root (hestia/) if it exists."""
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        return
    with env_path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())


def _api_key() -> str:
    _load_dotenv()
    key = os.environ.get("USDA_API_KEY", "DEMO_KEY")
    print(f"Using USDA API key: {key[:4]}{'*' * (len(key) - 4)}")
    return os.environ.get("USDA_API_KEY", "DEMO_KEY")


def _get(url: str) -> Any:
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"USDA API error {e.code}: {e.reason}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error: {e.reason}") from e


def search(query: str, page_size: int = 10) -> list[dict[str, Any]]:
    """Search FoodData Central for foods matching *query*.

    Returns a list of dicts with keys: fdc_id, description, data_type, brand_owner.
    Prefers Foundation and SR Legacy data types (most complete nutrient profiles).
    """
    params = urllib.parse.urlencode([
        ("query", query),
        ("pageSize", page_size),
        ("dataType", "Foundation"),
        ("dataType", "SR Legacy"),
        ("dataType", "Survey (FNDDS)"),
        ("api_key", _api_key()),
    ])
    data = _get(f"{_BASE}/foods/search?{params}")
    return [
        {
            "fdc_id": f["fdcId"],
            "description": f.get("description", ""),
            "data_type": f.get("dataType", ""),
            "brand_owner": f.get("brandOwner", ""),
        }
        for f in data.get("foods", [])
    ]


def fetch(fdc_id: int) -> dict[str, Any]:
    """Fetch full nutrition data for a food by FDC ID.

    Returns a partial catalog entry dict (nutrition fields + source block)
    ready to be merged into an ingredient entry via add_ingredient or update_ingredient.

    Nutrient values are per 100g. Sodium and cholesterol are converted from mg to g.
    """
    params = urllib.parse.urlencode({"api_key": _api_key()})
    data = _get(f"{_BASE}/food/{fdc_id}?{params}")

    nutrition: dict[str, Any] = {}
    for nutrient in data.get("foodNutrients", []):
        # Foundation/SR Legacy: nested nutrient.nutrient.id
        # Branded foods: flat nutrient.nutrientId
        nid = (
            nutrient.get("nutrient", {}).get("id")
            or nutrient.get("nutrientId")
        )
        # Foundation uses "amount"; branded/survey may use "value"
        value = nutrient.get("amount") if "amount" in nutrient else nutrient.get("value")
        if nid in _NUTRIENT_MAP and value is not None:
            field = _NUTRIENT_MAP[nid]
            fval = float(value)
            if field in _MG_TO_G:
                fval = fval / 1000.0
            nutrition[field] = round(fval, 4)

    # Parse foodPortions → store only g-per-tbsp (tsp/cup are derived by fixed ratios).
    # Prefer tbsp directly; fall back to tsp or cup if tbsp isn't listed.
    g_per_tbsp: float | None = None
    for unit_pref in ("tbsp", "tablespoon", "tsp", "teaspoon", "cup"):
        for portion in data.get("foodPortions", []):
            abbr = portion.get("measureUnit", {}).get("abbreviation", "").lower().strip()
            gram_weight = portion.get("gramWeight")
            if abbr == unit_pref and gram_weight is not None:
                amount = float(portion.get("amount") or 1.0)
                if amount > 0:
                    g_per_tbsp = round(float(gram_weight) / amount * _TO_TBSP[abbr], 4)
                    break
        if g_per_tbsp is not None:
            break
    if g_per_tbsp is not None:
        nutrition["g_per_tbsp"] = g_per_tbsp

    # Parse foodPortions for mL density (g per mL).
    # Prefer mL directly; fall back to fl oz.
    g_per_ml: float | None = None
    for unit_pref in ("ml", "milliliter", "milliliters", "fl oz", "floz"):
        for portion in data.get("foodPortions", []):
            abbr = portion.get("measureUnit", {}).get("abbreviation", "").lower().strip()
            gram_weight = portion.get("gramWeight")
            if abbr == unit_pref and gram_weight is not None:
                amount = float(portion.get("amount") or 1.0)
                if amount > 0:
                    g_per_ml = round(float(gram_weight) / amount * _TO_ML[abbr], 4)
                    break
        if g_per_ml is not None:
            break
    if g_per_ml is not None:
        nutrition["g_per_ml"] = g_per_ml

    nutrition["source"] = {
        "type": "usda",
        "fdc_id": fdc_id,
        "description": data.get("description", ""),
        "retrieved": date.today().isoformat(),
    }
    return nutrition
