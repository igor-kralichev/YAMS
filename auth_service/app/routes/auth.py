from fastapi import APIRouter, status, Depends, HTTPException, BackgroundTasks, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import secrets
from datetime import datetime

from shared.services.auth import get_current_account
from shared.db.models.refresh_tokens import RefreshToken
from shared.db.models.accounts import Account_Model
from shared.db.models.companies import Company_Model
from shared.db.models.users import User_Model

from shared.db.session import get_db
from shared.db.schemas.company import CompanyCreate, Company as CompanySchema
from shared.db.schemas.user import UserCreate, User as UserSchema
from shared.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, get_refresh_token_expiry
from auth_service.app.services.auth import get_account_by_email, send_verification_email, verify_token

router = APIRouter()


# Регистрация пользователя
@router.post(
    "/register/user",
    response_model=UserSchema,
    summary="POST запрос на регистрацию для пользователя",
    description=(
            "Тут добавляется инфа в 2 таблицы: accounts общая для авторизации, остальное в users"
    )
)
async def register_user(
        user: UserCreate,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db)
):
    # Проверяем, существует ли аккаунт с таким email
    existing_account = await get_account_by_email(db, user.account.email)
    if existing_account:
        raise HTTPException(
            status_code=400,
            detail="Email уже зарегистрирован"
        )

    hashed_password = get_password_hash(user.account.password)
    verification_token = secrets.token_urlsafe(32)

    # Создаём аккаунт для пользователя
    db_account = Account_Model(
        email=user.account.email,
        hashed_password=hashed_password,
        phone_num=user.account.phone_num,
        region_id=user.account.region_id,
        is_active=True,
        is_verified=False,
        verification_token=verification_token,
        role="user"
    )

    db_user = User_Model(
        fullname=user.fullname,
        photo_url=user.photo_url,
        account=db_account
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user, attribute_names=["account"])  # Явно обновляем связь

    background_tasks.add_task(send_verification_email, user.account.email, verification_token, "user")

    return db_user


# Регистрация компании
@router.post(
    "/register/company",
    response_model=CompanySchema,
    summary="POST запрос на регистрацию для компании",
    description=(
            "Аналогично users, только для компании"
    )
)
async def register_company(
        company: CompanyCreate,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db)
):
    # Проверяем, существует ли аккаунт с таким email
    existing_account = await get_account_by_email(db, company.account.email)
    if existing_account:
        raise HTTPException(
            status_code=400,
            detail="Email уже зарегистрирован"
        )

    # Хэшируем пароль
    hashed_password = get_password_hash(company.account.password)

    # Генерируем токен верификации
    verification_token = secrets.token_urlsafe(32)

    # Создаем аккаунт компании
    db_account = Account_Model(
        email=company.account.email,
        hashed_password=hashed_password,
        phone_num=company.account.phone_num,
        region_id=company.account.region_id,
        is_active=True,
        is_verified=False,
        verification_token=verification_token,
        role="company"
    )

    # Создаем компанию и связываем с аккаунтом
    db_company = Company_Model(
        name=company.name,
        description=company.description,
        slogan=company.slogan,
        address=company.address,
        logo_url=company.logo_url,
        employees=company.employees,
        year_founded=company.year_founded,
        website=company.website,
        account=db_account  # Связываем аккаунт
    )

    # Сохраняем в базе
    db.add(db_company)
    await db.commit()
    await db.refresh(db_company, ["account"])  # Обновляем связь с аккаунтом

    # Отправляем email для подтверждения
    background_tasks.add_task(
        send_verification_email,
        company.account.email,
        verification_token,
        "company"
    )

    return db_company


# Авторизация
@router.post(
    "/login",
    summary="POST запрос на авторизацию",
    description=(
            "Ищет по email в accounts и выбирает, кем будет пользователь"
    )
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    # Найти аккаунт по email
    account = await get_account_by_email(db, form_data.username)
    if not account:
        raise HTTPException(status_code=401, detail="Аккаунт не найден")

    # Определить, связан ли аккаунт с пользователем или компанией
    entity = None
    role = None

    if account.user:
        entity = account.user
        role = "user"
    elif account.company:
        entity = account.company
        role = "company"
    else:
        raise HTTPException(status_code=400, detail="Аккаунт не привязан к пользователю или компании")

    # Проверка пароля
    if not verify_password(form_data.password, account.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный пароль")

    # Проверка верификации
    if not account.is_verified:
        raise HTTPException(status_code=403, detail="Email не подтверждён")

    # Проверка активности (для компании)
    if role == "company" and not account.is_active:
        raise HTTPException(status_code=403, detail="Компания заблокирована")

    # Создание токенов
    access_token = create_access_token(data={"sub": str(account.id), "type": role})
    refresh_token = create_refresh_token()
    expires_at = get_refresh_token_expiry()

    # Сохранение refresh_token
    db_refresh_token = RefreshToken(
        token=refresh_token,
        account_id=account.id,
        expires_at=expires_at
    )
    db.add(db_refresh_token)
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": role  # Опционально: вернуть роль в ответе
    }


# Подтверждение email
@router.get(
    "/verify-email",
    summary="GET запрос на подтверждение почты",
    description=(
            "После регистрации на почту приходит письмо, если там нажмать кнопку, то сюда перекинет"
            "и подтвердит верификацию аккаунта"
    )
)
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Account_Model).filter(Account_Model.verification_token == token)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=400, detail="Недействительный токен")

    account.is_verified = True
    account.verification_token = None
    db.add(account)
    await db.commit()

    return {"message": "Email успешно подтверждён"}
    raise HTTPException(status_code=400, detail="Неверный тип")

@router.post(
    "/verify-token",
    summary="POST запрос на проверку токена",
    description=(
            "Проверка валидности токена"
    )
)
async def verify_token_endpoint(
        token: str = Body(..., embed=True),
):
    is_valid = await verify_token(token)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный или просроченный токен"
        )
    return {"status": "valid"}

# Обновление access_token (refresh)
@router.post(
    "/update-access-token",
    summary="POST запрос на обновление access_token",
    description=(
            "Берёт refresh_token пользователя из бд и присваивает ему новый access_token"
    )
)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(RefreshToken).filter(RefreshToken.token == refresh_token))
    db_refresh_token = result.scalar_one_or_none()

    if not db_refresh_token or db_refresh_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Недействительный refresh-токен")

    account = db_refresh_token.account
    if not account:
        raise HTTPException(status_code=400, detail="Связанный аккаунт не найден")

    # Объединённая логика определения типа аккаунта
    if account.role == "user" and account.user:
        entity_type = "user"
        email = account.email
    elif account.role == "company" and account.company:
        entity_type = "company"
        email = account.email
    else:
        raise HTTPException(status_code=400, detail="Не удалось определить тип аккаунта")

    # Удаляем старый refresh_token
    await db.delete(db_refresh_token)

    # Создаём новый access и refresh токены
    new_access_token = create_access_token(data={"sub": email, "type": entity_type})
    new_refresh_token = create_refresh_token()
    new_expires_at = get_refresh_token_expiry()

    db_new_refresh_token = RefreshToken(
        token=new_refresh_token,
        account_id=account.id,
        expires_at=new_expires_at
    )

    db.add(db_new_refresh_token)
    await db.commit()

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.post(
    "/logout",
    summary="POST запрос выход из аккаунта",
    description=(
            "Удаляет refresh_token из бд для этого пользователя"
    )
)
async def logout(
    current_account: Account_Model = Depends(get_current_account),
    db: AsyncSession = Depends(get_db)
):
    # Удаляем ВСЕ refresh-токены пользователя
    await db.execute(
        delete(RefreshToken)
        .where(RefreshToken.account_id == current_account.id)
    )
    await db.commit()
    return {"message": "Успешный выход из аккаунта"}
