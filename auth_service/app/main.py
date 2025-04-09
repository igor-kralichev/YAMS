from fastapi import FastAPI
from .routes import auth, user, company  # Локальные роуты


app = FastAPI(
    title="Auth Service",
    description="Сервис аутентификации и управления аккаунтами"
)

# Подключение локальных роутов (без префикса /api)
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(user.router, prefix="/users", tags=["users"])
app.include_router(company.router, prefix="/companies", tags=["companies"])