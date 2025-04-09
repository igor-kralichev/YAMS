import re

from unidecode import unidecode


def transliterate(text: str) -> str:
    text = unidecode(text)
    text = re.sub(r'[^a-zA-Z0-9_]', '_', text)
    text = re.sub(r'_+', '_', text).strip('_')
    return text.lower()