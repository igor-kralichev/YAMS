from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from .routes import user, company

app = FastAPI(
    title="Lk Service",
    description="Сервис управления аккаунтами"
)

# Подключение локальных роутов
app.include_router(user.router, prefix="/user", tags=["user"])
app.include_router(company.router, prefix="/company", tags=["company"])

app.mount("/static", StaticFiles(directory="static"), name="static")
