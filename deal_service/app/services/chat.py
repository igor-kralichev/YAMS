from datetime import datetime

from aiosmtplib import status
from jose import jwt, JWTError
from starlette.websockets import WebSocket
from websockets.exceptions import WebSocketException

from shared.core.config import settings


async def get_token_from_header(websocket: WebSocket) -> str:
    auth_header = websocket.headers.get("Authorization")
    if not auth_header:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Заголовок авторизации отсутствует"
        )

    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Недопустимая схема аутентификации"
            )
        return token
    except ValueError:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Недопустимый формат заголовка авторизации"
        )


async def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        # Дополнительная ручная проверка срока действия
        expire_timestamp = payload.get("exp")
        if not expire_timestamp:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Срок действия токена не истек"
            )

        if datetime.utcnow() > datetime.fromtimestamp(expire_timestamp):
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Срок действия токена истек"
            )

        return payload
    except JWTError as e:
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason=f"Недопустимый токен: {str(e)}"
        )