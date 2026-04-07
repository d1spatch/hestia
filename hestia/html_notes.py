"""Helpers for rendering recipe notes into safe HTML."""

from __future__ import annotations

import html
import re

_LINK_RE = re.compile(
    r"\[([^\]]+)\]\((https?://[^\s)]+)\)|(https?://[^\s<]+)",
    re.IGNORECASE,
)


def notes_to_html(text: str) -> str:
    """Render recipe note text with safe hyperlinks.

    Supports Markdown-style links like ``[label](https://example.com)`` and
    bare ``http://`` / ``https://`` URLs. All non-link text is HTML-escaped.
    """
    if not text:
        return ""

    parts: list[str] = []
    last_end = 0

    for match in _LINK_RE.finditer(text):
        parts.append(html.escape(text[last_end:match.start()]))

        if match.group(1) is not None:
            label = html.escape(match.group(1))
            url = html.escape(match.group(2), quote=True)
        else:
            raw_url = match.group(3)
            trailing = raw_url.rstrip(".,;:")
            suffix = raw_url[len(trailing):]
            url = html.escape(trailing, quote=True)
            label = html.escape(trailing)
            parts.append(
                f'<a href="{url}" target="_blank" rel="noopener noreferrer">{label}</a>'
            )
            parts.append(html.escape(suffix))
            last_end = match.end()
            continue

        parts.append(
            f'<a href="{url}" target="_blank" rel="noopener noreferrer">{label}</a>'
        )
        last_end = match.end()

    parts.append(html.escape(text[last_end:]))
    return "".join(parts)
