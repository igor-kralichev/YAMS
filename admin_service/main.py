# deal_service/app/main.py
from fastapi import FastAPI


app = FastAPI(
    title="Admin Service",
    description="Микросервис админской части"
)

# Подключение роутов
