from fastapi import FastAPI, Depends
from fastapi_csrf_protect import CsrfProtect
from app.api.routes import auth, company, rating, user
from app.db.session import engine
from app.db.base import Base
from app.core.config import settings

app = FastAPI(
    title="YAMS API",
    description="API for YAMS platform",
    version="1.0.0"
)

# Настройка CSRF-защиты
csrf_protect = CsrfProtect()
csrf_protect.load_config(lambda: [
    ("secret_key", settings.SECRET_KEY),
    ("cookie_samesite", "lax"),
    ("cookie_secure", False),
    ("cookie_domain", "localhost"),
    ("cookie_key", "csrftoken"),
])


# Маршрут для получения CSRF-токена
@app.get("/csrf-token")
async def get_csrf_token(csrf_protect: CsrfProtect = Depends()):
    return {"csrf_token": csrf_protect.generate_csrf_tokens()}

# Создание таблиц при запуске приложения
@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)

# Подключение роутов
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

app.include_router(user.router, prefix="/api/users", tags=["users"])

app.include_router(company.router, prefix="/api/companies", tags=["companies"])

@app.get("/")
async def root():
    return {"message": "Welcome to YAMS API"}