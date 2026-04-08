import unittest

from hestia.html_notes import notes_to_html


class NotesToHtmlTests(unittest.TestCase):
    def test_markdown_link_becomes_anchor(self) -> None:
        html = notes_to_html(
            "Source: [Serious Eats](https://www.seriouseats.com/papaya-habanero-hot-sauce-recipe)"
        )

        self.assertIn(
            '<a href="https://www.seriouseats.com/papaya-habanero-hot-sauce-recipe"',
            html,
        )
        self.assertIn(">Serious Eats</a>", html)

    def test_bare_url_becomes_anchor(self) -> None:
        html = notes_to_html("Source: https://example.com/recipe.")

        self.assertIn('<a href="https://example.com/recipe"', html)
        self.assertTrue(html.endswith("</a>."))

    def test_non_link_text_is_escaped(self) -> None:
        html = notes_to_html("<b>unsafe</b>")

        self.assertEqual(html, "&lt;b&gt;unsafe&lt;/b&gt;")

    def test_bullet_list_becomes_html_list(self) -> None:
        html = notes_to_html(
            "- First note item\n"
            "- Second note item with [link](https://example.com)"
        )

        self.assertTrue(html.startswith("<ul>"))
        self.assertIn("<li>First note item</li>", html)
        self.assertIn('<a href="https://example.com"', html)
        self.assertTrue(html.endswith("</ul>"))


if __name__ == "__main__":
    unittest.main()
