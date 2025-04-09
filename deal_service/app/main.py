# deal_service/app/main.py
from fastapi import FastAPI
from .routes import deals, feedback, chat


app = FastAPI(
    title="Deal_Model Service",
    description="Сервис управления сделками, отзывами и чатом"
)

# Подключение роутов
app.include_router(deals.router, prefix="/deal", tags=["deals"])
app.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])

