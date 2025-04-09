import aiosmtplib
from email.message import EmailMessage
from shared.core.config import settings

async def send_email(to_email: str, subject: str, body: str, content_type: str = "text/plain"):
    try:
     message = EmailMessage()
     message["From"] = settings.SMTP_USER
     message["To"] = to_email
     message["Subject"] = subject

     if content_type == "text/html":
         # Устанавливаем HTML-контент как альтернативу
         message.set_content("Если вы видите это сообщение, значит ваш почтовый клиент не поддерживает HTML.")
         message.add_alternative(body, subtype="html")
     else:
         message.set_content(body)

     await aiosmtplib.send(
         message,
         hostname=settings.SMTP_HOST,
         port=settings.SMTP_PORT,
         username=settings.SMTP_USER,
         password=settings.SMTP_PASSWORD,
         use_tls=True,
     )
    except Exception as e:
        print(f"Ошибка отправки email: {str(e)}")