# Функция для отправки чека о покупке топ-позиции
from datetime import datetime

from shared.services.email import send_email


async def send_top_purchase_email(email: str, days: int, total_cost: float, time_stop: datetime):
 html = f"""
 <html>
 <body style="font-family: Arial, sans-serif; color: #333;">
 <h2>Спасибо за покупку топ-позиции на платформе YAMS!</h2>
 <p>Вы приобрели топ-позицию на <strong>{days} {'день' if days == 1 else 'дня' if days < 5 else 'дней'}</strong></p>
 <p>Стоимость: <strong>{total_cost:.2f} ₽</strong></p>
 <p>Топ-позиция активна до: <strong>{time_stop.strftime('%Y-%m-%d %H:%M:%S')}</strong></p>
 <p>Ваша компания теперь будет отображаться в начале рейтинга и списка компаний.</p>
 <br>
 <p>Мы благодарим Вас за доверие и будем рады видеть Вас снова!</p>
 <p style="color: gray;">С уважением, команда YAMS</p>
 </body>
 </html>
 """
 await send_email(email, "Подтверждение покупки топ-позиции", html, content_type="text/html")