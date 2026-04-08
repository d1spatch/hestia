"""Helpers for rendering recipe notes into safe HTML."""

from __future__ import annotations

import html
import re

_LINK_RE = re.compile(
    r"\[([^\]]+)\]\((https?://[^\s)]+)\)|(https?://[^\s<]+)",
    re.IGNORECASE,
)
_LIST_ITEM_RE = re.compile(
    r"^\s*(?:(?P<ul>[-*+])|(?P<ol>\d+[.)]))\s+(?P<content>.+?)\s*$"
)


def _render_inline_html(text: str) -> str:
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


def notes_to_html(text: str) -> str:
    """Render recipe note text with safe hyperlinks and lightweight lists.

    Supports Markdown-style links like ``[label](https://example.com)``,
    bare ``http://`` / ``https://`` URLs, and simple bullet/numbered lists.
    All non-link text is HTML-escaped.
    """
    if not text:
        return ""

    if "\n" not in text and _LIST_ITEM_RE.match(text) is None:
        return _render_inline_html(text)

    blocks: list[str] = []
    paragraph_lines: list[str] = []
    list_items: list[str] = []
    list_kind: str | None = None

    def flush_paragraph() -> None:
        if not paragraph_lines:
            return
        content = "<br>\n".join(_render_inline_html(line) for line in paragraph_lines)
        blocks.append(f"<p>{content}</p>")
        paragraph_lines.clear()

    def flush_list() -> None:
        nonlocal list_kind
        if not list_items:
            list_kind = None
            return
        tag = "ol" if list_kind == "ol" else "ul"
        items_html = "".join(f"<li>{_render_inline_html(item)}</li>" for item in list_items)
        blocks.append(f"<{tag}>{items_html}</{tag}>")
        list_items.clear()
        list_kind = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        list_match = _LIST_ITEM_RE.match(line)

        if not stripped:
            flush_paragraph()
            flush_list()
            continue

        if list_match is not None:
            flush_paragraph()
            next_list_kind = "ol" if list_match.group("ol") else "ul"
            if list_kind is not None and list_kind != next_list_kind:
                flush_list()
            list_kind = next_list_kind
            list_items.append(list_match.group("content"))
            continue

        if list_kind is not None and (raw_line.startswith("  ") or raw_line.startswith("\t")) and list_items:
            list_items[-1] = f"{list_items[-1]} {stripped}"
            continue

        flush_list()
        paragraph_lines.append(stripped)

    flush_paragraph()
    flush_list()
    return "".join(blocks) if blocks else _render_inline_html(text)
