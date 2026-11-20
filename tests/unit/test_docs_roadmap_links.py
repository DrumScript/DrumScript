"""Ensure Sphinx's roadmap links stay relative to their source pages."""

import re
from pathlib import Path

import pytest

DOCS = Path(__file__).resolve().parents[2] / "docs"


@pytest.mark.parametrize("source_name", ["index.md", "about.md"])
def test_roadmap_links_resolve(source_name: str) -> None:
    """Every roadmap link should point to the actual Sphinx roadmap source."""
    source = DOCS / source_name
    links = re.findall(r"\[roadmap\]\(([^)#]+)(?:#[^)]*)?\)", source.read_text(encoding="utf-8"), re.IGNORECASE)
    assert links, f"{source_name} should link to the roadmap"
    for link in links:
        target = (source.parent / link).resolve()
        assert target == DOCS / "guide" / "roadmap.md", f"{source_name} has incorrect roadmap link {link!r}"
        assert target.is_file(), f"{source_name} has a broken roadmap link {link!r}"
