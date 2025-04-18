import asyncio
import json
from typing import Optional
import logging

from fastapi_csrf_protect.exceptions import CsrfProtectError
from redis.asyncio import Redis
from fastapi import FastAPI, Depends, Request, status, HTTPException, WebSocket, Query
from fastapi.security import OAuth2PasswordBearer
from fastapi_csrf_protect import CsrfProtect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi_limiter import FastAPILimiter
from httpx import AsyncClient, Timeout
from websockets import connect as websocket_connect
from websockets.exceptions import ConnectionClosed

from shared.core.config import settings
from shared.db.base import Base
from shared.db.seeds import run_all_seeds
from shared.db.session import engine

app = FastAPI(
    title="YAMS Gateway",
    description="API Gateway для YAMS",
    version="1.0.0"
)

logger = logging.getLogger(__name__)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить все домены
    allow_credentials=True,
    allow_methods=["*"],  # Разрешить все HTTP-методы
    allow_headers=["*"],  # Разрешить все заголовки
)

# Настройка CSRF
csrf_protect = CsrfProtect()
csrf_protect.load_config(lambda: [
    ("secret_key", settings.SECRET_KEY),
    ("cookie_samesite", "lax"),
    ("cookie_secure", False),
    ("cookie_domain", "localhost"),
    ("cookie_key", "csrftoken"),
])

# Подключение к Redis
redis_client = Redis(
    host=settings.REDIS_HOST,  # Например, "redis" (если в Docker)
    port=settings.REDIS_PORT,  # 6379
    db=settings.REDIS_DB       # 0
)

# URL микросервисов
SERVICE_URLS = {
    "auth": "http://localhost:8001",
    "deal": "http://localhost:8002",
    "rating": "http://localhost:8003",
    "lk": "http://localhost:8004",
    "admin": "http://localhost:8005"
}

# Создание таблиц при запуске
@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        # Запускаем синхронный метод create_all через run_sync
        await conn.run_sync(Base.metadata.create_all)
        await FastAPILimiter.init(redis_client)
    # Запуск сидинга
    await run_all_seeds()

# Функция зависимости
def get_csrf_protect():
    return csrf_protect


@app.api_route(
    "/api/admin/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    summary="Проксирование запросов к Admin Service",
    description="Переадресация запросов к Admin Service для управления пользователями, сделками и другими сущностями."
)
async def proxy_to_admin_service(request: Request, path: str):
    # Полный перехват и модификация URL
    full_path = str(request.url)
    admin_path = full_path.split("/api/admin/")[-1]

    # Заменяем пути к статическим файлам
    if admin_path.startswith("statics/"):
        target_url = f"{SERVICE_URLS['admin']}/{admin_path}"
    else:
        target_url = f"{SERVICE_URLS['admin']}/admin/{admin_path}"

    async with AsyncClient() as client:
        # Копируем все заголовки кроме Host
        headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}

        response = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            params=request.query_params,
            content=await request.body()
        )

        # Возвращаем ответ как есть
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.headers.get("content-type")
        )

# Маршрут для CSRF-токена (остаётся в Gateway)
@app.get(
    "/api/csrf-token",
    summary="Получение CSRF-токена",
    description="Генерирует и возвращает CSRF-токен для защиты от CSRF-атак.")
async def get_csrf_token(csrf: CsrfProtect = Depends(get_csrf_protect)):
    return {"csrf_token": csrf.generate_csrf_tokens()}


# Проксирование запросов к Auth Service
@app.api_route(
    "/api/auth/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    summary="Проксирование запросов к Auth Service",
    description=(
        "Переадресация на регистрацию, авторизацию\n"
        "Поддерживаемые пути:\n"
        "- POST /api/auth/login — авторизация пользователя\n"
        "- POST /api/auth/register/user — регистрация пользователя\n"
        "- POST /api/auth/register/company — регистрация пользователя\n"
        "- GET /api/auth/verify-email — верификация почты\n"
        "- POST /api/auth/verify-token — проверка токена\n"
        "- POST /api/auth/update-access-token — обновление access_token\n"
        "- POST /api/auth/logout — выход из аккаунта и удаление refresh_token\n"
    )
)
async def auth_proxy(request: Request, path: str):
    async with AsyncClient() as client:
        # Формируем URL для Auth Service
        url = f"{SERVICE_URLS['auth']}/auth/{path}"
        response = await client.request(
            method=request.method,
            url=url,
            headers=dict(request.headers),
            params=dict(request.query_params),
            content=await request.body()
        )
        # Логирование для отладки
        print(f"Response from auth service: {response.status_code}, {response.text}")

        try:
            return response.json()
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500,
                detail=f"Auth service error: {response.text}"
            )

# ЛК пользователя
@app.api_route(
    "/api/user/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    summary="Проксирование запросов к Auth Service",
    description=(
        "Переадресация на ЛК пользователя\n"
        "Поддерживаемые пути:\n"
        "- GET /api/user/me — просмотр данных текущего пользователя\n"
        "- PUT /api/user/me — обновление данных текущего пользователя\n"
        "- DELETE /api/user/me — удаление текущего пользователя\n"
        "- POST /api/user/change-password — смена пароля\n"
        "- POST /api/user/upload-photo — обновление фото\n"
    )
)
async def users_proxy(
        request: Request,
        path: str,
        csrf: CsrfProtect = Depends(get_csrf_protect)
):
    try:
        await csrf.validate_csrf(request)
    except CsrfProtectError:
        raise HTTPException(status_code=403, detail="Невалидный CSRF токен")

    async with AsyncClient() as client:
        url = f"{SERVICE_URLS['lk']}/user/{path}"
        response = await client.request(
            method=request.method,
            url=url,
            headers=dict(request.headers),
            params=dict(request.query_params),
            content=await request.body()
        )
        # Логирование для отладки
        print(f"Response from auth service: {response.status_code}, {response.text}")

        try:
            return response.json()
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500,
                detail=f"Auth service error: {response.text}"
            )

# ЛК компании
@app.api_route(
    "/api/company/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    summary="Проксирование запросов к Auth Service",
    description=(
        "Переадресация на ЛК компании\n"
        "Поддерживаемые пути:\n"
        "- GET /api/company/me — просмотр данных текущей компании\n"
        "- PUT /api/company/me — обновление данных текущей компании\n"
        "- DELETE /api/company/me — удаление текущей компании\n"
        "- POST /api/company/change-password — смена пароля\n"
        "- POST /api/company/upload-logo — обновление фото\n"
    )
)
async def companies_proxy(
        request: Request,
        path: str,
        csrf: CsrfProtect = Depends(get_csrf_protect)
):
    try:
        await csrf.validate_csrf(request)
    except CsrfProtectError:
        raise HTTPException(status_code=403, detail="Невалидный CSRF токен")

    async with AsyncClient() as client:
        url = f"{SERVICE_URLS['lk']}/company/{path}"
        response = await client.request(
            method=request.method,
            url=url,
            headers=dict(request.headers),
            params=dict(request.query_params),
            content=await request.body()
        )
        # Логирование для отладки
        print(f"Response from auth service: {response.status_code}, {response.text}")

        try:
            return response.json()
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500,
                detail=f"Auth service error: {response.text}"
            )

# Проксирование запросов к Rating Service
@app.api_route(
    "/api/rating/{path:path}",
    methods=["GET"],
    summary="Проксирование запросов к Rating Service",
    description=(
        "Переадресация запросов к Rating Service для получения рейтингов компаний.\n"
        "Поддерживаемые пути:\n"
        "- GET /api/rating/regions — получение списка регионов\n"
        "- GET /api/rating/industries — получение списка отраслей\n"
        "- GET /api/rating/companies — получение списка компаний с фильтрацией (требуется аутентификация)\n"
        "- GET /api/rating/companies/{company_id} — получение подробной информации о компании\n"
        "- GET /api/rating/ranking-vikor-companies — получение рейтинга компаний по VIKOR\n"
    )
)
async def rating_proxy(
    request: Request,
    path: str,
):

    async with AsyncClient() as client:
        url = f"{SERVICE_URLS['rating']}/rating/{path}"
        response = await client.request(
            method=request.method,
            url=url,
            headers=dict(request.headers),
            params=dict(request.query_params),
            content=await request.body()
        )
        # Логирование для отладки
        logger.info(f"Response from rating service: {response.status_code}, {response.text}")

        try:
            return response.json()
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Rating service error: {response.text}"
            )

# Проксирование запросов к Deal_Model Service
@app.api_route(
    "/api/deal/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    summary="Проксирование запросов к Deal Service",
    description=(
        "Переадресация на создание и прочие шалости со сделками\n"
        "Поддерживаемые пути:\n"
        "- GET /api/deal/regions — получение списка регионов (для фильтров)\n"
        "- GET /api/deal/deal-details — получение списка статусов сделок (активно, продано и т.д.)\n"
        "- GET /api/deal/deal-branches — получение списка отраслей (ИТ, сельское хозяйство и т.д.)\n"
        "- GET /api/deal/deal-types — получение списка типов сделок (продажа товара или услуга)\n"
        "- GET /api/deal/list — получение списка сделок (по умолчанию 50 сделок на страницу)\n"
        "- GET /api/deal/view-deal/{deal_id} — получение информации о конкретной сделке, включая количество покупателей и отзывов\n"
        "- POST /api/deal/create-deal — создание новой сделки (включая загрузку до 5 фотографий)\n"
        "- PUT /api/deal/update-deal/{deal_id} — обновление данных сделки (включая замену фотографий, максимум 5)\n"
        "- POST /api/deal/buy-deal/{deal_id} — покупка сделки (доступно только для сделок со статусом 'Активно')\n"
    )
)
async def deals_proxy(
        request: Request,
        path: str,
        csrf: CsrfProtect = Depends(get_csrf_protect)
):
    try:
        await csrf.validate_csrf(request)
    except CsrfProtectError:
        raise HTTPException(status_code=403, detail="Невалидный CSRF токен")

    async with AsyncClient() as client:
        url = f"{SERVICE_URLS['deal']}/deal/{path}"
        response = await client.request(
            method=request.method,
            url=url,
            headers=dict(request.headers),
            params=dict(request.query_params),
            content=await request.body()
        )
        # Логирование для отладки
        print(f"Response from auth service: {response.status_code}, {response.text}")

        try:
            return response.json()
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500,
                detail=f"Auth service error: {response.text}"
            )

# Чаты
@app.api_route(
    "/api/chat/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    summary="Проксирование запросов к Deal Service",
    description=(
        "Переадресация на чат (пока там только показ чатов, "
        "вебсокеты дальше для общения, они отдельно идут)\n"
        "Поддерживаемые пути:\n"
        "- GET /api/chat/my-chats — получение списка чатов текущего пользователя (продавца или покупателя)\n"
    )
)
async def chat_proxy(
        request: Request,
        path: str,
        csrf: CsrfProtect = Depends(get_csrf_protect)
):
    try:
        await csrf.validate_csrf(request)
    except CsrfProtectError:
        raise HTTPException(status_code=403, detail="Невалидный CSRF токен")

    async with AsyncClient() as client:
        url = f"{SERVICE_URLS['deal']}/chat/{path}"
        response = await client.request(
            method=request.method,
            url=url,
            headers=dict(request.headers),
            params=dict(request.query_params),
            content=await request.body()
        )
        # Логирование для отладки
        print(f"Response from auth service: {response.status_code}, {response.text}")

        try:
            return response.json()
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500,
                detail=f"Auth service error: {response.text}"
            )

# Отзывы
@app.api_route(
    "/api/feedback/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
    summary="Проксирование запросов к Deal Service",
    description=(
        "Переадресация на создание отзывов (если удаление, то, возможно, в админке будет)\n"
        "Поддерживаемые пути:\n"
        "- GET /api/feedback/{deal_id} — получение списка всех отзывов для указанной сделки\n"
        "- POST /api/feedback/create-feedback/{deal_id} — создание нового отзыва для сделки (с меткой is_purchaser для покупателей)\n"
    )
)
async def feedback_proxy(
        request: Request,
        path: str,
        csrf: CsrfProtect = Depends(get_csrf_protect)
):
    try:
        await csrf.validate_csrf(request)
    except CsrfProtectError:
        raise HTTPException(status_code=403, detail="Невалидный CSRF токен")
    
    async with AsyncClient() as client:
        url = f"{SERVICE_URLS['deal']}/feedback/{path}"
        response = await client.request(
            method=request.method,
            url=url,
            headers=dict(request.headers),
            params=dict(request.query_params),
            content=await request.body()
        )
        # Логирование для отладки
        print(f"Response from auth service: {response.status_code}, {response.text}")

        try:
            return response.json()
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500,
                detail=f"Auth service error: {response.text}"
            )

# Вебсокет чатов
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def verify_token(token: str) -> bool:
    timeout = Timeout(5.0)  # Таймаут 5 секунд
    async with AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(
                f"{SERVICE_URLS['auth']}/auth/verify-token",
                json={"token": token}
            )
            if response.status_code != 200:
                logger.error(f"Token verification failed: {response.text}")
                return False
            return True
        except Exception as e:
            logger.error(f"Auth service error: {str(e)}")
            return False


@app.websocket("/api/chat/ws/deals/{deal_id}/{consumer_id}")
async def websocket_proxy(
    websocket: WebSocket,
    deal_id: int,
    consumer_id: int,
    token: Optional[str] = Query(None)
):
    """
    WebSocket прокси для чатов сделок.

    Подключается к backend WebSocket серверу для общения в чате по конкретной сделке.
    Проверяет токен, пересылает сообщения в обе стороны и обрабатывает ошибки соединения.
    """
    await websocket.accept()

    # Получаем токен из заголовка (как в микросервисе)
    auth_header = websocket.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header else token

    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        # Формируем URL с учетом consumer_id
        backend_ws_url = f"ws://localhost:8002/chat/ws/deals/{deal_id}/{consumer_id}"

        async with websocket_connect(
            backend_ws_url,
            extra_headers=[("Authorization", f"Bearer {token}")],
            ping_timeout=20,
            close_timeout=10
        ) as backend_ws:

            async def forward():
                while True:
                    try:
                        message = await websocket.receive()
                        if message["type"] == "websocket.disconnect":
                            await backend_ws.close()
                            break
                        if "text" in message:
                            await backend_ws.send(message["text"])
                        elif "bytes" in message:
                            await backend_ws.send(message["bytes"])
                    except ConnectionClosed:
                        break
                    except Exception as e:
                        logger.error(f"Forward error: {str(e)}")
                        break

            async def backward():
                while True:
                    try:
                        data = await backend_ws.recv()
                        if isinstance(data, str):
                            await websocket.send_text(data)
                        elif isinstance(data, bytes):
                            await websocket.send_bytes(data)
                    except ConnectionClosed:
                        break
                    except Exception as e:
                        logger.error(f"Backward error: {str(e)}")
                        break

            async def ping_backend():
                """
                Пинг backend каждые 30 секунд.
                Если pong не получен в течение 10 секунд, считается, что сервер не отвечает.
                """
                while True:
                    try:
                        await asyncio.sleep(30)
                        # Отправляем ping и ждём pong
                        pong_waiter = await backend_ws.ping()
                        # Ждем pong не более 10 секунд
                        await asyncio.wait_for(pong_waiter, timeout=10)
                    except Exception:
                        logger.error("Сервер не отвечает на пинг, разрываем соединение")
                        # Если пинг не прошёл — вызываем исключение, чтобы завершить все задачи
                        raise Exception("Сервер не отвечает на пинг")

            # Запускаем одновременно пересылку сообщений и пинг
            tasks = [
                asyncio.create_task(forward()),
                asyncio.create_task(backward()),
                asyncio.create_task(ping_backend()),
            ]

            try:
                # Если любая из задач завершилась (например, из-за ошибки пинга),
                # завершаем все и переходим к закрытию соединения
                done, pending = await asyncio.wait(
                    tasks, return_when=asyncio.FIRST_EXCEPTION
                )
                # Если в завершённых задачах было исключение — пробрасываем его
                for task in done:
                    if task.exception():
                        raise task.exception()
            finally:
                for task in tasks:
                    task.cancel()
                try:
                    await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
                except Exception:
                    pass

    except ConnectionClosed:
        logger.info("Connection closed normally")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except Exception:
            pass

# Корневой эндпоинт
@app.get(
    "/",
    summary="Просто так",
    description=(
            "Ну хз, просто начало приложения в конце файла"
    )
)
async def root():
    return {"message": "Welcome to YAMS API"}