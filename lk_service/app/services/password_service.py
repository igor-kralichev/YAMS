from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from shared.db.models import Account_Model
from shared.core.security import verify_password, get_password_hash

async def change_password(
    account_id: int,
    old_password: str,
    new_password: str,
    db: AsyncSession
) -> dict:
    # Находим аккаунт по account_id
    result = await db.execute(
        select(Account_Model).where(Account_Model.id == account_id)
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")

    # Проверяем текущий пароль
    if not verify_password(old_password, account.hashed_password):
        raise HTTPException(status_code=400, detail="Неверный текущий пароль")

    # Хэшируем новый пароль
    new_hashed_password = get_password_hash(new_password)

    # Обновляем пароль в базе данных
    await db.execute(
        update(Account_Model)
        .where(Account_Model.id == account_id)
        .values(hashed_password=new_hashed_password)
    )
    await db.commit()

    return {"message": "Пароль успешно изменён"}