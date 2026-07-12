"""
Base class for keyboard backends.

All keyboard backends must inherit from this class and implement
the required methods.
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional

Callback = Callable[[], None]

# Supported double-tap shortcut keys
# Maps shortcut string -> modifier key name used by backends
# "ctrl" means either side; "left_ctrl"/"right_ctrl" means specific side
SUPPORTED_SHORTCUTS = {
    # Either side (backward-compatible)
    "ctrl+ctrl": "ctrl",
    "alt+alt": "alt",
    "shift+shift": "shift",
    # Left side only
    "left_ctrl+left_ctrl": "left_ctrl",
    "left_alt+left_alt": "left_alt",
    "left_shift+left_shift": "left_shift",
    # Right side only
    "right_ctrl+right_ctrl": "right_ctrl",
    "right_alt+right_alt": "right_alt",
    "right_shift+right_shift": "right_shift",
}

# Human-readable names for shortcuts (mode-agnostic base names)
SHORTCUT_DISPLAY_NAMES = {
    "ctrl+ctrl": "Ctrl (either side)",
    "alt+alt": "Alt (either side)",
    "shift+shift": "Shift (either side)",
    "left_ctrl+left_ctrl": "Left Ctrl",
    "left_alt+left_alt": "Left Alt",
    "left_shift+left_shift": "Left Shift",
    "right_ctrl+right_ctrl": "Right Ctrl",
    "right_alt+right_alt": "Right Alt",
    "right_shift+right_shift": "Right Shift",
}

# Grouping for UI display: maps group label -> list of shortcut IDs
SHORTCUT_GROUPS = {
    "Either Side": ["ctrl+ctrl", "alt+alt", "shift+shift"],
    "Left Side": ["left_ctrl+left_ctrl", "left_alt+left_alt", "left_shift+left_shift"],
    "Right Side": ["right_ctrl+right_ctrl", "right_alt+right_alt", "right_shift+right_shift"],
}

# Mode-specific display names (format: {shortcut: {mode: display_name}})
SHORTCUT_MODE_DISPLAY_NAMES = {
    "ctrl+ctrl": {
        "toggle": "Double-tap Ctrl",
        "push_to_talk": "Hold Ctrl",
    },
    "alt+alt": {
        "toggle": "Double-tap Alt",
        "push_to_talk": "Hold Alt",
    },
    "shift+shift": {
        "toggle": "Double-tap Shift",
        "push_to_talk": "Hold Shift",
    },
    "left_ctrl+left_ctrl": {
        "toggle": "Double-tap Left Ctrl",
        "push_to_talk": "Hold Left Ctrl",
    },
    "left_alt+left_alt": {
        "toggle": "Double-tap Left Alt",
        "push_to_talk": "Hold Left Alt",
    },
    "left_shift+left_shift": {
        "toggle": "Double-tap Left Shift",
        "push_to_talk": "Hold Left Shift",
    },
    "right_ctrl+right_ctrl": {
        "toggle": "Double-tap Right Ctrl",
        "push_to_talk": "Hold Right Ctrl",
    },
    "right_alt+right_alt": {
        "toggle": "Double-tap Right Alt",
        "push_to_talk": "Hold Right Alt",
    },
    "right_shift+right_shift": {
        "toggle": "Double-tap Right Shift",
        "push_to_talk": "Hold Right Shift",
    },
}

DEFAULT_SHORTCUT = "ctrl+ctrl"

# Physical keys watched by each modifier name. "ctrl" (either side) overlaps
# with "left_ctrl"/"right_ctrl", so shortcuts sharing any physical key conflict.
MODIFIER_PHYSICAL_KEYS = {
    "ctrl": frozenset({"left_ctrl", "right_ctrl"}),
    "alt": frozenset({"left_alt", "right_alt"}),
    "shift": frozenset({"left_shift", "right_shift"}),
    "super": frozenset({"left_super", "right_super"}),
    "left_ctrl": frozenset({"left_ctrl"}),
    "left_alt": frozenset({"left_alt"}),
    "left_shift": frozenset({"left_shift"}),
    "right_ctrl": frozenset({"right_ctrl"}),
    "right_alt": frozenset({"right_alt"}),
    "right_shift": frozenset({"right_shift"}),
}

# Supported shortcut modes
SHORTCUT_MODES = {
    "toggle": "Toggle (double-tap to start/stop)",
    "push_to_talk": "Push-to-Talk (hold to speak)",
}

DEFAULT_SHORTCUT_MODE = "toggle"


def get_shortcut_display_name(shortcut: str, mode: Optional[str] = None) -> str:
    """
    Get a human-readable display name for a shortcut.

    Args:
        shortcut: The shortcut string (e.g., "ctrl+ctrl")
        mode: Optional mode string. If provided, returns mode-specific name.

    Returns:
        A human-readable display name for the shortcut
    """
    if mode and shortcut in SHORTCUT_MODE_DISPLAY_NAMES:
        return SHORTCUT_MODE_DISPLAY_NAMES[shortcut].get(
            mode, SHORTCUT_DISPLAY_NAMES.get(shortcut, shortcut)
        )
    return SHORTCUT_DISPLAY_NAMES.get(shortcut, shortcut)


def parse_shortcut(shortcut_string: str) -> str:
    """
    Parse a shortcut string and return the modifier key name.

    Args:
        shortcut_string: The shortcut string (e.g., "ctrl+ctrl", "alt+alt")

    Returns:
        The modifier key name (e.g., "ctrl", "alt")

    Raises:
        ValueError: If the shortcut string is not recognized
    """
    shortcut_lower = shortcut_string.lower().strip()
    if shortcut_lower not in SUPPORTED_SHORTCUTS:
        raise ValueError(
            f"Unsupported shortcut: {shortcut_string}. "
            f"Supported shortcuts: {', '.join(SUPPORTED_SHORTCUTS.keys())}"
        )
    return SUPPORTED_SHORTCUTS[shortcut_lower]


def shortcuts_conflict(shortcut_a: str, shortcut_b: str) -> bool:
    """
    Check whether two shortcuts watch overlapping physical keys.

    "ctrl+ctrl" (either side) conflicts with "left_ctrl+left_ctrl" because
    both react to the left Ctrl key.

    Args:
        shortcut_a: First shortcut string (e.g., "ctrl+ctrl")
        shortcut_b: Second shortcut string (e.g., "left_ctrl+left_ctrl")

    Returns:
        True if the shortcuts share at least one physical key

    Raises:
        ValueError: If either shortcut string is not recognized
    """
    keys_a = MODIFIER_PHYSICAL_KEYS.get(parse_shortcut(shortcut_a), frozenset())
    keys_b = MODIFIER_PHYSICAL_KEYS.get(parse_shortcut(shortcut_b), frozenset())
    return bool(keys_a & keys_b)


class KeyboardBackend(ABC):
    """
    Abstract base class for keyboard backends.

    Each backend must implement methods for starting/stopping keyboard
    event listening and registering callbacks for specific shortcuts.
    """

    def __init__(self, shortcut: str = DEFAULT_SHORTCUT, mode: str = DEFAULT_SHORTCUT_MODE):
        """
        Initialize the keyboard backend.

        Args:
            shortcut: The shortcut string to listen for (e.g., "ctrl+ctrl")
            mode: The shortcut mode ("toggle" or "push_to_talk")
        """
        self.active = False
        self.double_tap_callback: Optional[Callback] = None
        self.key_press_callback: Optional[Callback] = None
        self.key_release_callback: Optional[Callback] = None
        self._shortcut = shortcut
        self._mode = mode
        self._modifier_key = parse_shortcut(shortcut)
        # Additional named double-tap bindings, independent from the primary
        # shortcut/mode: name -> (shortcut, modifier_key, callback)
        self._extra_bindings: dict = {}

    @property
    def shortcut(self) -> str:
        """Get the current shortcut string."""
        return self._shortcut

    @property
    def mode(self) -> str:
        """Get the current shortcut mode."""
        return self._mode

    def set_mode(self, mode: str) -> None:
        """
        Update the shortcut mode.

        Args:
            mode: The new mode ("toggle" or "push_to_talk")
        """
        if mode not in SHORTCUT_MODES:
            raise ValueError(f"Invalid mode: {mode}. Must be one of {list(SHORTCUT_MODES.keys())}")
        self._mode = mode

    @property
    def modifier_key(self) -> str:
        """Get the modifier key being watched for double-tap."""
        return self._modifier_key

    def set_shortcut(self, shortcut: str) -> None:
        """
        Update the shortcut to listen for.

        Args:
            shortcut: The new shortcut string (e.g., "ctrl+ctrl", "alt+alt")
        """
        self._modifier_key = parse_shortcut(shortcut)
        self._shortcut = shortcut

    @abstractmethod
    def start(self) -> bool:
        """
        Start listening for keyboard events.

        Returns:
            True if the backend started successfully, False otherwise
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop listening for keyboard events."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this backend is available on the current system.

        Returns:
            True if the backend can be used, False otherwise
        """
        pass

    @abstractmethod
    def get_permission_hint(self) -> Optional[str]:
        """
        Get a hint message if permissions are missing.

        Returns:
            A string explaining how to fix permissions, or None if permissions are OK
        """
        pass

    def register_toggle_callback(self, callback: Optional[Callback]) -> None:
        """
        Register a callback for the double-tap shortcut.

        Args:
            callback: Function to call when double-tap is detected
        """
        self.double_tap_callback = callback

    def register_press_callback(self, callback: Optional[Callback]) -> None:
        """
        Register a callback for key press events (push-to-talk mode).

        Args:
            callback: Function to call when the shortcut key is pressed
        """
        self.key_press_callback = callback

    def register_release_callback(self, callback: Optional[Callback]) -> None:
        """
        Register a callback for key release events (push-to-talk mode).

        Args:
            callback: Function to call when the shortcut key is released
        """
        self.key_release_callback = callback

    def register_extra_shortcut(self, name: str, shortcut: str, callback: Callback) -> None:
        """
        Register an additional named double-tap binding.

        Extra bindings always trigger on double-tap, regardless of the
        primary shortcut's mode.

        Args:
            name: Unique name identifying the binding (e.g., "cycle_language")
            shortcut: The shortcut string to listen for (e.g., "alt+alt")
            callback: Function to call when the double-tap is detected

        Raises:
            ValueError: If the shortcut string is not recognized
        """
        modifier_key = parse_shortcut(shortcut)
        self._extra_bindings[name] = (shortcut, modifier_key, callback)

    def unregister_extra_shortcut(self, name: str) -> None:
        """Remove a named extra binding; no-op if it doesn't exist."""
        self._extra_bindings.pop(name, None)

    def set_extra_shortcut(self, name: str, shortcut: str) -> None:
        """
        Update the shortcut of an existing extra binding.

        Args:
            name: The binding name
            shortcut: The new shortcut string

        Raises:
            KeyError: If no binding with that name exists
            ValueError: If the shortcut string is not recognized
        """
        _, _, callback = self._extra_bindings[name]
        modifier_key = parse_shortcut(shortcut)
        self._extra_bindings[name] = (shortcut, modifier_key, callback)

    def iter_extra_bindings(self):
        """Yield (name, shortcut, modifier_key, callback) for each extra binding."""
        for name, (shortcut, modifier_key, callback) in list(self._extra_bindings.items()):
            yield name, shortcut, modifier_key, callback
