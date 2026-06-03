"""Optional speech-to-text and text-to-speech helpers."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Optional


@dataclass
class SpeechResult:
    text: str
    error: Optional[str] = None


def speech_recognition_available() -> bool:
    try:
        import speech_recognition  # noqa: F401

        return True
    except ImportError:
        return False


def tts_available() -> bool:
    try:
        import pyttsx3  # noqa: F401

        return True
    except ImportError:
        return False


def speech_to_text(
    *,
    timeout: float = 8.0,
    phrase_limit: float = 12.0,
) -> SpeechResult:
    if not speech_recognition_available():
        return SpeechResult(
            "",
            error="speechrecognition not installed. Run: pip install -e \".[voice]\"",
        )
    import speech_recognition as sr

    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.4)
            audio = recognizer.listen(
                source,
                timeout=timeout,
                phrase_time_limit=phrase_limit,
            )
    except OSError as e:
        return SpeechResult("", error=f"Microphone unavailable: {e}")
    except Exception as e:
        name = type(e).__name__
        if name == "WaitTimeoutError":
            return SpeechResult("", error="No speech detected (timeout).")
        return SpeechResult("", error=f"Could not access microphone: {e}")

    try:
        text = recognizer.recognize_google(audio)
        if not text.strip():
            return SpeechResult("", error="Empty transcript.")
        return SpeechResult(text.strip())
    except Exception as e:
        name = type(e).__name__
        if name == "UnknownValueError":
            return SpeechResult("", error="Could not understand audio.")
        if name == "RequestError":
            return SpeechResult("", error=f"Speech API failed: {e}")
        return SpeechResult("", error=str(e))


def text_to_speech(text: str, *, block: bool = False) -> Optional[str]:
    """Speak text using pyttsx3. Returns error message or None on success."""
    if not text.strip():
        return "Nothing to speak."
    if not tts_available():
        return "pyttsx3 not installed. Run: pip install -e \".[voice]\""

    def _speak() -> None:
        import pyttsx3

        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()

    try:
        if block:
            _speak()
        else:
            thread = threading.Thread(target=_speak, daemon=True)
            thread.start()
        return None
    except Exception as e:
        return str(e)
