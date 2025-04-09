from datetime import datetime

from jose import JWTError, jwt
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.future import select

from shared.core.config import settings
from shared.db.models.accounts import Account_Model
from shared.services.email import send_email


async def get_account_by_email(db: AsyncSession, email: str) -> Account_Model | None:
    result = await db.execute(
        select(Account_Model)
        .options(joinedload(Account_Model.user), joinedload(Account_Model.company))  # Автоматическая загрузка связей
        .filter(Account_Model.email == email)
    )
    return result.scalar_one_or_none()


async def verify_token(token: str) -> dict:
    try:
        # Включаем проверку времени (verify_exp=True по умолчанию)
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        # Дополнительная проверка (на случай если verify_exp не сработает)
        expire_timestamp = payload.get("exp")
        if not expire_timestamp:
            raise HTTPException(status_code=401, detail="Token has no expiration")

        if datetime.utcnow() > datetime.fromtimestamp(expire_timestamp):
            raise HTTPException(status_code=401, detail="Token expired")

        payload["sub"] = int(payload["sub"])  # Преобразуем ID в int
        return payload

    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

# Отправка верификационного письма
async def send_verification_email(email: str, token: str, type: str):
    verification_link = f"{settings.APP_URL}/api/auth/verify-email?token={token}&type={type}"
    html_content = f"""
    <html>
      <body>
        <p>Подтвердите ваш email, нажав на ссылку ниже:</p>
        <p><a href="{verification_link}">Подтвердить почту</a></p>
      </body>
    </html>
    """
    await send_email(email, "Подтверждение email", html_content, content_type="text/html")
