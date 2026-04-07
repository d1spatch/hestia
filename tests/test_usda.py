import unittest
from unittest.mock import patch

from hestia import usda


class FetchTests(unittest.TestCase):
    @patch("hestia.usda._api_key", return_value="TEST_KEY")
    @patch("hestia.usda._get")
    def test_fetch_maps_racc_to_g_per_unit(self, mock_get, _mock_api_key) -> None:
        mock_get.return_value = {
            "description": "Blueberries, raw",
            "foodNutrients": [],
            "foodPortions": [
                {
                    "measureUnit": {"abbreviation": "racc"},
                    "portionDescription": "RACC",
                    "gramWeight": 140.0,
                    "amount": 1.0,
                }
            ],
        }

        result = usda.fetch(2346411)

        self.assertEqual(result["g_per_unit"], 140.0)
        self.assertNotIn("unit_sizes", result)

    @patch("hestia.usda._api_key", return_value="TEST_KEY")
    @patch("hestia.usda._get")
    def test_fetch_prefers_racc_over_other_generic_units(self, mock_get, _mock_api_key) -> None:
        mock_get.return_value = {
            "description": "Bell peppers, raw",
            "foodNutrients": [],
            "foodPortions": [
                {
                    "measureUnit": {"abbreviation": "unit"},
                    "portionDescription": "1 item",
                    "gramWeight": 119.0,
                    "amount": 1.0,
                },
                {
                    "measureUnit": {"abbreviation": "racc"},
                    "portionDescription": "RACC",
                    "gramWeight": 85.0,
                    "amount": 1.0,
                },
            ],
        }

        result = usda.fetch(2258591)

        self.assertEqual(result["g_per_unit"], 85.0)
        self.assertNotIn("unit_sizes", result)


if __name__ == "__main__":
    unittest.main()
