"""
Runtime generation of tray icons that display the active language code.

The AppIndicator ``set_label`` API is ignored by several panels (notably the
XFCE ``systray`` plugin and GNOME Shell's AppIndicator extension), so the
language badge is rendered into the icon itself instead. Icons are generated
as SVG files in the user's cache directory and referenced by name, which is
what ``Indicator.set_icon_full`` expects.

This module deliberately avoids importing GTK so it stays importable without a
display (see the lazy-GTK-import rule in CLAUDE.md).
"""

import logging
import os
import shutil
from xml.sax.saxutils import escape

logger = logging.getLogger(__name__)

# Background colours per recognition state, matching the existing SVG assets
# in resources/icons/scalable/.
STATE_COLORS = {
    "default": "#e74c3c",
    "active": "#2ecc71",
    "processing": "#f39c12",
}

TEXT_COLOR = "#ffffff"

# The base icons that must be available alongside the generated ones, because
# AppIndicator only accepts a single icon theme path.
BASE_ICON_NAMES = (
    "vocalinux-microphone-off",
    "vocalinux-microphone",
    "vocalinux-microphone-process",
    "vocalinux",
)

_SVG_TEMPLATE = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">
  <circle cx="64" cy="64" r="60" fill="{color}" />
  <text x="64" y="{baseline}" text-anchor="middle" font-family="sans-serif"
        font-weight="bold" font-size="{font_size}" fill="{text_color}">{text}</text>
</svg>
"""


def cache_dir() -> str:
    """Return the directory holding generated tray icons, creating it if needed."""
    base = os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")
    path = os.path.join(base, "vocalinux", "icons")
    os.makedirs(path, exist_ok=True)
    return path


def _font_metrics(text: str) -> tuple[int, int]:
    """Return (font_size, baseline_y) for the badge text.

    ``dominant-baseline`` has patchy support in older librsvg, so the baseline
    is positioned explicitly instead.
    """
    if len(text) <= 1:
        return 72, 89
    return 58, 85


def render_language_icon(text: str, state_key: str) -> str:
    """
    Generate (once) an icon showing ``text`` on the colour for ``state_key``.

    Args:
        text: The language badge, e.g. "CA". Must be non-empty.
        state_key: One of the keys in STATE_COLORS.

    Returns:
        The icon name without extension, suitable for ``set_icon_full``.
    """
    color = STATE_COLORS.get(state_key, STATE_COLORS["default"])
    icon_name = f"vocalinux-lang-{state_key}-{text.lower()}"
    icon_path = os.path.join(cache_dir(), f"{icon_name}.svg")

    if not os.path.exists(icon_path):
        font_size, baseline = _font_metrics(text)
        svg = _SVG_TEMPLATE.format(
            color=color,
            text=escape(text),
            text_color=TEXT_COLOR,
            font_size=font_size,
            baseline=baseline,
        )
        try:
            with open(icon_path, "w", encoding="utf-8") as handle:
                handle.write(svg)
        except OSError as e:
            # An unwritable cache must not take the tray icon down; the caller
            # falls back to the packaged icons when we return "".
            logger.warning(f"Could not generate language icon {icon_name}: {e}")
            return ""
        logger.debug(f"Generated language icon: {icon_path}")

    return icon_name


def ensure_base_icons_cached(icons_dir: str) -> None:
    """
    Copy the packaged base icons into the generated-icon cache.

    AppIndicator only accepts one icon theme path, so both the static and the
    generated icons have to live in the same directory.
    """
    target_dir = cache_dir()
    for name in BASE_ICON_NAMES:
        source = os.path.join(icons_dir, f"{name}.svg")
        if not os.path.exists(source):
            logger.warning(f"Base icon missing, not cached: {source}")
            continue
        destination = os.path.join(target_dir, f"{name}.svg")
        try:
            shutil.copyfile(source, destination)
        except OSError as e:
            logger.warning(f"Could not cache base icon {name}: {e}")
