import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from starlette.websockets import WebSocket


from shared.core.config import settings
from shared.db.session import get_db
from shared.db.models.users import User_Model
from shared.db.models import Company_Model as CompanyModel
from shared.db.models.accounts import Account_Model

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_account(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Account_Model:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить подлинность сертификатов",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        account_id: str = payload.get("sub")
        if account_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(
        select(Account_Model)
        .where(Account_Model.id == int(account_id)))
    account = result.scalar_one_or_none()
    if account is None:
        raise credentials_exception
    return account

async def get_current_user(
    account: Account_Model = Depends(get_current_account),
    db: AsyncSession = Depends(get_db)
) -> User_Model:
    if account.role != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недопустимый тип токена"
        )

    result = await db.execute(
        select(User_Model)
        .options(joinedload(User_Model.account))
        .where(User_Model.account_id == account.id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    return user

async def get_current_company(
    account: Account_Model = Depends(get_current_account),
    db: AsyncSession = Depends(get_db)
) -> CompanyModel:
    if account.role != "company":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недопустимый тип токена"
        )

    result = await db.execute(
        select(CompanyModel)
        .options(joinedload(CompanyModel.account))
        .where(CompanyModel.account_id == account.id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Компания не найдена"
        )
    return company

