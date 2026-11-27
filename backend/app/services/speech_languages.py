"""Which languages the speech-to-text model can be told about.

Groq serves OpenAI Whisper. Whisper accepts an explicit ``language`` hint only
for the languages it was trained on; sending anything else makes the API reject
the request with HTTP 400. Igbo (``ig``) is NOT in that list, whereas Yoruba
(``yo``) and Hausa (``ha``) are.

For an unsupported language we omit the hint and let the model auto-detect.
The result is a best-effort draft that a person must correct; the UI warns
about this before the transcription starts.
"""

from __future__ import annotations

# Whisper's language set (ISO 639-1, plus the 3-letter codes Whisper itself uses).
WHISPER_LANGUAGES: frozenset[str] = frozenset(
    {
        "af", "am", "ar", "as", "az", "ba", "be", "bg", "bn", "bo", "br", "bs",
        "ca", "cs", "cy", "da", "de", "el", "en", "es", "et", "eu", "fa", "fi",
        "fo", "fr", "gl", "gu", "ha", "haw", "he", "hi", "hr", "ht", "hu", "hy",
        "id", "is", "it", "ja", "jw", "ka", "kk", "km", "kn", "ko", "la", "lb",
        "ln", "lo", "lt", "lv", "mg", "mi", "mk", "ml", "mn", "mr", "ms", "mt",
        "my", "ne", "nl", "nn", "no", "oc", "pa", "pl", "ps", "pt", "ro", "ru",
        "sa", "sd", "si", "sk", "sl", "sn", "so", "sq", "sr", "su", "sv", "sw",
        "ta", "te", "tg", "th", "tk", "tl", "tr", "tt", "uk", "ur", "uz", "vi",
        "yi", "yo", "zh",
    }
)


def whisper_supports(language_code: str | None) -> bool:
    """True when Whisper accepts ``language_code`` as an explicit hint."""
    return bool(language_code) and language_code.lower() in WHISPER_LANGUAGES
