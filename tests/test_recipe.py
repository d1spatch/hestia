import unittest

from hestia.recipe import to_grams


class ToGramsTests(unittest.TestCase):
    def test_pinch_converts_to_two_grams(self) -> None:
        self.assertEqual(to_grams(1, "pinch"), 2.0)

    def test_pinches_scale_linearly(self) -> None:
        self.assertEqual(to_grams(3, "pinches"), 6.0)


if __name__ == "__main__":
    unittest.main()
