"""
Tests for the language/model registry in vosk_model_info.py.
"""

from vocalinux.utils.vosk_model_info import SUPPORTED_LANGUAGES, VOSK_MODEL_INFO


class TestCatalanSupport:
    """Catalan ("ca") must be registered for both Whisper and VOSK engines."""

    def test_catalan_in_supported_languages(self):
        assert "ca" in SUPPORTED_LANGUAGES
        assert SUPPORTED_LANGUAGES["ca"]["name"] == "Catalan"
        assert SUPPORTED_LANGUAGES["ca"]["whisper"] == "ca"
        assert SUPPORTED_LANGUAGES["ca"]["vosk"] == "vosk-model-small-ca-0.4"

    def test_catalan_small_vosk_model(self):
        assert VOSK_MODEL_INFO["small"]["languages"]["ca"] == "vosk-model-small-ca-0.4"

    def test_catalan_has_no_medium_or_large_vosk_model(self):
        # alphacephei only publishes a small Catalan model; medium/large rely
        # on the runtime small-model fallback in SpeechRecognitionManager.
        assert "ca" not in VOSK_MODEL_INFO["medium"]["languages"]
        assert "ca" not in VOSK_MODEL_INFO["large"]["languages"]


class TestRegistryConsistency:
    """SUPPORTED_LANGUAGES and VOSK_MODEL_INFO must agree with each other."""

    def test_vosk_names_match_small_model_map(self):
        for lang, info in SUPPORTED_LANGUAGES.items():
            if info["vosk"] is None:
                continue
            assert VOSK_MODEL_INFO["small"]["languages"][lang] == info["vosk"], (
                f"SUPPORTED_LANGUAGES[{lang!r}]['vosk'] does not match " f"VOSK_MODEL_INFO['small']"
            )

    def test_every_vosk_language_has_a_small_model(self):
        # The runtime falls back to the small model when a size is missing,
        # so every language present in any size tier must exist in "small".
        for size, size_info in VOSK_MODEL_INFO.items():
            for lang in size_info["languages"]:
                assert lang in VOSK_MODEL_INFO["small"]["languages"], (
                    f"Language {lang!r} in {size!r} tier has no small model to " f"fall back to"
                )
