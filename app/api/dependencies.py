from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.company import Company  # Добавляем модель компании
from app.services.auth import get_user_by_email, get_company_by_email  # Добавляем функцию для компаний

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        entity_type: str = payload.get("type")
        if email is None:
            raise HTTPException(status_code=401, detail="Недействительный токен: отсутствует email")
        if entity_type != "user":
            raise HTTPException(status_code=403, detail="Доступ запрещён: токен не принадлежит пользователю")
    except JWTError:
        raise HTTPException(status_code=401, detail="Недействительный токен")

    user = get_user_by_email(db, email=email)
    if user is None:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Пользователь заблокирован")
    return user

def get_current_company(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Company:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        entity_type: str = payload.get("type")
        if email is None:
            raise HTTPException(status_code=401, detail="Недействительный токен: отсутствует email")
        if entity_type != "company":
            raise HTTPException(status_code=403, detail="Доступ запрещён: токен не принадлежит компании")
    except JWTError:
        raise HTTPException(status_code=401, detail="Недействительный токен")

    company = get_company_by_email(db, email=email)
    if company is None:
        raise HTTPException(status_code=401, detail="Компания не найдена")
    if not company.is_active:
        raise HTTPException(status_code=403, detail="Компания заблокирована")
    return company
def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    return current_user