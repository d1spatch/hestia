"""Jinja2-based rendering to LaTeX + HTML, with optional PDF compilation."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .recipe import Recipe

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_OUTPUT_DIR = Path(__file__).parent.parent / "output"


def _env(escape_latex: bool = False) -> Environment:
    if escape_latex:
        # Use different delimiters so they don't conflict with LaTeX braces
        return Environment(
            loader=FileSystemLoader(str(_TEMPLATES_DIR)),
            block_start_string=r"\BLOCK{",
            block_end_string="}",
            variable_start_string=r"\VAR{",
            variable_end_string="}",
            comment_start_string=r"\#{",
            comment_end_string="}",
            trim_blocks=True,
            autoescape=False,
        )
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
    )


def _latex_escape(text: str) -> str:
    """Escape special LaTeX characters in plain text."""
    replacements = [
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ]
    for orig, repl in replacements:
        text = text.replace(orig, repl)
    return text


def render_html(
    recipe: Recipe,
    nutrition: dict[str, Any],
    output_dir: Path = _OUTPUT_DIR,
) -> Path:
    """Render a recipe to a self-contained HTML file.

    Uses `hestia/templates/recipe.html.j2`. All CSS is embedded inline —
    no external resources required.

    Args:
        recipe: A validated `Recipe` instance.
        nutrition: Nutrition/cost dict from `recipe.compute_nutrition`.
        output_dir: Directory to write the output file. Created if absent.

    Returns:
        Path to the generated `.html` file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    env = _env(escape_latex=False)
    template = env.get_template("recipe.html.j2")
    html = template.render(recipe=recipe, nutrition=nutrition)
    out = output_dir / f"{recipe.slug}.html"
    out.write_text(html, encoding="utf-8")
    return out


def render_latex(
    recipe: Recipe,
    nutrition: dict[str, Any],
    output_dir: Path = _OUTPUT_DIR,
) -> Path:
    """Render a recipe to a LaTeX `.tex` source file.

    Uses `hestia/templates/recipe.tex.j2`. The template uses alternative
    Jinja2 delimiters (`\\VAR{...}`, `\\BLOCK{...}`) to avoid conflicts with
    LaTeX syntax. All text variables are passed through the `| latex` filter
    to escape special characters.

    Args:
        recipe: A validated `Recipe` instance.
        nutrition: Nutrition/cost dict from `recipe.compute_nutrition`.
        output_dir: Directory to write the output file. Created if absent.

    Returns:
        Path to the generated `.tex` file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    env = _env(escape_latex=True)
    env.filters["latex"] = _latex_escape
    template = env.get_template("recipe.tex.j2")
    tex = template.render(recipe=recipe, nutrition=nutrition)
    out = output_dir / f"{recipe.slug}.tex"
    out.write_text(tex, encoding="utf-8")
    return out


def compile_pdf(tex_path: Path, output_dir: Path = _OUTPUT_DIR) -> Path:
    """Compile a `.tex` file to PDF using `pdflatex`.

    Runs `pdflatex` in a temporary directory (so auxiliary files don't clutter
    the output folder) and copies the resulting PDF to `output_dir`.

    Args:
        tex_path: Path to the `.tex` source file.
        output_dir: Directory to write the final `.pdf`. Created if absent.

    Returns:
        Path to the generated `.pdf` file.

    Raises:
        RuntimeError: If `pdflatex` is not found on PATH, or if compilation fails.
            The error message includes the full pdflatex stdout/stderr for diagnosis.
    """
    if shutil.which("pdflatex") is None:
        raise RuntimeError(
            "pdflatex not found on PATH. "
            "Install MiKTeX (https://miktex.org) and ensure it is on your PATH."
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            [
                "pdflatex",
                "-interaction=nonstopmode",
                "-output-directory", tmpdir,
                str(tex_path.resolve()),
            ],
            capture_output=True,
            text=True,
        )
        tmp_pdf = Path(tmpdir) / tex_path.with_suffix(".pdf").name
        if not tmp_pdf.exists():
            raise RuntimeError(
                f"pdflatex failed.\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            )
        out_pdf = output_dir / tmp_pdf.name
        shutil.copy(tmp_pdf, out_pdf)

    return out_pdf
