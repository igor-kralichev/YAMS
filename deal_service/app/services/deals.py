from shared.services.email import send_email

# Отправка чека о сделке в приложении
async def send_purchase_email(email: str, name_deal: str, price: float, yams_fee: float):
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <h2>Спасибо за покупку через платформу YAMS!</h2>
        <p>Вы совершили сделку: <strong>{name_deal}</strong></p>
        <p>Стоимость: <strong>{price:.2f} ₽</strong></p>
        <p>Комиссия YAMS (3%): <strong>{yams_fee:.2f} ₽</strong></p>
        <p>Итоговая сумма: <strong>{price + yams_fee:.2f} ₽</strong></p>
        <br>
        <p>Мы благодарим Вас за доверие и будем рады видеть Вас снова!</p>
        <p style="color: gray;">С уважением, команда YAMS</p>
      </body>
    </html>
    """
    await send_email(email, "Подтверждение покупки сделки", html, content_type="text/html")
