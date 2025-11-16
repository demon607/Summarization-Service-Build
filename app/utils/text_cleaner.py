import reflex as rx
import unicodedata
import re
import html


def clean_text(text: str | None) -> str:
    """Sanitize text to be clean, English-only ASCII."""
    if not text:
        return ""
    text = html.unescape(text)
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("UTF-8")
    text = re.sub("[^A-Za-z0-9\\s.,!?\\-:;\\'\"()&]", " ", text)
    text = re.sub("\\s+", " ", text).strip()
    return text