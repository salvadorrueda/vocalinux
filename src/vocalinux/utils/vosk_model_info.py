"""Language registry and VOSK model metadata."""

import os

# Models directory
MODELS_DIR = os.path.expanduser("~/.local/share/vocalinux/models")
SYSTEM_MODELS_DIRS = [
    "/usr/local/share/vocalinux/models",
    "/usr/share/vocalinux/models",
]

# Language definitions with display names and Whisper/VOSK codes
# Supported languages for speech recognition
SUPPORTED_LANGUAGES = {
    "auto": {
        "name": "Auto-detect",
        "whisper": None,
        "vosk": None,
        "warning": "Slower, may be less accurate",
    },
    "en-us": {
        "name": "English (US)",
        "whisper": "en",
        "vosk": "vosk-model-small-en-us-0.15",
    },
    "hi": {
        "name": "Hindi",
        "whisper": "hi",
        "vosk": "vosk-model-small-hi-0.22",
    },
    "es": {
        "name": "Spanish",
        "whisper": "es",
        "vosk": "vosk-model-small-es-0.42",
    },
    "ca": {
        "name": "Catalan",
        "whisper": "ca",
        "vosk": "vosk-model-small-ca-0.4",
    },
    "fr": {
        "name": "French",
        "whisper": "fr",
        "vosk": "vosk-model-small-fr-0.22",
    },
    "de": {
        "name": "German",
        "whisper": "de",
        "vosk": "vosk-model-small-de-0.15",
    },
    "it": {
        "name": "Italian",
        "whisper": "it",
        "vosk": "vosk-model-small-it-0.22",
    },
    "pt": {
        "name": "Portuguese",
        "whisper": "pt",
        "vosk": "vosk-model-small-pt-0.3",
    },
    "ru": {
        "name": "Russian",
        "whisper": "ru",
        "vosk": "vosk-model-small-ru-0.22",
    },
    "zh": {
        "name": "Chinese",
        "whisper": "zh",
        "vosk": "vosk-model-small-cn-0.22",
    },
}


# VOSK model metadata for display
VOSK_MODEL_INFO = {
    "small": {
        "size_mb": 40,
        "desc": "Lightweight, fast",
        "languages": {
            "en-us": "vosk-model-small-en-us-0.15",
            "en-in": "vosk-model-small-en-in-0.4",
            "hi": "vosk-model-small-hi-0.22",
            "es": "vosk-model-small-es-0.42",
            "ca": "vosk-model-small-ca-0.4",
            "fr": "vosk-model-small-fr-0.22",
            "de": "vosk-model-small-de-0.15",
            "it": "vosk-model-small-it-0.22",
            "pt": "vosk-model-small-pt-0.3",
            "ru": "vosk-model-small-ru-0.22",
            "zh": "vosk-model-small-cn-0.22",
        },
    },
    "medium": {
        "size_mb": 1500,
        "desc": "Balanced accuracy/speed",
        "languages": {
            "en-us": "vosk-model-en-us-0.22",
            "fr": "vosk-model-fr-0.22",
            "de": "vosk-model-de-0.21",
            "ru": "vosk-model-ru-0.22",
            "hi": "vosk-model-hi-0.22",
            "es": "vosk-model-es-0.42",
            "pt": "vosk-model-pt-0.4",
            "zh": "vosk-model-cn-0.22",
        },
    },
    "large": {
        "size_mb": 1500,
        "desc": "Same as medium (best available)",
        "languages": {
            "en-us": "vosk-model-en-us-0.22",
            "fr": "vosk-model-fr-0.22",
            "de": "vosk-model-de-0.21",
            "ru": "vosk-model-ru-0.22",
            "hi": "vosk-model-hi-0.22",
            "es": "vosk-model-es-0.42",
            "pt": "vosk-model-pt-0.4",
            "zh": "vosk-model-cn-0.22",
        },
    },
}


def is_vosk_model_downloaded(size: str, language: str) -> bool:
    """Check if a VOSK model is downloaded for the given size and language."""
    if size not in VOSK_MODEL_INFO:
        return False

    # Auto-detect is not supported by VOSK, fall back to en-us
    if language == "auto":
        language = "en-us"
    if language not in VOSK_MODEL_INFO[size]["languages"]:
        # Runtime falls back to the small model of the same language
        size = "small"
        if language not in VOSK_MODEL_INFO["small"]["languages"]:
            language = "en-us"

    model_name = VOSK_MODEL_INFO[size]["languages"][language]

    # Check user's local models directory
    user_model_path = os.path.join(MODELS_DIR, model_name)
    if os.path.exists(user_model_path):
        return True

    # Check system-wide installation directories
    for system_dir in SYSTEM_MODELS_DIRS:
        system_model_path = os.path.join(system_dir, model_name)
        if os.path.exists(system_model_path):
            return True

    return False
