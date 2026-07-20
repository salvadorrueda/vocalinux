"""
Tests for runtime generation of language-badge tray icons.

These are pure filesystem/string tests: language_icon.py deliberately has no
GTK dependency, so no mocking of gi is required here.
"""

import os

import pytest

from vocalinux.ui.language_icon import (
    BASE_ICON_NAMES,
    STATE_COLORS,
    cache_dir,
    ensure_base_icons_cached,
    render_language_icon,
)


def test_cache_dir_honours_xdg_and_is_created(tmp_path, monkeypatch):
    """The cache directory follows XDG_CACHE_HOME and exists after the call."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))

    path = cache_dir()

    assert path == str(tmp_path / "vocalinux" / "icons")
    assert os.path.isdir(path)


def test_render_writes_svg_with_text_and_state_colour(tmp_path, monkeypatch):
    """The generated SVG carries the badge text and the state's colour."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))

    name = render_language_icon("CA", "active")

    assert name == "vocalinux-lang-active-ca"
    assert not name.endswith(".svg")  # set_icon_full expects a bare name

    with open(os.path.join(cache_dir(), f"{name}.svg"), encoding="utf-8") as handle:
        svg = handle.read()
    assert ">CA<" in svg
    assert STATE_COLORS["active"] in svg


@pytest.mark.parametrize(
    "state_key",
    ["default", "active", "processing"],
)
def test_render_uses_distinct_colour_per_state(state_key, tmp_path, monkeypatch):
    """Each recognition state renders with its own background colour."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))

    name = render_language_icon("EN", state_key)

    with open(os.path.join(cache_dir(), f"{name}.svg"), encoding="utf-8") as handle:
        assert STATE_COLORS[state_key] in handle.read()


def test_render_is_idempotent_and_does_not_rewrite(tmp_path, monkeypatch):
    """A second call returns the same name without touching the file."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))

    first = render_language_icon("ES", "default")
    icon_path = os.path.join(cache_dir(), f"{first}.svg")
    os.utime(icon_path, (0, 0))

    second = render_language_icon("ES", "default")

    assert second == first
    assert os.stat(icon_path).st_mtime == 0


def test_render_scales_font_for_single_character(tmp_path, monkeypatch):
    """One-character badges use a larger font than two-character ones."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))

    def font_size_of(text):
        name = render_language_icon(text, "default")
        with open(os.path.join(cache_dir(), f"{name}.svg"), encoding="utf-8") as handle:
            svg = handle.read()
        return int(svg.split('font-size="')[1].split('"')[0])

    assert font_size_of("X") > font_size_of("XX")


def test_render_escapes_text(tmp_path, monkeypatch):
    """Text is XML-escaped rather than injected raw into the SVG."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))

    name = render_language_icon("A&B", "default")

    with open(os.path.join(cache_dir(), f"{name}.svg"), encoding="utf-8") as handle:
        assert "A&amp;B" in handle.read()


def test_ensure_base_icons_cached_copies_all_icons(tmp_path, monkeypatch):
    """Base icons are copied into the cache so one theme path serves both."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    for name in BASE_ICON_NAMES:
        (source_dir / f"{name}.svg").write_text(f"<svg>{name}</svg>")

    ensure_base_icons_cached(str(source_dir))

    for name in BASE_ICON_NAMES:
        assert os.path.exists(os.path.join(cache_dir(), f"{name}.svg"))


def test_ensure_base_icons_cached_tolerates_missing_source(tmp_path, monkeypatch):
    """A missing base icon is warned about, not fatal."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    source_dir = tmp_path / "empty"
    source_dir.mkdir()

    ensure_base_icons_cached(str(source_dir))  # Should not raise

    assert os.listdir(cache_dir()) == []
