from fastapi import FastAPI
from .routes import auth  # Локальные роуты

app = FastAPI(
    title="Auth Service",
    description="Сервис аутентификации"
)

# Подключение локальных роутов (без префикса /api)
app.include_router(auth.router, prefix="/auth", tags=["auth"])
