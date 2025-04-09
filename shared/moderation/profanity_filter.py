import re
from pathlib import Path

class ProfanityFilter:
    def __init__(self):
        self.regex = None
        self.load_words()

    def load_words(self):
        path = Path(__file__).parent / "banned_words.txt"
        with open(path, encoding="utf-8") as f:
            patterns = []
            for line in f:
                word = line.strip()
                if word:
                    # Преобразуем специальные символы в регулярные выражения
                    pattern = (
                        re.escape(word)
                        .replace(r'\{', r'\w*')  # { -> любое количество букв/цифр
                        .replace(r'\}', r'\w*')  # } -> любое количество букв/цифр
                        .replace(r'\|', r'\W*')  # | -> любое количество не букв/цифр
                        .replace(r'\[', r'\W*')  # [ -> любое количество не букв/цифр
                        .replace(r'\]', r'\W*')  # ] -> любое количество не букв/цифр
                    )
                    patterns.append(f'(?:{pattern})')

            # Создаём регулярное выражение с границами слов и игнорированием регистра
            self.regex = re.compile(
                r'(?<!\w)(?:' + '|'.join(patterns) + r')(?!\w)',
                re.IGNORECASE
            )

    def is_clean_exact(self, text: str) -> bool:
        # Проверяем, есть ли совпадения с регулярным выражением
        return self.regex.search(text) is None

# Глобальный экземпляр
filter = ProfanityFilter()