# deal_service/app/main.py
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from deal_service.app.routes import deals, feedback, chat


app = FastAPI(
    title="Deal_Model Service",
    description="Сервис управления сделками, отзывами и чатом"
)

# Подключение роутов
app.include_router(deals.router, prefix="/deal", tags=["deals"])
app.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])

app.mount("/static", StaticFiles(directory="static"), name="static")
