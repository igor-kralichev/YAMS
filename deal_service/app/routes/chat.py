import asyncio
import json
import logging
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect,WebSocketException, APIRouter, Depends, HTTPException, status
from collections import defaultdict

from jose import JWTError, jwt
from redis.asyncio import Redis
from sqlalchemy import select, func, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, aliased

from deal_service.app.services.chat import get_token_from_header, verify_token
from shared.db.models import Account_Model, Deal_Model, Message_Model
from shared.db.models.deal_consumers import DealConsumers as deal_consumers
from shared.db.schemas.chat import ChatSchema
from shared.db.session import get_db
from shared.services.auth import get_current_account

# Хранилище активных подключений
active_connections = defaultdict(dict)
logger = logging.getLogger(__name__)
redis_client = Redis(host="localhost", port=6379, db=0)
router = APIRouter()


@router.get(
    "/my-chats",
    response_model=list[ChatSchema],
    summary="GET на получение чатов для пользователя",
    description=(
        "Возвращает список чатов для текущего пользователя (продавца или любого пользователя). "
        "Каждый чат соответствует паре сделка-пользователь."
    )
)
async def get_user_chats(
    db: AsyncSession = Depends(get_db),
    current_account: Account_Model = Depends(get_current_account)
):
    try:
        # Подзапрос для получения последнего сообщения для каждой пары deal_id и consumer_id
        last_msg_subq = (
            select(
                Message_Model.deal_id,
                func.coalesce(Message_Model.sender_id, Message_Model.recipient_id).label("consumer_id"),
                func.max(Message_Model.created_at).label("last_msg_time")
            )
            .where(
                or_(
                    Message_Model.sender_id != current_account.id,
                    Message_Model.recipient_id != current_account.id
                )
            )
            .group_by(
                Message_Model.deal_id,
                func.coalesce(Message_Model.sender_id, Message_Model.recipient_id)
            )
            .subquery()
        )

        Seller = aliased(Account_Model, name="seller")
        Consumer = aliased(Account_Model, name="consumer")

        # Подзапрос для проверки, является ли пользователь покупателем
        purchase_subq = (
            select(deal_consumers.c.deal_id, deal_consumers.c.consumer_id)
            .subquery()
        )

        # Основной запрос
        query = (
            select(
                Deal_Model.id.label("deal_id"),
                func.coalesce(Message_Model.sender_id, Message_Model.recipient_id).label("consumer_id"),
                Deal_Model.name_deal,
                Message_Model.content.label("last_message"),
                last_msg_subq.c.last_msg_time,
                Seller.email.label("seller_email"),
                Consumer.email.label("consumer_email"),
                (purchase_subq.c.consumer_id != None).label("is_purchaser")
            )
            .join(Message_Model, Deal_Model.id == Message_Model.deal_id)
            .outerjoin(
                last_msg_subq,
                (Deal_Model.id == last_msg_subq.c.deal_id) &
                (func.coalesce(Message_Model.sender_id, Message_Model.recipient_id) == last_msg_subq.c.consumer_id) &
                (Message_Model.created_at == last_msg_subq.c.last_msg_time)
            )
            .outerjoin(Seller, Deal_Model.seller_id == Seller.id)
            .outerjoin(Consumer, func.coalesce(Message_Model.sender_id, Message_Model.recipient_id) == Consumer.id)
            .outerjoin(
                purchase_subq,
                (Deal_Model.id == purchase_subq.c.deal_id) &
                (func.coalesce(Message_Model.sender_id, Message_Model.recipient_id) == purchase_subq.c.consumer_id)
            )
            .where(
                or_(
                    Deal_Model.seller_id == current_account.id,
                    Message_Model.sender_id == current_account.id,
                    Message_Model.recipient_id == current_account.id
                )
            )
            .distinct(Deal_Model.id, func.coalesce(Message_Model.sender_id, Message_Model.recipient_id))
            .order_by(
                Deal_Model.id,
                func.coalesce(Message_Model.sender_id, Message_Model.recipient_id),
                desc(last_msg_subq.c.last_msg_time)
            )
        )

        result = await db.execute(query)
        chats = result.all()

        if not chats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Чаты не найдены"
            )

        return [
            ChatSchema(
                deal_id=chat.deal_id,
                consumer_id=chat.consumer_id,
                name_deal=chat.name_deal,
                last_message=chat.last_message,
                last_message_at=chat.last_msg_time,
                participants={
                    "seller": chat.seller_email if chat.seller_email else "Удаленный аккаунт",
                    "consumer": chat.consumer_email if chat.consumer_email else "Удаленный аккаунт"
                },
                is_purchaser=bool(chat.is_purchaser)
            )
            for chat in chats
        ]

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении чатов: {str(e)}"
        )



@router.websocket("/ws/deals/{deal_id}/{consumer_id}")
async def websocket_chat(
    websocket: WebSocket,
    deal_id: int,
    consumer_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket для двухстороннего чата по сделке между продавцом и любым пользователем.
    Подключает пользователя к WebSocket-чату, соответствующему конкретной сделке и пользователю.
    Пересылает сообщения между продавцом и пользователем в режиме реального времени.
    """
    pubsub = None
    redis_task = None
    ping_task = None
    current_account = None
    redis_key = f"deal:{deal_id}:consumer:{consumer_id}:users"

    try:
        # Шаг 1: Получение токена и проверка
        token = await get_token_from_header(websocket)
        payload = await verify_token(token)

        # Шаг 2: Получение аккаунта
        async with db.begin():
            account_id = int(payload["sub"])
            current_account = await db.get(Account_Model, account_id)
            if not current_account:
                raise WebSocketException(
                    code=status.WS_1008_POLICY_VIOLATION,
                    reason="Аккаунт не найден"
                )

        # Шаг 3: Проверка сделки
        async with db.begin():
            deal_res = await db.execute(
                select(Deal_Model)
                .where(Deal_Model.id == deal_id)
                .options(joinedload(Deal_Model.seller))
            )
            deal = deal_res.scalar_one_or_none()

            if not deal:
                raise WebSocketException(
                    code=status.WS_1008_POLICY_VIOLATION,
                    reason="Сделка не найдена"
                )

            # Проверяем, что consumer_id — это существующий пользователь
            consumer = await db.get(Account_Model, consumer_id)
            if not consumer:
                raise WebSocketException(
                    code=status.WS_1008_POLICY_VIOLATION,
                    reason="Указанный пользователь не найден"
                )

            # Проверяем, что текущий пользователь — либо продавец, либо указанный пользователь
            participants = {deal.seller_id, consumer_id}
            if current_account.id not in participants:
                raise WebSocketException(
                    code=status.WS_1008_POLICY_VIOLATION,
                    reason="Отказано в доступе"
                )

        # Шаг 4: Принятие соединения
        await websocket.accept()

        # Запускаем отправку ping-пакетов в отдельной задаче
        async def send_ping():
            while True:
                try:
                    await asyncio.sleep(30)
                    await websocket.send_json({"type": "ping"})
                except Exception as e:
                    logger.error(f"Ping error: {str(e)}")
                    break

        ping_task = asyncio.create_task(send_ping())

        # Шаг 5: Загрузка истории сообщений (исправленный запрос)
        async with db.begin():
            messages_result = await db.execute(
                select(Message_Model)
                .where(Message_Model.deal_id == deal_id)
                .where(Message_Model.consumer_id == consumer_id)
                .where(
                    (Message_Model.sender_id.in_([deal.seller_id, consumer_id])) &
                    (Message_Model.recipient_id.in_([deal.seller_id, consumer_id]))
                )
                .order_by(Message_Model.created_at.asc())
            )
            messages = messages_result.scalars().all()

        # Отправка истории
        for msg in messages:
            try:
                await websocket.send_json(msg.to_dict())
            except Exception as e:
                logger.error(f"Ошибка при отправке истории: {str(e)}")
                break

        # Шаг 6: Регистрация подключения
        active_connections.setdefault((deal_id, consumer_id), {})[current_account.id] = websocket
        await redis_client.sadd(redis_key, current_account.id)

        # Шаг 7: Подписка на Redis
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(f"deal:{deal_id}:consumer:{consumer_id}")

        async def redis_listener():
            while True:
                try:
                    message = await pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=1.0
                    )
                    if message:
                        try:
                            await websocket.send_json(json.loads(message["data"]))
                        except Exception as e:
                            logger.error(f"Ошибка отправки сообщения из Redis: {str(e)}")
                            break
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"Redis error: {str(e)}")
                    break

        redis_task = asyncio.create_task(redis_listener())

        # Шаг 8: Обработка сообщений
        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)

                # Валидация
                if "content" not in message_data:
                    await websocket.send_json({"error": "Отсутствует 'content'"})
                    continue

                content = message_data["content"]
                if not isinstance(content, str) or len(content) > 1000:
                    await websocket.send_json({"error": "Недопустимое содержимое"})
                    continue

                # Определение получателя
                recipient_id = (
                    consumer_id
                    if current_account.id == deal.seller_id
                    else deal.seller_id
                )

                # Сохранение сообщения
                async with db.begin():
                    new_message = Message_Model(
                        sender_id=current_account.id,
                        recipient_id=recipient_id,
                        content=content,
                        deal_id=deal_id,
                        consumer_id=consumer_id  # Явно передаем consumer_id из URL
                    )
                    db.add(new_message)
                    await db.flush()  # Получаем ID без коммита
                    await db.refresh(new_message)  # Обновляем объект

                # Публикация в Redis
                message_dict = new_message.to_dict()
                await redis_client.publish(f"deal:{deal_id}:consumer:{consumer_id}", json.dumps(message_dict))

            except WebSocketDisconnect:
                logger.info("Клиент отключен")
                break
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Неверный JSON"})
            except Exception as e:
                logger.error(f"Ошибка: {str(e)}")
                await websocket.send_json({"error": "Ошибка сервера"})

    except WebSocketException as e:
        logger.error(f"Ошибка аутентификации: {e.reason}")
        try:
            await websocket.close(code=e.code, reason=e.reason)
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except Exception:
            pass
    finally:
        if ping_task:
            ping_task.cancel()
        if redis_task:
            redis_task.cancel()
        if pubsub:
            try:
                await pubsub.unsubscribe(f"deal:{deal_id}:consumer:{consumer_id}")
            except Exception:
                pass
        if current_account:
            active_connections.get((deal_id, consumer_id), {}).pop(current_account.id, None)
            await redis_client.srem(redis_key, current_account.id)
        await db.close()
