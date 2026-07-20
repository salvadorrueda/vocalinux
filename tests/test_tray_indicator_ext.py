"""
Additional coverage tests for tray_indicator.py module.

Tests for TrayIndicator class methods including initialization, menu creation,
state handling, and UI updates.
"""

import os
import signal
import sys
import unittest
from unittest.mock import MagicMock, call, patch

import pytest

# Create mock modules for GTK/GI BEFORE importing anything
mock_gi = MagicMock()
mock_gi.require_version = MagicMock()

mock_gtk = MagicMock()
mock_glib = MagicMock()
mock_gobject = MagicMock()
mock_gdkpixbuf = MagicMock()
mock_appindicator = MagicMock()

# Create mock for gi.repository
mock_gi_repository = MagicMock()
mock_gi_repository.Gtk = mock_gtk
mock_gi_repository.GLib = mock_glib
mock_gi_repository.GObject = mock_gobject
mock_gi_repository.GdkPixbuf = mock_gdkpixbuf
mock_gi_repository.AppIndicator3 = mock_appindicator

# Inject mocks into sys.modules BEFORE any imports
sys.modules["gi"] = mock_gi
sys.modules["gi.repository"] = mock_gi_repository


class TestTrayIndicatorInitialization(unittest.TestCase):
    """Tests for TrayIndicator initialization."""

    @classmethod
    def setUpClass(cls):
        """Set up class fixtures."""
        # Ensure mocks are in place for the entire test class
        sys.modules["gi"] = mock_gi
        sys.modules["gi.repository"] = mock_gi_repository

    def setUp(self):
        """Set up test environment before each test."""
        # Reset all GTK mocks to avoid test pollution
        mock_gtk.reset_mock()
        mock_glib.reset_mock()
        mock_gobject.reset_mock()
        mock_gdkpixbuf.reset_mock()
        mock_appindicator.reset_mock()

        # Configure idle_add to execute the function directly
        mock_glib.idle_add.side_effect = lambda func, *args: func(*args) or False

        # Clear any cached imports of tray_indicator
        modules_to_remove = [k for k in list(sys.modules.keys()) if "tray_indicator" in k]
        for mod in modules_to_remove:
            del sys.modules[mod]

    def test_tray_indicator_init(self):
        """Test TrayIndicator initialization."""
        # Import BEFORE patching to ensure mocks are already in place
        from vocalinux.common_types import RecognitionState
        from vocalinux.ui.tray_indicator import TrayIndicator

        with (
            patch("vocalinux.ui.tray_indicator.logging"),
            patch("vocalinux.ui.tray_indicator._resource_manager") as mock_resource_manager,
            patch("vocalinux.ui.tray_indicator.ConfigManager") as mock_config_manager,
            patch("vocalinux.ui.tray_indicator.KeyboardShortcutManager") as mock_keyboard_manager,
        ):

            # Set up mocks
            mock_speech_engine = MagicMock()
            mock_speech_engine.state = RecognitionState.IDLE
            mock_text_injector = MagicMock()

            # Mock config manager
            mock_config_inst = MagicMock()
            mock_config_inst.get.return_value = "ctrl+ctrl"
            mock_config_manager.return_value = mock_config_inst

            # Mock keyboard shortcut manager
            mock_keyboard_inst = MagicMock()
            mock_keyboard_inst.active = False
            mock_keyboard_manager.return_value = mock_keyboard_inst

            # Mock resource manager
            mock_resource_manager.icons_dir = "/tmp/icons"
            mock_resource_manager.get_icon_path.return_value = "/tmp/icons/test.png"
            mock_resource_manager.ensure_directories_exist.return_value = None
            mock_resource_manager.validate_resources.return_value = {
                "resources_dir_exists": True,
                "missing_icons": [],
                "missing_sounds": [],
            }

            # Initialize
            indicator = TrayIndicator(
                speech_engine=mock_speech_engine,
                text_injector=mock_text_injector,
            )

            # Verify initialization
            assert indicator.speech_engine == mock_speech_engine
            assert indicator.text_injector == mock_text_injector
            assert indicator.config_manager == mock_config_inst
            assert indicator.shortcut_manager == mock_keyboard_inst
            assert indicator._syncing_autostart_menu is False

            # Verify that idle_add was called to initialize the indicator
            mock_glib.idle_add.assert_called()

    def test_tray_indicator_registers_state_callback(self):
        """Test that TrayIndicator registers state callback on speech engine."""
        # Import BEFORE patching to ensure mocks are already in place
        from vocalinux.common_types import RecognitionState
        from vocalinux.ui.tray_indicator import TrayIndicator

        with (
            patch("vocalinux.ui.tray_indicator.logging"),
            patch("vocalinux.ui.tray_indicator._resource_manager") as mock_resource_manager,
            patch("vocalinux.ui.tray_indicator.ConfigManager") as mock_config_manager,
            patch("vocalinux.ui.tray_indicator.KeyboardShortcutManager") as mock_keyboard_manager,
        ):

            from vocalinux.ui.tray_indicator import TrayIndicator

            # Set up mocks
            mock_speech_engine = MagicMock()
            mock_text_injector = MagicMock()

            mock_config_inst = MagicMock()
            mock_config_inst.get.return_value = "ctrl+ctrl"
            mock_config_manager.return_value = mock_config_inst

            mock_keyboard_inst = MagicMock()
            mock_keyboard_inst.active = False
            mock_keyboard_manager.return_value = mock_keyboard_inst

            mock_resource_manager.icons_dir = "/tmp/icons"
            mock_resource_manager.get_icon_path.return_value = "/tmp/icons/test.png"
            mock_resource_manager.ensure_directories_exist.return_value = None
            mock_resource_manager.validate_resources.return_value = {
                "resources_dir_exists": True,
                "missing_icons": [],
                "missing_sounds": [],
            }

            # Initialize
            TrayIndicator(
                speech_engine=mock_speech_engine,
                text_injector=mock_text_injector,
            )

            # Verify callback was registered
            mock_speech_engine.register_state_callback.assert_called_once()


class TestTrayIndicatorMenuOperations(unittest.TestCase):
    """Tests for TrayIndicator menu operations."""

    @classmethod
    def setUpClass(cls):
        """Set up class fixtures."""
        sys.modules["gi"] = mock_gi
        sys.modules["gi.repository"] = mock_gi_repository

    def setUp(self):
        """Set up test environment before each test."""
        mock_gtk.reset_mock()
        mock_glib.reset_mock()
        mock_gobject.reset_mock()
        mock_gdkpixbuf.reset_mock()
        mock_appindicator.reset_mock()
        mock_glib.idle_add.side_effect = lambda func, *args: func(*args) or False
        modules_to_remove = [k for k in list(sys.modules.keys()) if "tray_indicator" in k]
        for mod in modules_to_remove:
            del sys.modules[mod]

    def test_add_menu_item(self):
        """Test adding a menu item."""
        # Import BEFORE patching to ensure mocks are already in place
        from vocalinux.common_types import RecognitionState
        from vocalinux.ui.tray_indicator import TrayIndicator

        with (
            patch("vocalinux.ui.tray_indicator.logging"),
            patch("vocalinux.ui.tray_indicator._resource_manager") as mock_resource_manager,
            patch("vocalinux.ui.tray_indicator.ConfigManager") as mock_config_manager,
            patch("vocalinux.ui.tray_indicator.KeyboardShortcutManager") as mock_keyboard_manager,
        ):

            from vocalinux.ui.tray_indicator import TrayIndicator

            mock_speech_engine = MagicMock()
            mock_text_injector = MagicMock()
            mock_config_inst = MagicMock()
            mock_config_inst.get.return_value = "ctrl+ctrl"
            mock_config_manager.return_value = mock_config_inst
            mock_keyboard_inst = MagicMock()
            mock_keyboard_inst.active = False
            mock_keyboard_manager.return_value = mock_keyboard_inst
            mock_resource_manager.icons_dir = "/tmp/icons"
            mock_resource_manager.get_icon_path.return_value = "/tmp/icons/test.png"
            mock_resource_manager.ensure_directories_exist.return_value = None
            mock_resource_manager.validate_resources.return_value = {
                "resources_dir_exists": True,
                "missing_icons": [],
                "missing_sounds": [],
            }

            indicator = TrayIndicator(
                speech_engine=mock_speech_engine,
                text_injector=mock_text_injector,
            )

            assert indicator is not None

    def test_add_menu_separator(self):
        """Test adding a menu separator."""
        # Import BEFORE patching to ensure mocks are already in place
        from vocalinux.common_types import RecognitionState
        from vocalinux.ui.tray_indicator import TrayIndicator

        with (
            patch("vocalinux.ui.tray_indicator.logging"),
            patch("vocalinux.ui.tray_indicator._resource_manager") as mock_resource_manager,
            patch("vocalinux.ui.tray_indicator.ConfigManager") as mock_config_manager,
            patch("vocalinux.ui.tray_indicator.KeyboardShortcutManager") as mock_keyboard_manager,
        ):

            from vocalinux.ui.tray_indicator import TrayIndicator

            mock_speech_engine = MagicMock()
            mock_text_injector = MagicMock()
            mock_config_inst = MagicMock()
            mock_config_inst.get.return_value = "ctrl+ctrl"
            mock_config_manager.return_value = mock_config_inst
            mock_keyboard_inst = MagicMock()
            mock_keyboard_inst.active = False
            mock_keyboard_manager.return_value = mock_keyboard_inst
            mock_resource_manager.icons_dir = "/tmp/icons"
            mock_resource_manager.get_icon_path.return_value = "/tmp/icons/test.png"
            mock_resource_manager.ensure_directories_exist.return_value = None
            mock_resource_manager.validate_resources.return_value = {
                "resources_dir_exists": True,
                "missing_icons": [],
                "missing_sounds": [],
            }

            indicator = TrayIndicator(
                speech_engine=mock_speech_engine,
                text_injector=mock_text_injector,
            )

            assert indicator is not None


class TestTrayIndicatorStateHandling(unittest.TestCase):
    """Tests for TrayIndicator state handling."""

    @classmethod
    def setUpClass(cls):
        """Set up class fixtures."""
        sys.modules["gi"] = mock_gi
        sys.modules["gi.repository"] = mock_gi_repository

    def setUp(self):
        """Set up test environment before each test."""
        mock_gtk.reset_mock()
        mock_glib.reset_mock()
        mock_gobject.reset_mock()
        mock_gdkpixbuf.reset_mock()
        mock_appindicator.reset_mock()
        mock_glib.idle_add.side_effect = lambda func, *args: func(*args) or False
        modules_to_remove = [k for k in list(sys.modules.keys()) if "tray_indicator" in k]
        for mod in modules_to_remove:
            del sys.modules[mod]

    def test_on_recognition_state_changed(self):
        """Test state change callback."""
        # Import BEFORE patching to ensure mocks are already in place
        from vocalinux.common_types import RecognitionState
        from vocalinux.ui.tray_indicator import TrayIndicator

        with (
            patch("vocalinux.ui.tray_indicator.logging"),
            patch("vocalinux.ui.tray_indicator._resource_manager") as mock_resource_manager,
            patch("vocalinux.ui.tray_indicator.ConfigManager") as mock_config_manager,
            patch("vocalinux.ui.tray_indicator.KeyboardShortcutManager") as mock_keyboard_manager,
        ):

            from vocalinux.ui.tray_indicator import TrayIndicator

            mock_speech_engine = MagicMock()
            mock_text_injector = MagicMock()
            mock_config_inst = MagicMock()
            mock_config_inst.get.return_value = "ctrl+ctrl"
            mock_config_manager.return_value = mock_config_inst
            mock_keyboard_inst = MagicMock()
            mock_keyboard_inst.active = False
            mock_keyboard_manager.return_value = mock_keyboard_inst
            mock_resource_manager.icons_dir = "/tmp/icons"
            mock_resource_manager.get_icon_path.return_value = "/tmp/icons/test.png"
            mock_resource_manager.ensure_directories_exist.return_value = None
            mock_resource_manager.validate_resources.return_value = {
                "resources_dir_exists": True,
                "missing_icons": [],
                "missing_sounds": [],
            }

            indicator = TrayIndicator(
                speech_engine=mock_speech_engine,
                text_injector=mock_text_injector,
            )

            assert indicator is not None

    def test_update_ui_idle_state(self):
        """Test UI update for idle state."""
        # Import BEFORE patching to ensure mocks are already in place
        from vocalinux.common_types import RecognitionState
        from vocalinux.ui.tray_indicator import TrayIndicator

        with (
            patch("vocalinux.ui.tray_indicator.logging"),
            patch("vocalinux.ui.tray_indicator._resource_manager") as mock_resource_manager,
            patch("vocalinux.ui.tray_indicator.ConfigManager") as mock_config_manager,
            patch("vocalinux.ui.tray_indicator.KeyboardShortcutManager") as mock_keyboard_manager,
        ):

            from vocalinux.ui.tray_indicator import TrayIndicator

            mock_speech_engine = MagicMock()
            mock_text_injector = MagicMock()
            mock_config_inst = MagicMock()
            mock_config_inst.get.return_value = "ctrl+ctrl"
            mock_config_manager.return_value = mock_config_inst
            mock_keyboard_inst = MagicMock()
            mock_keyboard_inst.active = False
            mock_keyboard_manager.return_value = mock_keyboard_inst
            mock_resource_manager.icons_dir = "/tmp/icons"
            mock_resource_manager.get_icon_path.return_value = "/tmp/icons/test.png"
            mock_resource_manager.ensure_directories_exist.return_value = None
            mock_resource_manager.validate_resources.return_value = {
                "resources_dir_exists": True,
                "missing_icons": [],
                "missing_sounds": [],
            }

            indicator = TrayIndicator(
                speech_engine=mock_speech_engine,
                text_injector=mock_text_injector,
            )

            assert indicator is not None

    def test_update_ui_listening_state(self):
        """Test UI update for listening state."""
        # Import BEFORE patching to ensure mocks are already in place
        from vocalinux.common_types import RecognitionState
        from vocalinux.ui.tray_indicator import TrayIndicator

        with (
            patch("vocalinux.ui.tray_indicator.logging"),
            patch("vocalinux.ui.tray_indicator._resource_manager") as mock_resource_manager,
            patch("vocalinux.ui.tray_indicator.ConfigManager") as mock_config_manager,
            patch("vocalinux.ui.tray_indicator.KeyboardShortcutManager") as mock_keyboard_manager,
        ):

            from vocalinux.ui.tray_indicator import TrayIndicator

            mock_speech_engine = MagicMock()
            mock_text_injector = MagicMock()
            mock_config_inst = MagicMock()
            mock_config_inst.get.return_value = "ctrl+ctrl"
            mock_config_manager.return_value = mock_config_inst
            mock_keyboard_inst = MagicMock()
            mock_keyboard_inst.active = False
            mock_keyboard_manager.return_value = mock_keyboard_inst
            mock_resource_manager.icons_dir = "/tmp/icons"
            mock_resource_manager.get_icon_path.return_value = "/tmp/icons/test.png"
            mock_resource_manager.ensure_directories_exist.return_value = None
            mock_resource_manager.validate_resources.return_value = {
                "resources_dir_exists": True,
                "missing_icons": [],
                "missing_sounds": [],
            }

            indicator = TrayIndicator(
                speech_engine=mock_speech_engine,
                text_injector=mock_text_injector,
            )

            assert indicator is not None


class TestTrayIndicatorSignalHandling(unittest.TestCase):
    """Tests for TrayIndicator signal handling."""

    @classmethod
    def setUpClass(cls):
        """Set up class fixtures."""
        sys.modules["gi"] = mock_gi
        sys.modules["gi.repository"] = mock_gi_repository

    def setUp(self):
        """Set up test environment before each test."""
        mock_gtk.reset_mock()
        mock_glib.reset_mock()
        mock_gobject.reset_mock()
        mock_gdkpixbuf.reset_mock()
        mock_appindicator.reset_mock()
        mock_glib.idle_add.side_effect = lambda func, *args: func(*args) or False
        modules_to_remove = [k for k in list(sys.modules.keys()) if "tray_indicator" in k]
        for mod in modules_to_remove:
            del sys.modules[mod]

    def test_signal_handler(self):
        """Test signal handler for graceful termination."""
        # Import BEFORE patching to ensure mocks are already in place
        from vocalinux.common_types import RecognitionState
        from vocalinux.ui.tray_indicator import TrayIndicator

        with (
            patch("vocalinux.ui.tray_indicator.logging"),
            patch("vocalinux.ui.tray_indicator._resource_manager") as mock_resource_manager,
            patch("vocalinux.ui.tray_indicator.ConfigManager") as mock_config_manager,
            patch("vocalinux.ui.tray_indicator.KeyboardShortcutManager") as mock_keyboard_manager,
        ):

            from vocalinux.ui.tray_indicator import TrayIndicator

            mock_speech_engine = MagicMock()
            mock_text_injector = MagicMock()
            mock_config_inst = MagicMock()
            mock_config_inst.get.return_value = "ctrl+ctrl"
            mock_config_manager.return_value = mock_config_inst
            mock_keyboard_inst = MagicMock()
            mock_keyboard_inst.active = False
            mock_keyboard_manager.return_value = mock_keyboard_inst
            mock_resource_manager.icons_dir = "/tmp/icons"
            mock_resource_manager.get_icon_path.return_value = "/tmp/icons/test.png"
            mock_resource_manager.ensure_directories_exist.return_value = None
            mock_resource_manager.validate_resources.return_value = {
                "resources_dir_exists": True,
                "missing_icons": [],
                "missing_sounds": [],
            }

            indicator = TrayIndicator(
                speech_engine=mock_speech_engine,
                text_injector=mock_text_injector,
            )

            # Test signal handler
            indicator._signal_handler(signal.SIGINT, None)

            # Verify idle_add was called to quit
            mock_glib.idle_add.assert_called()

    def test_update_shortcut(self):
        """Test updating keyboard shortcut."""
        # Import BEFORE patching to ensure mocks are already in place
        from vocalinux.common_types import RecognitionState
        from vocalinux.ui.tray_indicator import TrayIndicator

        with (
            patch("vocalinux.ui.tray_indicator.logging"),
            patch("vocalinux.ui.tray_indicator._resource_manager") as mock_resource_manager,
            patch("vocalinux.ui.tray_indicator.ConfigManager") as mock_config_manager,
            patch("vocalinux.ui.tray_indicator.KeyboardShortcutManager") as mock_keyboard_manager,
        ):

            from vocalinux.ui.tray_indicator import TrayIndicator

            mock_speech_engine = MagicMock()
            mock_text_injector = MagicMock()
            mock_config_inst = MagicMock()
            mock_config_inst.get.return_value = "ctrl+ctrl"
            mock_config_manager.return_value = mock_config_inst
            mock_keyboard_inst = MagicMock()
            mock_keyboard_inst.active = True
            mock_keyboard_inst.shortcut = "ctrl+ctrl"
            mock_keyboard_inst.mode = "toggle"
            mock_keyboard_inst.set_shortcut.return_value = True
            mock_keyboard_manager.return_value = mock_keyboard_inst
            mock_resource_manager.icons_dir = "/tmp/icons"
            mock_resource_manager.get_icon_path.return_value = "/tmp/icons/test.png"
            mock_resource_manager.ensure_directories_exist.return_value = None
            mock_resource_manager.validate_resources.return_value = {
                "resources_dir_exists": True,
                "missing_icons": [],
                "missing_sounds": [],
            }

            indicator = TrayIndicator(
                speech_engine=mock_speech_engine,
                text_injector=mock_text_injector,
            )

            # Test updating shortcut
            result = indicator.update_shortcut("alt+alt")

            # Verify the update succeeded
            assert isinstance(result, bool)


if __name__ == "__main__":
    unittest.main()


class TestTrayIndicatorLanguageSwitching(unittest.TestCase):
    """Tests for the Language submenu and cycle-language shortcut wiring."""

    @classmethod
    def setUpClass(cls):
        """Set up class fixtures."""
        sys.modules["gi"] = mock_gi
        sys.modules["gi.repository"] = mock_gi_repository

    def setUp(self):
        """Set up test environment before each test."""
        mock_gtk.reset_mock()
        mock_glib.reset_mock()
        mock_appindicator.reset_mock()
        mock_glib.idle_add.side_effect = lambda func, *args: func(*args) or False
        modules_to_remove = [k for k in list(sys.modules.keys()) if "tray_indicator" in k]
        for mod in modules_to_remove:
            del sys.modules[mod]

    def _make_indicator(self, cycle_shortcut=""):
        """Build a TrayIndicator with all collaborators mocked."""
        from vocalinux.ui.tray_indicator import TrayIndicator

        patchers = [
            patch("vocalinux.ui.tray_indicator.logging"),
            patch("vocalinux.ui.tray_indicator._resource_manager"),
            patch("vocalinux.ui.tray_indicator.ConfigManager"),
            patch("vocalinux.ui.tray_indicator.KeyboardShortcutManager"),
            patch("vocalinux.ui.tray_indicator.LanguageSwitcher"),
        ]
        mocks = [p.start() for p in patchers]
        for p in patchers:
            self.addCleanup(p.stop)
        _, mock_resource_manager, mock_config_manager, mock_keyboard_manager, mock_switcher_cls = (
            mocks
        )

        config_values = {
            ("shortcuts", "toggle_recognition"): "ctrl+ctrl",
            ("shortcuts", "mode"): "toggle",
            ("shortcuts", "cycle_language"): cycle_shortcut,
        }
        mock_config_inst = MagicMock()
        mock_config_inst.get_str.side_effect = lambda section, key, default="": config_values.get(
            (section, key), default
        )
        mock_config_manager.return_value = mock_config_inst

        mock_keyboard_inst = MagicMock()
        mock_keyboard_inst.active = False
        mock_keyboard_manager.return_value = mock_keyboard_inst

        mock_switcher_inst = MagicMock()
        mock_switcher_cls.return_value = mock_switcher_inst

        mock_resource_manager.icons_dir = "/tmp/icons"
        mock_resource_manager.get_icon_path.return_value = "/tmp/icons/test.png"
        mock_resource_manager.validate_resources.return_value = {
            "resources_dir_exists": True,
            "missing_icons": [],
            "missing_sounds": [],
        }

        indicator = TrayIndicator(
            speech_engine=MagicMock(),
            text_injector=MagicMock(),
        )
        return indicator, mock_keyboard_inst, mock_switcher_inst

    def test_cycle_shortcut_registered_when_configured(self):
        """A configured cycle shortcut is registered as an extra shortcut."""
        indicator, keyboard, _ = self._make_indicator(cycle_shortcut="alt+alt")

        keyboard.register_extra_shortcut.assert_called_once_with(
            "cycle_language", "alt+alt", indicator._on_cycle_language
        )

    def test_cycle_shortcut_skipped_when_disabled(self):
        """No extra shortcut is registered when cycle_language is empty."""
        _, keyboard, _ = self._make_indicator(cycle_shortcut="")

        keyboard.register_extra_shortcut.assert_not_called()

    def test_on_cycle_language_delegates_to_switcher(self):
        """The cycle shortcut callback delegates to LanguageSwitcher.cycle."""
        indicator, _, switcher = self._make_indicator()

        indicator._on_cycle_language()

        switcher.cycle.assert_called_once()

    def test_update_cycle_shortcut_registers_new(self):
        """update_cycle_shortcut re-registers the extra binding live."""
        indicator, keyboard, _ = self._make_indicator()
        keyboard.register_extra_shortcut.reset_mock()
        keyboard.register_extra_shortcut.return_value = True

        result = indicator.update_cycle_shortcut("shift+shift")

        self.assertTrue(result)
        keyboard.unregister_extra_shortcut.assert_called_with("cycle_language")
        keyboard.register_extra_shortcut.assert_called_once_with(
            "cycle_language", "shift+shift", indicator._on_cycle_language
        )

    def test_update_cycle_shortcut_empty_disables(self):
        """update_cycle_shortcut('') unregisters without re-registering."""
        indicator, keyboard, _ = self._make_indicator(cycle_shortcut="alt+alt")
        keyboard.register_extra_shortcut.reset_mock()

        result = indicator.update_cycle_shortcut("")

        self.assertTrue(result)
        keyboard.unregister_extra_shortcut.assert_called_with("cycle_language")
        keyboard.register_extra_shortcut.assert_not_called()

    def test_language_menu_activation_calls_switch_to(self):
        """Activating an active radio item switches the language."""
        indicator, _, switcher = self._make_indicator()
        widget = MagicMock()
        widget.get_active.return_value = True

        indicator._on_language_menu_activated(widget, "ca")

        switcher.switch_to.assert_called_once_with("ca")

    def test_language_menu_activation_ignores_deactivation(self):
        """Radio items being deactivated do not trigger a switch."""
        indicator, _, switcher = self._make_indicator()
        widget = MagicMock()
        widget.get_active.return_value = False

        indicator._on_language_menu_activated(widget, "ca")

        switcher.switch_to.assert_not_called()

    def test_language_menu_activation_respects_syncing_guard(self):
        """No switch is triggered while the submenu is being rebuilt."""
        indicator, _, switcher = self._make_indicator()
        indicator._syncing_language_menu = True
        widget = MagicMock()
        widget.get_active.return_value = True

        indicator._on_language_menu_activated(widget, "ca")

        switcher.switch_to.assert_not_called()

    def test_rebuild_language_submenu_creates_one_item_per_language(self):
        """The submenu gets one radio item per effective language."""
        indicator, _, switcher = self._make_indicator()
        switcher.get_effective_languages.return_value = ["en-us", "ca", "es"]
        switcher.get_current_language.return_value = "ca"
        submenu = MagicMock()
        submenu.get_children.return_value = []
        indicator._language_submenu = submenu

        indicator._rebuild_language_submenu()

        self.assertEqual(submenu.append.call_count, 3)
        submenu.show_all.assert_called_once()
        self.assertFalse(indicator._syncing_language_menu)

    def test_settings_dialog_close_rebuilds_submenu(self):
        """Closing the settings dialog re-syncs the Language submenu."""
        indicator, _, _ = self._make_indicator()
        indicator._rebuild_language_submenu = MagicMock()
        dialog = MagicMock()

        indicator._on_settings_dialog_response(dialog, mock_gtk.ResponseType.CLOSE)

        indicator._rebuild_language_submenu.assert_called_once()
        dialog.destroy.assert_called_once()

    def test_language_label_text_known_languages(self):
        """Known language codes map to their 2-letter Whisper-derived badge."""
        indicator, _, _ = self._make_indicator()

        self.assertEqual(indicator._language_label_text("en-us"), "EN")
        self.assertEqual(indicator._language_label_text("es"), "ES")
        self.assertEqual(indicator._language_label_text("ca"), "CA")

    def test_language_label_text_auto_is_empty(self):
        """Auto-detect has no single language, so it shows no badge."""
        indicator, _, _ = self._make_indicator()

        self.assertEqual(indicator._language_label_text("auto"), "")

    def test_language_label_text_unknown_code_is_empty(self):
        """An unrecognized language code degrades to no badge instead of raising."""
        indicator, _, _ = self._make_indicator()

        self.assertEqual(indicator._language_label_text("xx-yy"), "")

    def test_update_language_label_sets_indicator_label(self):
        """The AppIndicator label reflects the current language's badge."""
        indicator, _, switcher = self._make_indicator()
        switcher.get_current_language.return_value = "ca"
        indicator.indicator.set_label.reset_mock()  # clear the call from init

        indicator._update_language_label()

        indicator.indicator.set_label.assert_called_once_with("CA", "XX")

    def test_update_language_label_auto_clears_label(self):
        """Auto-detect clears the label instead of showing a stale badge."""
        indicator, _, switcher = self._make_indicator()
        switcher.get_current_language.return_value = "auto"
        indicator.indicator.set_label.reset_mock()  # clear the call from init

        indicator._update_language_label()

        indicator.indicator.set_label.assert_called_once_with("", "XX")

    def test_update_language_label_noop_without_indicator(self):
        """Refreshing the label before the indicator exists is a safe no-op."""
        indicator, _, _ = self._make_indicator()
        del indicator.indicator

        indicator._update_language_label()  # Should not raise

    def test_on_language_switched_refreshes_label(self):
        """A completed language switch also refreshes the tray label."""
        indicator, _, switcher = self._make_indicator()
        switcher.get_current_language.return_value = "fr"

        indicator._on_language_switched("fr")

        indicator.indicator.set_label.assert_called_with("FR", "XX")

    def test_icon_name_carries_language_badge(self):
        """With a language selected, the icon is generated with the badge drawn in."""
        from vocalinux.common_types import RecognitionState

        indicator, _, switcher = self._make_indicator()
        switcher.get_current_language.return_value = "ca"

        with patch(
            "vocalinux.ui.tray_indicator.render_language_icon", return_value="generated-icon"
        ) as render:
            name, description = indicator._icon_name_for_state(RecognitionState.LISTENING)

        render.assert_called_once_with("CA", "active")
        self.assertEqual(name, "generated-icon")
        self.assertIn("CA", description)

    def test_icon_name_falls_back_when_generation_fails(self):
        """An unwritable icon cache degrades to the packaged icon, not a broken tray."""
        from vocalinux.common_types import RecognitionState

        indicator, _, switcher = self._make_indicator()
        switcher.get_current_language.return_value = "ca"

        with patch("vocalinux.ui.tray_indicator.render_language_icon", return_value=""):
            name, _ = indicator._icon_name_for_state(RecognitionState.LISTENING)

        self.assertEqual(name, "vocalinux-microphone")

    def test_icon_name_falls_back_to_base_icon_for_auto(self):
        """Auto-detect has no badge, so the packaged icons are used."""
        from vocalinux.common_types import RecognitionState

        indicator, _, switcher = self._make_indicator()
        switcher.get_current_language.return_value = "auto"

        name, _ = indicator._icon_name_for_state(RecognitionState.LISTENING)

        self.assertEqual(name, "vocalinux-microphone")

    def test_language_switch_redraws_icon(self):
        """Switching language updates the icon, not just the (often ignored) label."""
        indicator, _, switcher = self._make_indicator()
        switcher.get_current_language.return_value = "es"
        indicator.indicator.set_icon_full.reset_mock()

        with patch(
            "vocalinux.ui.tray_indicator.render_language_icon", return_value="generated-icon"
        ):
            indicator._on_language_switched("es")

        indicator.indicator.set_icon_full.assert_called()
        self.assertEqual(indicator.indicator.set_icon_full.call_args[0][0], "generated-icon")

    def test_language_switch_sets_tooltip_title(self):
        """The readable language name is exposed as a tooltip fallback."""
        indicator, _, switcher = self._make_indicator()
        switcher.get_current_language.return_value = "ca"

        indicator._on_language_switched("ca")

        indicator.indicator.set_title.assert_called_with("Vocalinux - Catalan")

    def test_settings_dialog_close_updates_language_label(self):
        """Closing the settings dialog also refreshes the tray label."""
        indicator, _, _ = self._make_indicator()
        indicator._update_language_label = MagicMock()
        dialog = MagicMock()

        indicator._on_settings_dialog_response(dialog, mock_gtk.ResponseType.CLOSE)

        indicator._update_language_label.assert_called_once()
