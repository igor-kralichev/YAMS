# deal_service/app/main.py
from fastapi import FastAPI


app = FastAPI(
    title="Rating Service",
    description="Сервис управления рейтингом"
)

# Подключение роутов
