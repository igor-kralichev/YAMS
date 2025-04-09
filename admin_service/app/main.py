# admin_service/app/main.py
from fastapi import FastAPI
from sqladmin import Admin
from sqlalchemy.sql import text
from starlette.middleware.sessions import SessionMiddleware

from shared.core.config import settings
from shared.db.session import engine, AsyncSessionLocal
from admin_service.app.routes.admin import admin_router, AccountAdmin, DealAdmin, FeedbackAdmin, AdminAuth

app = FastAPI(
    title="Admin Service",
    description="Админская панель для управления пользователями, сделками и другими сущностями."
)

# Добавляем middleware для работы с сессиями
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Проверка подключения к базе данных при запуске
@app.on_event("startup")
async def startup_event():
    from shared.db.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        try:
            await session.execute(text("SELECT 1"))
            print("Связь с бд установлена")
        except Exception as e:
            print(f"Неудачное подключение к бд: {str(e)}")
            raise e

# Инициализация админки с авторизацией
print("Инициализация SQLAdmin с base_url=/admin")
try:
    admin = Admin(
        app,
        engine,
        authentication_backend=AdminAuth(secret_key=settings.SECRET_KEY),
        base_url="/admin",
        templates_dir="admin_service/templates"
    )
except Exception as e:
    print(f"Ошибка инициализации SQLAdmin: {str(e)}")
    raise e

# Регистрация представлений
try:
    print("Регистрация представлений аккаунтов")
    admin.add_view(AccountAdmin)
    print("Регистрация представлений сделок")
    admin.add_view(DealAdmin)
    print("Регистрация представлений отзывов")
    admin.add_view(FeedbackAdmin)
except Exception as e:
    print(f"Ошибка регистрации представлений: {str(e)}")
    raise e

app.include_router(admin_router)