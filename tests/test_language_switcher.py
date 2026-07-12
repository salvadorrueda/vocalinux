"""
Tests for the LanguageSwitcher (quick language switching logic).
"""

from unittest.mock import MagicMock, call, patch

import pytest

from vocalinux.common_types import RecognitionState
from vocalinux.ui.language_switcher import LanguageSwitcher


class InlineThread:
    """threading.Thread stand-in that runs the target synchronously on start()."""

    def __init__(self, target=None, args=(), kwargs=None, daemon=None, name=None):
        self._target = target
        self._args = args
        self._kwargs = kwargs or {}

    def start(self):
        if self._target:
            self._target(*self._args, **self._kwargs)


def _make_config(
    language="en-us",
    engine="whisper_cpp",
    favorites=None,
    show_notifications=True,
    whispercpp_model="tiny",
):
    config = MagicMock()
    values = {
        ("speech_recognition", "language"): language,
        ("speech_recognition", "engine"): engine,
        ("shortcuts", "cycle_language"): "",
    }
    config.get_str.side_effect = lambda section, key, default="": values.get(
        (section, key), default
    )
    config.get_list.return_value = list(favorites if favorites is not None else ["auto", "en-us"])
    config.get_bool.return_value = show_notifications
    config.get_model_size_for_engine.side_effect = lambda engine_name: (
        whispercpp_model if engine_name == "whisper_cpp" else "small"
    )
    return config


def _make_engine(state=RecognitionState.IDLE):
    engine = MagicMock()
    engine.state = state
    return engine


@pytest.fixture(autouse=True)
def inline_threads():
    with patch("vocalinux.ui.language_switcher.threading.Thread", InlineThread):
        yield


@pytest.fixture(autouse=True)
def mock_notifications():
    with patch("vocalinux.ui.language_switcher.show_notification") as mock:
        yield mock


class TestGetEffectiveLanguages:
    def test_favorites_in_registry_order(self):
        config = _make_config(favorites=["fr", "ca", "en-us"])
        switcher = LanguageSwitcher(config, _make_engine())
        assert switcher.get_effective_languages() == ["en-us", "ca", "fr"]

    def test_vosk_drops_auto_and_unsupported(self):
        config = _make_config(engine="vosk", favorites=["auto", "en-us", "ca"])
        switcher = LanguageSwitcher(config, _make_engine())
        assert switcher.get_effective_languages() == ["en-us", "ca"]

    def test_english_only_whispercpp_model_restricts_to_english(self):
        config = _make_config(
            favorites=["auto", "en-us", "ca"],
            whispercpp_model="medium.en",
        )
        switcher = LanguageSwitcher(config, _make_engine())
        assert switcher.get_effective_languages() == ["en-us"]

    def test_empty_result_falls_back_to_en_us(self):
        config = _make_config(favorites=["nonexistent-lang"], language="en-us")
        switcher = LanguageSwitcher(config, _make_engine())
        assert switcher.get_effective_languages() == ["en-us"]

    def test_current_language_always_included(self):
        config = _make_config(language="ca", favorites=["en-us", "es"])
        switcher = LanguageSwitcher(config, _make_engine())
        assert switcher.get_effective_languages() == ["en-us", "es", "ca"]


class TestSwitchTo:
    def test_noop_when_already_current(self):
        config = _make_config(language="ca")
        engine = _make_engine()
        switcher = LanguageSwitcher(config, engine)

        assert switcher.switch_to("ca") is True
        engine.reconfigure.assert_not_called()
        config.set.assert_not_called()

    def test_persists_then_reconfigures(self):
        config = _make_config(language="en-us")
        engine = _make_engine()
        switcher = LanguageSwitcher(config, engine)
        order = []
        config.save_config.side_effect = lambda: order.append("save")
        engine.reconfigure.side_effect = lambda **kw: order.append("reconfigure")

        assert switcher.switch_to("ca") is True

        config.set.assert_called_with("speech_recognition", "language", "ca")
        engine.reconfigure.assert_called_once_with(language="ca")
        assert order == ["save", "reconfigure"]

    def test_stops_recognition_only_when_not_idle(self):
        config = _make_config(language="en-us")
        engine = _make_engine(state=RecognitionState.LISTENING)
        switcher = LanguageSwitcher(config, engine)
        switcher.switch_to("ca")
        engine.stop_recognition.assert_called_once()

        engine_idle = _make_engine(state=RecognitionState.IDLE)
        switcher_idle = LanguageSwitcher(_make_config(language="en-us"), engine_idle)
        switcher_idle.switch_to("ca")
        engine_idle.stop_recognition.assert_not_called()

    def test_rejects_language_invalid_for_engine(self, mock_notifications):
        config = _make_config(language="en-us", engine="vosk")
        engine = _make_engine()
        switcher = LanguageSwitcher(config, engine)

        assert switcher.switch_to("auto") is False
        engine.reconfigure.assert_not_called()
        assert "not available" in mock_notifications.call_args[0][0].lower()

    def test_vosk_missing_model_notifies_download(self, mock_notifications):
        config = _make_config(language="en-us", engine="vosk")
        switcher = LanguageSwitcher(config, _make_engine())

        with patch("vocalinux.ui.language_switcher.is_vosk_model_downloaded", return_value=False):
            switcher.switch_to("ca")

        titles = [c.args[0] for c in mock_notifications.call_args_list]
        assert "Downloading model" in titles
        assert "Language switched" in titles

    def test_success_notification_uses_display_name(self, mock_notifications):
        config = _make_config(language="en-us")
        switcher = LanguageSwitcher(config, _make_engine())
        switcher.switch_to("ca")

        mock_notifications.assert_called_with(
            "Language switched", "Now dictating in Catalan", "dialog-information"
        )

    def test_notifications_suppressed_when_disabled(self, mock_notifications):
        config = _make_config(language="en-us", show_notifications=False)
        switcher = LanguageSwitcher(config, _make_engine())
        switcher.switch_to("ca")
        mock_notifications.assert_not_called()

    def test_failure_reverts_config_and_notifies(self, mock_notifications):
        config = _make_config(language="en-us")
        engine = _make_engine()
        engine.reconfigure.side_effect = RuntimeError("boom")
        switcher = LanguageSwitcher(config, engine)
        listener = MagicMock()
        switcher.add_listener(listener)

        switcher.switch_to("ca")

        assert config.set.call_args_list == [
            call("speech_recognition", "language", "ca"),
            call("speech_recognition", "language", "en-us"),
        ]
        assert "failed" in mock_notifications.call_args[0][0].lower()
        listener.assert_called_once_with("en-us")

    def test_listener_receives_new_code_on_success(self):
        config = _make_config(language="en-us")
        switcher = LanguageSwitcher(config, _make_engine())
        listener = MagicMock()
        switcher.add_listener(listener)

        switcher.switch_to("ca")
        listener.assert_called_once_with("ca")

    def test_lock_released_after_switch(self):
        config = _make_config(language="en-us")
        switcher = LanguageSwitcher(config, _make_engine())
        switcher.switch_to("ca")
        # A second switch must be possible (lock was released)
        assert switcher.switch_to("es") is True


class TestCycle:
    def test_cycles_to_next_favorite(self):
        # Effective order follows the registry: ["en-us", "es", "ca"]
        config = _make_config(language="en-us", favorites=["en-us", "ca", "es"])
        switcher = LanguageSwitcher(config, _make_engine())
        with patch.object(switcher, "switch_to") as mock_switch:
            switcher.cycle()
        mock_switch.assert_called_once_with("es")

    def test_wraps_around(self):
        # Effective order is ["en-us", "es", "ca"]; from the last entry it wraps
        config = _make_config(language="ca", favorites=["en-us", "ca", "es"])
        switcher = LanguageSwitcher(config, _make_engine())
        with patch.object(switcher, "switch_to") as mock_switch:
            switcher.cycle()
        mock_switch.assert_called_once_with("en-us")

    def test_skips_when_fewer_than_two_languages(self):
        config = _make_config(language="en-us", favorites=["en-us"])
        switcher = LanguageSwitcher(config, _make_engine())
        with patch.object(switcher, "switch_to") as mock_switch:
            switcher.cycle()
        mock_switch.assert_not_called()

    def test_current_not_in_favorites_starts_from_first(self):
        config = _make_config(language="de", favorites=["en-us", "ca"])
        switcher = LanguageSwitcher(config, _make_engine())
        with patch.object(switcher, "switch_to") as mock_switch:
            switcher.cycle()
        # Effective list is ["en-us", "ca", "de"]; current "de" is last → wraps to first
        mock_switch.assert_called_once_with("en-us")
