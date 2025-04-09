# admin_service/app/routes/admin.py
import asyncio

from fastapi import APIRouter, HTTPException, status
from sqladmin import ModelView, action
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import select, update, cast, Integer
from jose import JWTError, jwt
from fastapi import Request
import logging

from starlette.responses import RedirectResponse

from shared.db.session import AsyncSessionLocal
from shared.db.models import Account_Model, Deal_Model, Feedback_Model, DealDetail, DealTypes, DealBranch, Region
from shared.core.config import settings
from shared.services.email import send_email

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

admin_router = APIRouter()

# Кастомный бэкенд авторизации для SQLAdmin
class AdminAuth(AuthenticationBackend):
    def __init__(self, secret_key: str):
        super().__init__(secret_key=secret_key)

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
        client_ip = request.client.host

        if not username or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Логин или пароль неверный"
            )

        # Проверяем, существует ли пользователь с таким email и ролью admin
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Account_Model)
                .where(Account_Model.email == username)
                .where(Account_Model.role == "admin")
                .where(Account_Model.is_active.is_(True))
            )
            admin_user = result.scalar_one_or_none()

            if not admin_user:
                logger.warning(f"Неудачная попытка входа с IP {client_ip}: пользователь {username} не найден или не администратор")
                return False

                # Проверяем пароль
            from shared.services.auth import verify_password
            if not verify_password(password, admin_user.hashed_password):
                logger.warning(f"Неудачная попытка входа с IP {client_ip}: неверный пароль для пользователя {username}")
                return False

            # Генерируем JWT-токен
            token_data = {"sub": str(admin_user.id)}
            token = jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

            # Сохраняем токен в сессии
            request.session.update({"token": token})
            logger.info(f"Администратор {username} успешно вошёл с IP {client_ip}")
            return True

    async def logout(self, request: Request) -> bool:
            client_ip = request.client.host  # Получаем IP-адрес клиента
            # Очищаем сессию при выходе
            request.session.clear()
            logger.info(f"Администратор вышел из аккаунта с IP {client_ip}")
            return True


    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token:
            logger.warning("Aутентификация не пройдена: нет токена для сессии")
            return False

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            account_id = payload.get("sub")
            if not account_id:
                logger.warning("Aутентификация не пройдена: передан невалидный токен")
                return False

            # Проверяем, что пользователь всё ещё существует и является админом
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(Account_Model)
                    .where(Account_Model.id == int(account_id))
                    .where(Account_Model.role == "admin")
                    .where(Account_Model.is_active.is_(True))
                )
                admin_user = result.scalar_one_or_none()

                if not admin_user:
                    logger.warning(f"Аутентификация не пройдена: пользователь {account_id} не найден или не администратор")
                    return False

            return True
        except JWTError as e:
            logger.error(f"Аутентификация не пройдена: JWT ошибка - {str(e)}")
            return False


# Представления для моделей
class AccountAdmin(ModelView, model=Account_Model):
    column_list = ["id", "email", "role", "is_active", "is_verified", "created_at"]
    column_searchable_list = ["email"]
    column_filters = ["role", "is_active"]
    page_size = 20
    name = "Пользователь"
    name_plural = "Пользователи"

    async def _update_active_status(self, request: Request, pks: list, is_active: bool, action: str) -> dict:
        """
        Вспомогательный метод для обновления статуса is_active и логирования действия.

        :param request: HTTP-запрос
        :param pks: Список ID пользователей
        :param is_active: Новое значение для is_active (True/False)
        :param action: Описание действия для логов ("деактивировал"/"активировал")
        :return: Сообщение об успехе
        """
        client_ip = request.client.host  # Получаем IP-адрес клиента
        try:
            async with AsyncSessionLocal() as db:
                # Получаем пользователей для уведомления
                users = (await db.execute(
                    select(Account_Model).where(cast(Account_Model.id, Integer).in_(pks))
                )).scalars().all()

                # Обновляем is_active
                await db.execute(
                    update(Account_Model)
                    .where(cast(Account_Model.id, Integer).in_(pks))
                    .values(is_active=is_active)
                )
                await db.commit()

                # Логируем
                token = request.session.get("token")
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                admin_id = payload.get("sub")
                logger.info(f"Администратор {admin_id} {action} пользователей с ID {pks} с IP {client_ip}")

                # Отправляем уведомления
                for user in users:
                    subject = "Ваш аккаунт был заблокирован" if not is_active else "Ваш аккаунт был разблокирован"
                    body = (
                        "Ваш аккаунт был заблокирован администратором. "
                        "Если это ошибка, пожалуйста, свяжитесь с поддержкой."
                    ) if not is_active else (
                        "Ваш аккаунт был разблокирован администратором. "
                        "Теперь вы можете снова использовать все функции приложения."
                    )
                    asyncio.create_task(send_email(to_email=user.email, subject=subject, body=body))
                return {"message": f"{action.capitalize()} {len(pks)} пользователей"}
        except JWTError:
            logger.error(f"Ошибка декодирования JWT-токена при выполнении действия с IP {client_ip}")
            return {"message": "Ошибка авторизации"}
        except Exception as e:
            logger.error(f"Ошибка при {action} пользователей с IP {client_ip}: {str(e)}")
            return {"message": f"Ошибка: {str(e)}"}

    @action(
        name="deactivate",
        label="Деактивировать",
        add_in_list=True
    )
    async def bulk_deactivate(self, request: Request):
        pks = [int(pk) for pk in request.query_params.getlist("pks")]
        result = await self._update_active_status(request, pks, is_active=False, action="деактивировал")
        message = result.get("message", "Операция выполнена успешно")
        flash(request, message, category="success" if "Ошибка" not in message else "error")
        referer = request.headers.get("referer")
        return RedirectResponse(url=referer or request.url.path, status_code=303)

    @action(
        name="activate",
        label="Активировать",
        add_in_list=True
    )
    async def bulk_activate(self, request: Request):
        pks = [int(pk) for pk in request.query_params.getlist("pks")]
        result = await self._update_active_status(request, pks, is_active=True, action="активировал")
        message = result.get("message", "Активация выполнена успешно")
        flash(request, message, category="success" if "Ошибка" not in message else "error")
        referer = request.headers.get("referer")
        return RedirectResponse(url=referer or request.url.path, status_code=303)

    async def on_model_change(self, data, model, is_created, request):
        client_ip = request.client.host
        token = request.session.get("token")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        admin_id = payload.get("sub")
        action = "создал" if is_created else "изменил"
        logger.info(f"Администратор {admin_id} {action} пользователя {model.email} с IP {client_ip}")
        await super().on_model_change(data, model, is_created, request)

# Функция для установки flash-сообщения в сессии
def flash(request: Request, message: str, category: str = "info"):
    request.session["flash_message"] = {"message": message, "category": category}

# Вспомогательная функция для получения flash-сообщений
def get_flash(request: Request):
    message = request.session.pop("flash_message", None)
    return message

# Класс для администрирования сделок
class DealAdmin(ModelView, model=Deal_Model):
    column_list = ["id", "name_deal", "seller_id", "total_cost", "status", "created_at"]
    column_searchable_list = ["name_deal"]
    column_filters = ["status", "seller_id"]
    page_size = 20
    name = "Сделка"
    name_plural = "Сделки"

    # Асинхронный метод, который вызывается при удалении модели
    async def on_model_delete(self, model, request: Request) -> None:
        # model.seller — продавец, связанный со сделкой
        if model.seller and model.seller.email:
            subject = f"Ваша сделка '{model.name_deal}' была удалена"
            body = f"Уведомляем вас, что ваша сделка '{model.name_deal}' была удалена из-за нарушений правил сообщества."
            asyncio.create_task(send_email(to_email=model.seller.email, subject=subject, body=body))

# Класс для администрирования отзывов
class FeedbackAdmin(ModelView, model=Feedback_Model):
    column_list = ["id", "deal_id", "author_id", "stars", "details", "is_purchaser", "created_at"]
    column_searchable_list = ["details"]
    column_filters = ["stars", "is_purchaser"]
    page_size = 20
    name = "Отзыв"
    name_plural = "Отзывы"

    # Асинхронный метод для обработки удаления отзыва
    async def on_model_delete(self, model, request: Request) -> None:
        # model.deal – ссылка на сделку, на которую оставлен отзыв
        # model.author — автор отзыва
        if model.deal and model.author and model.author.email:
            subject = f"Ваш отзыв на сделку '{model.deal.name_deal}' был удалён"
            body = f"Ваш отзыв на сделку '{model.deal.name_deal}' был удалён из-за нарушений правил сообщества."
            asyncio.create_task(send_email(to_email=model.author.email, subject=subject, body=body))

# Класс для администрирования регионов
class RegionAdmin(ModelView, model=Region):
    column_list = ["id", "name"]
    column_searchable_list = ["name"]
    page_size = 20
    name = "Регион"
    name_plural = "Регионы"

# Класс для администрирования отраслей сделок
class DealBranchAdmin(ModelView, model=DealBranch):
    column_list = ["id", "name"]
    column_searchable_list = ["name"]
    page_size = 20
    name = "Отрасль сделки"
    name_plural = "Отрасли сделок"

# Класс для администрирования типов сделок
class DealTypesAdmin(ModelView, model=DealTypes):
    column_list = ["id", "name"]
    column_searchable_list = ["name"]
    page_size = 20
    name = "Тип сделки"
    name_plural = "Типы сделок"

# Класс для администрирования деталей сделок
class DealDetailAdmin(ModelView, model=DealDetail):
    column_list = ["id", "detail"]
    column_searchable_list = ["detail"]
    page_size = 20
    name = "Деталь сделки"
    name_plural = "Детали сделок"