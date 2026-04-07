import unittest

from hestia.catalog import preserve_existing_fields


class PreserveExistingFieldsTests(unittest.TestCase):
    def test_preserves_existing_g_per_unit(self) -> None:
        existing = {"g_per_unit": 120.0}
        updates = {"calories_per_100g": 57.0, "g_per_unit": 140.0}

        filtered = preserve_existing_fields(existing, updates, {"g_per_unit"})

        self.assertNotIn("g_per_unit", filtered)
        self.assertEqual(filtered["calories_per_100g"], 57.0)

    def test_keeps_g_per_unit_when_missing_on_existing_entry(self) -> None:
        existing = {"calories_per_100g": 57.0}
        updates = {"g_per_unit": 140.0}

        filtered = preserve_existing_fields(existing, updates, {"g_per_unit"})

        self.assertEqual(filtered["g_per_unit"], 140.0)


if __name__ == "__main__":
    unittest.main()
