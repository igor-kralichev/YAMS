# lk_service/app/routes/users.py
import os
import secrets
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import joinedload

from auth_service.app.routes.auth import send_verification_email
from lk_service.app.services.password_service import change_password
from lk_service.app.services.purchase_history import get_purchase_history
from shared.db.models import User_Model as UserModel, Account_Model
from shared.db.schemas import User as UserSchema
from shared.services.auth import get_current_user
from shared.db.schemas.user import UserUpdate, ChangePasswordRequest
from shared.db.session import get_db
from shared.core.security import get_password_hash, verify_password
from shared.services.transliterate import transliterate

router = APIRouter()


@router.get(
    "/me",
    response_model=UserSchema,
    summary="GET на просмотр данных пользователя",
    description=(
            "ЛК пользователя"
    )
)
async def read_users_me(
        current_user: UserModel = Depends(get_current_user)
):
    return current_user


@router.put(
    "/me",
    response_model=UserSchema,
    summary="PUT запрос на изменение данных пользователя",
    description=(
            "Также как с компанией, т.е. без фото"
    )
)
async def update_user(
        update_data: UserUpdate,
        background_tasks: BackgroundTasks,
        current_user: UserModel = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    try:
        update_dict = update_data.dict(exclude_unset=True)
        account_data = {}
        user_data = {}

        # Разделение данных: аккаунт vs пользователь
        for key, value in update_dict.items():
            if key in ["email", "phone_num", "region_id"]:
                account_data[key] = value
            else:
                user_data[key] = value

        # Обновление аккаунта (email)
        if account_data:
            if "email" in account_data:
                new_email = account_data["email"]

                # Проверка, что email действительно меняется
                if new_email != current_user.account.email:
                    existing_account = await db.execute(
                        select(Account_Model).filter(Account_Model.email == new_email)
                    )
                    existing = existing_account.scalar()
                    if existing and existing.id != current_user.account_id:
                        raise HTTPException(400, detail="Email уже используется")

                    # Генерация токена и сброс верификации
                    verification_token = secrets.token_urlsafe(32)
                    account_data["is_verified"] = False
                    account_data["verification_token"] = verification_token

                    # Отправка письма
                    background_tasks.add_task(send_verification_email, email=new_email, token=verification_token, type="user")

            await db.execute(
                update(Account_Model)
                .where(Account_Model.id == current_user.account_id)
                .values(**account_data)
            )

        # Обновление пользователя
        if user_data:
            await db.execute(
                update(UserModel)
                .where(UserModel.id == current_user.id)
                .values(**user_data)
            )

        await db.commit()

        # Возвращаем обновлённые данные
        result = await db.execute(
            select(UserModel)
            .options(joinedload(UserModel.account))
            .where(UserModel.id == current_user.id)
        )
        return result.scalar_one()

    except IntegrityError:
        await db.rollback()
        raise HTTPException(400, detail="Ошибка обновления данных")

@router.delete(
    "/me",
    status_code=204,
    summary="DELETE пользователя",
    description=(
            "Аналогично компании"
    )
)
async def delete_company(
        current_user: UserModel = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    try:
        account_id = current_user.account_id

        # Удаление пользователя
        await db.delete(current_user)

        # Удаление аккаунта
        await db.execute(
            delete(Account_Model)
            .where(Account_Model.id == account_id)
        )

        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ошибка целостности данных при удалении (возможно, есть связанные объекты)"
        )

    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка базы данных при удалении аккаунта"
        )

    except AttributeError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден или уже удалён"
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Непредвиденная ошибка: {str(e)}"
        )


@router.post(
    "/change-password",
    summary="POST запрос на смену пароля",
    description=(
            "Как в компании (можно и в auth роут кинуть, но, думаю, и тут сойдёт"
    )
)
async def change_user_password(
    request: ChangePasswordRequest,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    account_id = current_user.account_id
    return await change_password(
        account_id=account_id,
        old_password=request.old_password,
        new_password=request.new_password,
        db=db
    )



@router.post(
    "/upload-photo",
    summary="POST запрос на добавление фото в аккаунт пользователя",
    description=(
            "Аналогия с компанией"
    )
)
async def upload_photo(
        file: UploadFile = File(...),
        current_user: UserModel = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    # Формируем безопасное имя файла на основе полного имени пользователя
    safe_name = transliterate(current_user.fullname)
    file_extension = Path(file.filename).suffix  # Получаем расширение файла
    file_path = f"static/users/{current_user.id}_{safe_name}{file_extension}"

    # Если у пользователя уже установлен путь до фото, удаляем старый файл
    if current_user.photo_url:
        old_file_path = current_user.photo_url.lstrip("/")
        if os.path.exists(old_file_path):
            try:
                os.remove(old_file_path)
            except Exception as e:
                # Можно залогировать ошибку, но не прерывать обновление
                print(f"Ошибка удаления старого файла {old_file_path}: {e}")

    # Создаём директорию, если её нет
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Асинхронное сохранение файла
    try:
        async with aiofiles.open(file_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения файла: {str(e)}")

    # Обновляем путь до фото в базе данных (предполагается, что поле называется photo_url)
    await db.execute(
        update(UserModel)
        .where(UserModel.id == current_user.id)
        .values(photo_url=f"/{file_path}")
    )
    await db.commit()

    return {"photo_url": f"/{file_path}"}

@router.get(
    "/purchase-history",
    summary="GET запрос на историю покупок",
    description="Возвращает историю покупок текущего пользователя"
)
async def get_user_purchase_history(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    account_id = current_user.account_id
    history = await get_purchase_history(account_id, db)
    return history