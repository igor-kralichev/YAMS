from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import secrets

from app.core.config import settings
from app.db.models import RefreshToken, Company
from app.db.session import get_db
from app.db.models.user import User
from app.schemas.company import CompanyCreate, Company as CompanySchema
from app.schemas.user import UserCreate, User as UserSchema
from app.core.security import *
from app.services.auth import get_user_by_email, get_company_by_email
from app.services.email import send_email

router = APIRouter()

# Фоновая задача для отправки email
async def send_verification_email(email: str, token: str, type: str):
    verification_link = f"{settings.APP_URL}/api/auth/verify-email?token={token}&type={type}"
    html_content = f"""
    <html>
      <body>
        <p>Подтвердите ваш email, нажав на ссылку ниже:</p>
        <p><a href="{verification_link}">Подтвердить почту</a></p>
      </body>
    </html>
    """
    await send_email(email, "Подтверждение email", html_content, content_type="text/html")

# Регистрация пользователя
@router.post("/register/user", response_model=UserSchema)
async def register(
    user: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован как пользователь")

    db_company = get_company_by_email(db, email=user.email)
    if db_company:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован как компания")

    hashed_password = get_password_hash(user.password)
    verification_token = secrets.token_urlsafe(32)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        is_verified=False,
        verification_token=verification_token
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    background_tasks.add_task(send_verification_email, user.email, verification_token, "user")
    return db_user

# Регистрация компании
@router.post("/register/company", response_model=CompanySchema)
async def register_company(
    company: CompanyCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_company = get_company_by_email(db, email=company.email)
    if db_company:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован как компания")

    db_user = get_user_by_email(db, email=company.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован как пользователь")

    hashed_password = get_password_hash(company.password)
    verification_token = secrets.token_urlsafe(32)
    db_company = Company(
        email=company.email,
        hashed_password=hashed_password,
        name=company.name,
        is_verified=False,
        verification_token=verification_token
    )
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    background_tasks.add_task(send_verification_email, company.email, verification_token, "company")
    return db_company

# Авторизация пользователя
@router.post("/login/user")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверные учетные данные")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email не подтверждён")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Пользователь заблокирован")

    # Генерация токенов
    access_token = create_access_token(data={"sub": user.email, "type": "user"})
    refresh_token = create_refresh_token()
    expires_at = get_refresh_token_expiry()

    # Сохранение refresh-токена в базе
    db_refresh_token = RefreshToken(
        token=refresh_token,
        user_id=user.id,
        expires_at=expires_at
    )
    db.add(db_refresh_token)
    db.commit()

    # Возвращаем оба токена
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

# Авторизация компании
@router.post("/login/company")
async def login_company(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    company = get_company_by_email(db, email=form_data.username)
    if not company or not verify_password(form_data.password, company.hashed_password):
        raise HTTPException(status_code=401, detail="Неверные учетные данные")
    if not company.is_verified:
        raise HTTPException(status_code=403, detail="Email не подтверждён")
    if not company.is_active:
        raise HTTPException(status_code=403, detail="Компания заблокирована")

    access_token = create_access_token(data={"sub": company.email, "type": "company"})
    refresh_token = create_refresh_token()
    expires_at = get_refresh_token_expiry()

    db_refresh_token = RefreshToken(
        token=refresh_token,
        company_id=company.id,
        expires_at=expires_at
    )
    db.add(db_refresh_token)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

# Подтверждение email
@router.get("/verify-email")
async def verify_email(token: str, type: str, db: Session = Depends(get_db)):
    if type == "user":
        user = db.query(User).filter(User.verification_token == token).first()
        if not user:
            raise HTTPException(status_code=400, detail="Недействительный токен")
        user.is_verified = True
        user.verification_token = None
        db.commit()
        return {"message": "Email пользователя успешно подтверждён"}
    elif type == "company":
        company = db.query(Company).filter(Company.verification_token == token).first()
        if not company:
            raise HTTPException(status_code=400, detail="Недействительный токен")
        company.is_verified = True
        company.verification_token = None
        db.commit()
        return {"message": "Email компании успешно подтверждён"}
    else:
        raise HTTPException(status_code=400, detail="Неверный тип")

# Обновление access_token, используя refresh_token
@router.post("/refresh")
def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    db_refresh_token = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
    if not db_refresh_token or db_refresh_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Недействительный refresh-токен")

    if db_refresh_token.user_id:
        user = db_refresh_token.user
        new_access_token = create_access_token(data={"sub": user.email, "type": "user"})
        entity_id = user.id
        entity_type = "user"
    elif db_refresh_token.company_id:
        company = db_refresh_token.company
        new_access_token = create_access_token(data={"sub": company.email, "type": "company"})
        entity_id = company.id
        entity_type = "company"
    else:
        raise HTTPException(status_code=400, detail="Недействительный refresh-токен")

    db.delete(db_refresh_token)
    new_refresh_token = create_refresh_token()
    new_expires_at = get_refresh_token_expiry()
    if entity_type == "user":
        db_new_refresh_token = RefreshToken(
            token=new_refresh_token,
            user_id=entity_id,
            expires_at=new_expires_at
        )
    else:
        db_new_refresh_token = RefreshToken(
            token=new_refresh_token,
            company_id=entity_id,
            expires_at=new_expires_at
        )
    db.add(db_new_refresh_token)
    db.commit()

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout(
    refresh_token: str = Header(...),  # Принимаем refresh_token из заголовка
    db: Session = Depends(get_db)
):
    db_refresh_token = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
    if not db_refresh_token:
        raise HTTPException(status_code=400, detail="Недействительный refresh-токен")

    db.delete(db_refresh_token)
    db.commit()
    return {"message": "Успешный выход из аккаунта"}