# auth_service/app/routes/companies.py
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
from shared.services.transliterate import transliterate
from shared.core.security import get_password_hash, verify_password
from shared.db.models import Company_Model as CompanyModel, Account_Model
from shared.db.schemas import Company as CompanySchema
from shared.services.auth import get_current_company
from shared.db.schemas.company import CompanyUpdate, ChangePasswordRequest
from shared.db.session import get_db

router = APIRouter()


@router.get(
    "/me",
    response_model=CompanySchema,
    summary="GET запрос на просмотр данных о компании, которая авторизовалась",
    description=(
            "Это основа, база для ЛК"
    )
)
async def read_companies_me(
    current_company: CompanyModel = Depends(get_current_company)
):
    return current_company


@router.put(
    "/me",
    response_model=CompanySchema,
    summary="PUT запрос на обновление данных",
    description=(
            "Обновить данные по компании в ЛК (лого в другом месте обновляем)"
    )
)
async def update_company(
    update_data: CompanyUpdate,
    background_tasks: BackgroundTasks,
    current_company: CompanyModel = Depends(get_current_company),
    db: AsyncSession = Depends(get_db)
):
    try:
        update_dict = update_data.dict(exclude_unset=True)
        account_data = {}
        company_data = {}

        # Разделение данных: аккаунт vs компания
        for key, value in update_dict.items():
            if key in ["email", "phone_num", "region_id"]:
                account_data[key] = value
            else:
                company_data[key] = value

        # Обновление аккаунта (email)
        if account_data:
            if "email" in account_data:
                new_email = account_data["email"]

                # Проверка, что email действительно меняется
                if new_email != current_company.account.email:
                    existing_account = await db.execute(
                        select(Account_Model).filter(Account_Model.email == new_email)
                    )
                    existing = existing_account.scalar()
                    if existing and existing.id != current_company.account_id:
                        raise HTTPException(400, detail="Email уже используется")

                    # Генерация токена и сброс верификации
                    verification_token = secrets.token_urlsafe(32)
                    account_data["is_verified"] = False
                    account_data["verification_token"] = verification_token

                    # Отправка письма
                    background_tasks.add_task(send_verification_email, email=new_email, token=verification_token,
                                              type="company")

            await db.execute(
                update(Account_Model)
                .where(Account_Model.id == current_company.account_id)
                .values(**account_data)
            )

        # Обновление компании
        if company_data:
            await db.execute(
                update(CompanyModel)
                .where(CompanyModel.id == current_company.id)
                .values(**company_data)
            )

        await db.commit()

        # Возвращаем обновлённые данные
        result = await db.execute(
            select(CompanyModel)
            .options(joinedload(CompanyModel.account))
            .where(CompanyModel.id == current_company.id)
        )
        return result.scalar_one()

    except IntegrityError:
        await db.rollback()
        raise HTTPException(400, detail="Ошибка обновления данных")


@router.delete(
    "/me",
    status_code=204,
    summary="DELETE запрос на самоликвидацию",
    description=(
            "Роскомнадзор аккаунта"
    )
)
async def delete_company(
        current_company: CompanyModel = Depends(get_current_company),
        db: AsyncSession = Depends(get_db)
):
    try:
        account_id = current_company.account_id

        # Удаление компании
        await db.delete(current_company)

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
            "Возможна проверка на ввод текущего пароля, после чего можно новый вводить"
    )
)
async def change_company_password(
        request: ChangePasswordRequest,
        current_company: CompanyModel = Depends(get_current_company),
        db: AsyncSession = Depends(get_db)
):
    # Проверка текущего пароля
    if not verify_password(request.old_password, current_company.account.hashed_password):
        raise HTTPException(400, detail="Неверный текущий пароль")

    # Хэширование нового пароля
    new_hashed_password = get_password_hash(request.new_password)

    # Обновление пароля
    await db.execute(
        update(Account_Model)
        .where(Account_Model.id == current_company.account_id)
        .values(hashed_password=new_hashed_password)
    )
    await db.commit()

    return {"message": "Пароль успешно изменён"}


@router.post(
    "/upload-logo",
    summary="POST запрос на смену/добавление лого",
    description=(
            "Тут работа уже чисто с фото"
    )
)
async def upload_logo(
        file: UploadFile = File(...),
        current_company: CompanyModel = Depends(get_current_company),
        db: AsyncSession = Depends(get_db)
):
    # Формирование безопасного имени файла
    safe_name = transliterate(current_company.name)
    file_extension = Path(file.filename).suffix
    file_path = f"static/companies/{current_company.id}_{safe_name}{file_extension}"

    # Если ранее был установлен логотип, удаляем старый файл
    if current_company.logo_url:
        old_file_path = current_company.logo_url.lstrip("/")
        if os.path.exists(old_file_path):
            try:
                os.remove(old_file_path)
            except Exception as e:
                # Можно залогировать ошибку удаления, но не прерывать процесс обновления
                print(f"Ошибка удаления старого файла {old_file_path}: {e}")

    # Создаем папку, если её нет
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Асинхронное сохранение файла
    try:
        async with aiofiles.open(file_path, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения файла: {str(e)}")

    # Обновляем путь логотипа в БД
    await db.execute(
        update(CompanyModel)
        .where(CompanyModel.id == current_company.id)
        .values(logo_url=f"/{file_path}")
    )
    await db.commit()

    return {"logo_url": f"/{file_path}"}