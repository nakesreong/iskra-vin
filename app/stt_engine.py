# app/stt_engine.py
"""Speech-to-text engine based on the Whisper model.

This module loads a Whisper model according to ``configs/settings.yaml`` and
provides :func:`transcribe_audio_to_text` for converting audio files to text. It
is utilized by the Telegram bot for voice command recognition and can be run
standalone for debugging.
"""

import whisper
import os
from .config_loader import load_settings

# --- Load STT configuration (model size) ---
STT_CONFIG_DATA = None
MODEL_SIZE_FROM_CONFIG = "base"  # Default value if the config fails to load

try:
    STT_CONFIG_DATA = load_settings()

    if STT_CONFIG_DATA and "stt_engine" in STT_CONFIG_DATA and "whisper_model_size" in STT_CONFIG_DATA["stt_engine"]:
        MODEL_SIZE_FROM_CONFIG = STT_CONFIG_DATA["stt_engine"]["whisper_model_size"]
        print(f"STT_Engine: Whisper model size from config: '{MODEL_SIZE_FROM_CONFIG}'")
    else:
        print(
            "STT_Engine: Parameter 'whisper_model_size' not found in "
            "configs/settings.yaml (section stt_engine). Using default value "
            f"'{MODEL_SIZE_FROM_CONFIG}'"
        )

except FileNotFoundError:
    print(
        f"STT_Engine: configs/settings.yaml not found. Using default Whisper model '{MODEL_SIZE_FROM_CONFIG}'"
    )
except (RuntimeError, ValueError) as e_yaml:
    print(
        f"STT_Engine: Error in configs/settings.yaml: {e_yaml}. Using default Whisper model '{MODEL_SIZE_FROM_CONFIG}'"
    )
except Exception as e_conf:
    print(f"STT_Engine: Unexpected error loading STT configuration: {e_conf}. Using default Whisper model '{MODEL_SIZE_FROM_CONFIG}'")
# --- End of STT configuration loading ---


# --- Whisper model loading ---
STT_MODEL = None
# Use MODEL_SIZE_FROM_CONFIG
MODEL_TO_LOAD = MODEL_SIZE_FROM_CONFIG

try:
    print(f"STT_Engine: Loading Whisper model '{MODEL_TO_LOAD}'...")
    # download_root could also come from config if needed
    # download_root_path = STT_CONFIG_DATA.get('stt_engine', {}).get('download_root') if STT_CONFIG_DATA else None
    # STT_MODEL = whisper.load_model(MODEL_TO_LOAD, download_root=download_root_path if download_root_path else None)
    # Specify device="cpu" for explicit CPU usage
    STT_MODEL = whisper.load_model(MODEL_TO_LOAD)
    # To use a GPU specify device="cuda" or "cuda:0" for the first available GPU
    print(f"STT_Engine: Whisper model '{MODEL_TO_LOAD}' loaded successfully.")
except Exception as e:
    # ... error handling for model loading remains the same, mentioning MODEL_TO_LOAD
    print(f"Critical STT_Engine error: failed to load Whisper model '{MODEL_TO_LOAD}': {e}")
    STT_MODEL = None
# --- End of model loading ---


def transcribe_audio_to_text(audio_file_path: str) -> str | None:
    """
    Recognize speech from an audio file using Whisper.

    Args:
        audio_file_path (str): Path to the audio file.

    Returns:
        str | None: The recognized text or None on error.
    """
    if not STT_MODEL:
        print("STT_Engine Error: Whisper model not loaded. Cannot transcribe.")
        return None

    if not os.path.exists(audio_file_path):
        print(f"STT_Engine Error: Audio file not found at path: {audio_file_path}")
        return None

    print(f"STT_Engine: Starting transcription of audio file: {audio_file_path}")
    try:
        # Perform recognition.
        # We can specify the language upfront (language="ru")
        # or let Whisper detect it automatically.
        # For better accuracy with Russian it's preferable to set it.
        result = STT_MODEL.transcribe(audio_file_path, language="ru", fp16=False)
        # fp16=False may help if precision issues arise on GPU.
        # On CPU it is less relevant. Remove if using GPU and encountering issues.

        recognized_text = result["text"]
        print(f"STT_Engine: Recognized text: '{recognized_text}'")
        return recognized_text.strip()  # Strip extra spaces

    except Exception as e:
        print(f"STT_Engine Error: An exception occurred during transcription: {e}")
        import traceback

        traceback.print_exc()  # Print full traceback for debugging
        return None


