# account_service/app/routes/companies.py
import os
import secrets
from pathlib import Path
from typing import List, Optional

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from sqlalchemy.orm import joinedload

from account_service.app.services.change_data import send_verification_email
from account_service.app.services.change_data import change_password
from account_service.app.services.purchase_history import get_purchase_history
from rating_service.app.schemas.ratings import BuyingTopPublic
from shared.services.transliterate import transliterate
from shared.db.models import Company_Model as CompanyModel, Account_Model, Deal_Model, deal_consumers, BuyTop
from shared.db.schemas import Company as CompanySchema
from shared.services.auth import get_current_company
from shared.db.schemas.company import CompanyUpdate, ChangePasswordRequest
from shared.db.session import get_db

router = APIRouter()


@router.get(
    "/me",
    response_model=CompanySchema,
    summary="GET запрос на просмотр данных о компании, которая авторизовалась",
    description="Возвращает данные текущей компании, включая названия партнёрских компаний"
)
async def read_companies_me(
    current_company: CompanyModel = Depends(get_current_company),
    db: AsyncSession = Depends(get_db)
):
    # Получаем массив partner_companies
    partner_ids = current_company.partner_companies or []
    partner_companies_names = []

    if partner_ids:
        # Находим компании по id из accounts
        companies = await db.execute(
            select(Account_Model.id, CompanyModel.name)
            .join(CompanyModel, CompanyModel.account_id == Account_Model.id)
            .where(Account_Model.id.in_(partner_ids))
            .where(Account_Model.role == "company")
            .order_by(CompanyModel.name)
        )
        partner_companies_names = [{"id": row[0], "name": row[1]} for row in companies.all()]

    # Формируем ответ
    company_data = CompanySchema.from_orm(current_company)
    company_data_dict = company_data.dict()
    company_data_dict["partner_companies_names"] = partner_companies_names

    return company_data_dict



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
    account_id = current_company.account_id
    return await change_password(
        account_id=account_id,
        old_password=request.old_password,
        new_password=request.new_password,
        db=db
    )


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

@router.get(
    "/interacted-companies",
    response_model=List[dict],
    summary="Получение компаний, с которыми взаимодействовала текущая компания",
    description="Возвращает уникальные компании-покупатели сделок текущей компании"
)
async def get_interacted_companies(
    current_company: CompanyModel = Depends(get_current_company),
    db: AsyncSession = Depends(get_db)
):
    # Находим все сделки, где текущая компания — продавец
    seller_account_id = current_company.account_id
    deal_ids = await db.execute(
        select(Deal_Model.id).where(Deal_Model.seller_id == seller_account_id)
    )
    deal_ids = [row[0] for row in deal_ids.all()]

    if not deal_ids:
        return []

    # Находим уникальных покупателей с ролью 'company'
    consumers = await db.execute(
        select(deal_consumers.c.consumer_id)
        .where(deal_consumers.c.deal_id.in_(deal_ids))
        .join(Account_Model, Account_Model.id == deal_consumers.c.consumer_id)
        .where(Account_Model.role == "company")
        .distinct()  # Убираем дубликаты
    )
    consumer_ids = [row[0] for row in consumers.all()]

    if not consumer_ids:
        return []

    # Получаем id и названия компаний
    companies = await db.execute(
        select(Account_Model.id, CompanyModel.name)
        .join(CompanyModel, CompanyModel.account_id == Account_Model.id)
        .where(Account_Model.id.in_(consumer_ids))
    )

    # Возвращаем список словарей с id (из accounts) и name (из companies)
    return [{"id": row[0], "name": row[1]} for row in companies.all()]


@router.post(
    "/set-partner-companies",
    response_model=CompanySchema,
    summary="Выбор до 3 лучших компаний",
    description="Сохраняет до 3 ID компаний в partner_companies текущей компании"
)
async def set_partner_companies(
        partner_ids: List[int] = Body(..., description="Список ID компаний (от 0 до 3)"),
        current_company: CompanyModel = Depends(get_current_company),
        db: AsyncSession = Depends(get_db)
):

    # Проверяем количество выбранных компаний
    if len(partner_ids) > 3:
        raise HTTPException(400, detail="Можно выбрать не более 3 компаний")

    # Проверяем, что текущая компания не выбрана
    if current_company.account_id in partner_ids:
        raise HTTPException(400, detail="Нельзя выбрать собственную компанию")

    # Проверяем, что выбранные компании взаимодействовали с текущей
    interacted_companies = await get_interacted_companies(current_company, db)
    interacted_ids = {comp["id"] for comp in interacted_companies}
    if not set(partner_ids).issubset(interacted_ids) and partner_ids:
        raise HTTPException(400, detail="Можно выбирать только компании, с которыми были сделки")

    # Обновляем partner_companies в базе
    await db.execute(
        update(CompanyModel)
        .where(CompanyModel.id == current_company.id)
        .values(partner_companies=partner_ids)
    )
    await db.commit()

    # Возвращаем обновлённую компанию
    result = await db.execute(
        select(CompanyModel)
        .options(joinedload(CompanyModel.account))
        .where(CompanyModel.id == current_company.id)
    )
    return result.scalar_one()

@router.get(
    "/partner-companies",
    response_model=List[dict],
    summary="Получение названий партнёрских компаний",
    description="Возвращает названия компаний из partner_companies текущей компании"
)
async def get_partner_companies(
    current_company: CompanyModel = Depends(get_current_company),
    db: AsyncSession = Depends(get_db)
):
    # Получаем массив partner_companies
    partner_ids = current_company.partner_companies or []
    if not partner_ids:
        return []

    # Находим компании по id из accounts
    companies = await db.execute(
        select(Account_Model.id, CompanyModel.name)
        .join(CompanyModel, CompanyModel.account_id == Account_Model.id)
        .where(Account_Model.id.in_(partner_ids))
        .where(Account_Model.role == "company")
        .order_by(CompanyModel.name)
    )

    # Возвращаем список словарей с id и name
    return [{"id": row[0], "name": row[1]} for row in companies.all()]

@router.get(
    "/me/top-purchase",
    response_model=Optional[BuyingTopPublic],
    summary="GET запрос на просмотр данных о покупке топ-позиции",
    description="Возвращает данные о покупке топ-позиции текущей компании: если активна — подробности, иначе — дата окончания, сумма и количество покупок"
)
async def get_top_purchase(
    current_company: CompanyModel = Depends(get_current_company),
    db: AsyncSession = Depends(get_db)
):
    # Ищем запись о покупке топа у текущей компании
    result = await db.execute(
        select(BuyTop)
        .where(BuyTop.id_company == current_company.id)
    )
    top_purchase = result.scalar_one_or_none()

    if not top_purchase:
        return None  # Вообще не покупали

    # Вернём данные независимо от активности
    return BuyingTopPublic.from_orm_with_company(top_purchase, current_company.name)

@router.get(
    "/purchase-history",
    summary="GET запрос на историю покупок",
    description="Возвращает историю покупок текущей компании"
)
async def get_company_purchase_history(
    current_company: CompanyModel = Depends(get_current_company),
    db: AsyncSession = Depends(get_db)
):
    account_id = current_company.account_id
    history = await get_purchase_history(account_id, db)
    return history