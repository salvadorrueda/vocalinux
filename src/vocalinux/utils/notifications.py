"""Desktop notification helper for Vocalinux."""

import logging
import subprocess

logger = logging.getLogger(__name__)


def show_notification(title: str, message: str, icon: str = "dialog-information") -> None:
    """Show a desktop notification via notify-send."""
    try:
        subprocess.Popen(
            ["notify-send", "-i", icon, "-a", "Vocalinux", title, message],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, OSError) as e:
        logger.debug(f"Could not show notification: {e}")
