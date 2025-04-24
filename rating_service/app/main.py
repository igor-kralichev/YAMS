# rating_service/app/main.py
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from rating_service.app.routes import ratings

app = FastAPI(
    title="Rating Service",
    description="Сервис управления рейтингом компаний"
)

# Подключение роутов
app.include_router(ratings.router, prefix="/rating", tags=["rating"])

app.mount("/static", StaticFiles(directory="static"), name="static")
