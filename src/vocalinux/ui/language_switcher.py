"""
Quick language switching for Vocalinux.

Shared logic behind the tray "Language" submenu and the cycle-language
keyboard shortcut. GTK-free so it can be tested and reused headlessly.
"""

import logging
import threading
from typing import Callable, List

from ..common_types import RecognitionState
from ..utils.notifications import show_notification
from ..utils.vosk_model_info import SUPPORTED_LANGUAGES, is_vosk_model_downloaded
from ..utils.whispercpp_model_info import is_english_only_model

logger = logging.getLogger(__name__)


class LanguageSwitcher:
    """
    Switches the speech-recognition language outside the settings dialog.

    Reads the user's favorite languages from config, filters them by what the
    current engine supports, and applies switches on a background thread
    (engine reconfiguration blocks, and may download a VOSK model).
    """

    def __init__(self, config_manager, speech_engine):
        self.config_manager = config_manager
        self.speech_engine = speech_engine
        self._switch_lock = threading.Lock()
        self._listeners: List[Callable[[str], None]] = []

    def add_listener(self, callback: Callable[[str], None]) -> None:
        """
        Register a callback invoked with the final language code after a
        switch attempt (the new code on success, the reverted one on failure).

        Called from the worker thread; GTK consumers must hop to the main
        loop themselves (e.g. GLib.idle_add).
        """
        self._listeners.append(callback)

    def get_current_language(self) -> str:
        """The configured recognition language."""
        return self.config_manager.get_str("speech_recognition", "language", "auto")

    def get_effective_languages(self) -> List[str]:
        """
        Favorite languages usable with the current engine, in registry order.

        Always includes the currently configured language so UI radio groups
        can reflect reality even when it is not a favorite.
        """
        favorites = self.config_manager.get_list(
            "speech_recognition", "favorite_languages", ["auto", "en-us"]
        )
        engine = self.config_manager.get_str("speech_recognition", "engine", "whisper_cpp")

        codes = [code for code in SUPPORTED_LANGUAGES if code in favorites]
        codes = [code for code in codes if self._is_language_valid_for_engine(code, engine)]

        if not codes:
            codes = ["en-us"]

        current = self.get_current_language()
        if current in SUPPORTED_LANGUAGES and current not in codes:
            codes.append(current)

        return codes

    def _is_language_valid_for_engine(self, code: str, engine: str) -> bool:
        info = SUPPORTED_LANGUAGES.get(code)
        if info is None:
            return False

        if engine == "vosk":
            return info["vosk"] is not None

        if engine == "whisper_cpp":
            model = self.config_manager.get_model_size_for_engine("whisper_cpp")
            if is_english_only_model(model):
                return info["whisper"] == "en"

        return True

    def switch_to(self, lang_code: str) -> bool:
        """
        Switch the recognition language, applying the change in the background.

        Returns:
            True if the switch was started (or was a no-op), False if it was
            rejected or another switch is already in progress.
        """
        current = self.get_current_language()
        if lang_code == current:
            logger.debug(f"Language already set to {lang_code}")
            return True

        engine = self.config_manager.get_str("speech_recognition", "engine", "whisper_cpp")
        if not self._is_language_valid_for_engine(lang_code, engine):
            display = SUPPORTED_LANGUAGES.get(lang_code, {}).get("name", lang_code)
            self._notify(
                "Language not available",
                f"{display} is not supported by the current engine or model",
                icon="dialog-warning",
            )
            return False

        if not self._switch_lock.acquire(blocking=False):
            logger.info(f"Ignoring language switch to {lang_code}: a switch is in progress")
            return False

        # Persist before reconfiguring so a crash mid-switch still comes back
        # up in the requested language.
        self.config_manager.set("speech_recognition", "language", lang_code)
        self.config_manager.save_config()

        thread = threading.Thread(
            target=self._apply_switch,
            args=(lang_code, current, engine),
            daemon=True,
            name="language-switch",
        )
        thread.start()
        return True

    def _apply_switch(self, lang_code: str, previous: str, engine: str) -> None:
        display = SUPPORTED_LANGUAGES[lang_code]["name"]
        final_code = lang_code
        try:
            if engine == "vosk":
                size = self.config_manager.get_model_size_for_engine("vosk")
                if not is_vosk_model_downloaded(size, lang_code):
                    self._notify(
                        "Downloading model",
                        f"Downloading {display} speech model…",
                    )

            if self.speech_engine.state != RecognitionState.IDLE:
                self.speech_engine.stop_recognition()

            self.speech_engine.reconfigure(language=lang_code)
            self._notify("Language switched", f"Now dictating in {display}")
        except Exception as e:
            logger.error(f"Failed to switch language to {lang_code}: {e}")
            self.config_manager.set("speech_recognition", "language", previous)
            self.config_manager.save_config()
            final_code = previous
            self._notify(
                "Language switch failed",
                f"Could not switch to {display}",
                icon="dialog-error",
            )
        finally:
            self._switch_lock.release()
            for listener in self._listeners:
                try:
                    listener(final_code)
                except Exception as e:
                    logger.error(f"Language switch listener failed: {e}")

    def cycle(self) -> None:
        """Switch to the next favorite language (wraps around)."""
        languages = self.get_effective_languages()
        if len(languages) < 2:
            logger.info("Language cycling needs at least two effective favorite languages")
            return

        current = self.get_current_language()
        try:
            index = languages.index(current)
        except ValueError:
            index = -1

        self.switch_to(languages[(index + 1) % len(languages)])

    def _notify(self, title: str, message: str, icon: str = "dialog-information") -> None:
        if self.config_manager.get_bool("ui", "show_notifications", True):
            show_notification(title, message, icon)
