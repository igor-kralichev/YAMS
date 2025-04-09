# deal_service/app/routes/deal.py
import os
import shutil
import uuid
from pathlib import Path


from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from sqlalchemy.orm import joinedload
from starlette.background import BackgroundTasks

from deal_service.app.services.deals import send_purchase_email
from shared.db.models import Account_Model, Region, DealBranch, DealDetail, DealTypes, Feedback_Model
from shared.db.models.deal_consumers import DealConsumers
from shared.db.session import get_db
from shared.services.auth import get_current_account
from shared.db.models.deals import Deal_Model
from shared.db.schemas.deal import Deal
import aiofiles
import aiofiles.os as aio_os
import aiofiles.ospath as aio_ospath

router = APIRouter()

@router.get(
    "/regions",
    response_model=list[dict],
    summary="GET регионы нашей страны на 2025 год",
    description=(
        "Для фильтров выборка по регионам"
    )
)
async def get_regions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Region.id, Region.name))
    regions = result.all()
    # Преобразуем к формату [{"id": 1, "name": "Название"}, ...]
    return [{"id": r[0], "name": r[1]} for r in regions]

@router.get(
    "/deal-details",
    response_model=list[dict],
    summary="GET на получение деталей сделки",
    description=(
        "Активно/забронировано/продано и т.д., см в seed_deal_details"
    )
)
async def get_deal_details(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DealDetail.id, DealDetail.detail))
    details = result.all()
    return [{"id": r[0], "name": r[1]} for r in details]

@router.get(
    "/deal-branches",
    response_model=list[dict],
    summary="GET на получение отраслей (выбрал основные, можно добавить)",
    description=(
        "ИТ/сельское хозяйство и т.д., см в seed_deal_branches"
    )
)
async def get_deal_branches(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DealBranch.id, DealBranch.name))
    branches = result.all()
    return [{"id": r[0], "name": r[1]} for r in branches]

@router.get(
    "/deal-types",
    response_model=list[dict],
    summary="GET на получение формата сделки",
    description=(
        "Тут только 2 состояние: Продажа товара или услуга"
    )
)
async def get_deal_types(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DealTypes.id, DealTypes.name))
    types = result.all()
    return [{"id": r[0], "name": r[1]} for r in types]


@router.get(
    "/list",
    response_model=List[Deal],
    summary="GET на получение сделок",
    description=(
        "Тут указано по дефолту 50 сделок на страницу"
    )
)
async def list_deals(
        page: int = 1,
        page_size: int = 50,
        region_id: Optional[int] = None,
        deal_branch_id: Optional[int] = None,
        deal_type_id: Optional[int] = None,
        search: Optional[str] = None,
        db: AsyncSession = Depends(get_db)
):
    if page < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Страниц должно быть >= 1")
    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="На странице от 1 до 100 сделок")

    offset = (page - 1) * page_size
    stmt = select(Deal_Model).options(
        joinedload(Deal_Model.region),
        joinedload(Deal_Model.deal_branch),
        joinedload(Deal_Model.deal_type)
    )

    # Применяем фильтры, если они заданы
    if region_id is not None:
        stmt = stmt.where(Deal_Model.region_id == region_id)
    if deal_branch_id is not None:
        stmt = stmt.where(Deal_Model.deal_branch_id == deal_branch_id)
    if search:
        stmt = stmt.where(Deal_Model.name_deal.ilike(f"%{search}%"))
    if deal_type_id is not None:
        stmt = stmt.where(Deal_Model.deal_type_id == deal_type_id)

    stmt = stmt.order_by(Deal_Model.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(stmt)
    deals = result.scalars().all()

    # Подсчитываем количество покупок для каждой сделки
    deal_ids = [deal.id for deal in deals]
    if deal_ids:
        # Выполняем один запрос для подсчёта покупок для всех сделок
        count_stmt = (
            select(DealConsumers.c.deal_id, func.count().label("order_count"))
            .where(DealConsumers.c.deal_id.in_(deal_ids))
            .group_by(DealConsumers.c.deal_id)
        )
        count_result = await db.execute(count_stmt)
        order_counts = dict(count_result.all())  # {deal_id: order_count}
    else:
        order_counts = {}

    return [
        Deal(
            id=deal.id,
            name_deal=deal.name_deal,
            seller_id=deal.seller_id,
            seller_price=deal.seller_price,
            YAMS_percent=deal.YAMS_percent,
            total_cost=deal.total_cost,
            region_id=deal.region_id,
            address_deal=deal.address_deal,
            date_close=deal.date_close,
            photos_url=deal.photos_url,
            deal_type_id=deal.deal_type_id,
            deal_details_id=deal.deal_details_id,
            deal_branch_id=deal.deal_branch_id,
            created_at=deal.created_at,
            order_count=order_counts.get(deal.id, 0)  # Количество покупок, 0 если нет записей
        )
        for deal in deals
    ]

@router.get(
    "/view-deal/{deal_id}",
    response_model=Deal,
    summary="GET на получение информации о конкретной сделке",
    description=(
        "Возвращает полную информацию о сделке по её ID, включая количество покупателей и отзывов."
    )
)
async def view_deal(
    deal_id: int,
    db: AsyncSession = Depends(get_db)
):
    # Получаем сделку с дополнительной информацией
    stmt = select(Deal_Model).options(
        joinedload(Deal_Model.region),
        joinedload(Deal_Model.deal_branch),
        joinedload(Deal_Model.deal_type),
        joinedload(Deal_Model.deal_details),
        joinedload(Deal_Model.seller)
    ).where(Deal_Model.id == deal_id)

    result = await db.execute(stmt)
    deal = result.unique().scalar_one_or_none()  # Используем unique() из-за joinedload

    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")

    # Подсчитываем количество покупателей (order_count)
    count_stmt = (
        select(func.count())
        .select_from(DealConsumers)
        .where(DealConsumers.c.deal_id == deal_id)
    )
    count_result = await db.execute(count_stmt)
    order_count = count_result.scalar() or 0  # 0, если покупателей нет

    # Подсчитываем количество отзывов (feedback_count)
    feedback_stmt = (
        select(func.count())
        .select_from(Feedback_Model)  # Используем модель Feedback_Model
        .where(Feedback_Model.deal_id == deal_id)
    )
    feedback_result = await db.execute(feedback_stmt)
    feedback_count = feedback_result.scalar() or 0  # 0, если отзывов нет

    # Формируем ответ
    return Deal(
        id=deal.id,
        name_deal=deal.name_deal,
        seller_id=deal.seller_id,
        seller_price=deal.seller_price,
        YAMS_percent=deal.YAMS_percent,
        total_cost=deal.total_cost,
        region_id=deal.region_id,
        address_deal=deal.address_deal,
        date_close=deal.date_close,
        photos_url=deal.photos_url,
        deal_type_id=deal.deal_type_id,
        deal_details_id=deal.deal_details_id,
        deal_branch_id=deal.deal_branch_id,
        created_at=deal.created_at,
        order_count=order_count,  # Количество покупателей
        feedback_count=feedback_count  # Количество отзывов
    )


@router.post(
    "/create-deal",
    response_model=Deal,
    summary="POST на создание сделки",
    description=(
        "Вся информация по сделке тут будет и фото тоже здесь добавляет. "
        "Максимум 5 фотографий."
    )
)
async def create_deal(
    name_deal: str = Form(...),
    seller_price: float = Form(...),
    region_id: int = Form(...),
    address_deal: str = Form(...),
    deal_type_id: int = Form(...),
    deal_branch_id: int = Form(...),
    photos: List[UploadFile] = File(default_factory=list),  # Список файлов, по умолчанию пустой
    db: AsyncSession = Depends(get_db),
    current_account: Account_Model = Depends(get_current_account)
):
    # Проверка роли
    if current_account.role != "company":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав на создание сделки"
        )

    # Проверка существования региона
    region = await db.execute(select(Region).where(Region.id == region_id))
    if not region.scalar():
        raise HTTPException(400, "Указанный регион не существует")

    # Проверка существования отрасли
    branch = await db.execute(select(DealBranch).where(DealBranch.id == deal_branch_id))
    if not branch.scalar():
        raise HTTPException(400, "Указанная отрасль не существует")

    # Получаем ID статуса "Активно"
    status_result = await db.execute(
        select(DealDetail.id).where(DealDetail.detail == "Активно")
    )
    active_status_id = status_result.scalar()
    if not active_status_id:
        raise HTTPException(500, "Статус 'Активно' не найден")

    # Проверяем существование типа сделки
    deal_type = await db.execute(select(DealTypes).where(DealTypes.id == deal_type_id))
    if not deal_type.scalar():
        raise HTTPException(400, "Указанный тип сделки не существует")

    # Валидация адреса
    parts = [p.strip() for p in address_deal.split(',')]
    if len(parts) < 3:
        raise HTTPException(400, "Неверный формат адреса. Введите: Город, улица, дом[, квартира]")
    if not parts[0] or not parts[1] or not parts[2]:
        raise HTTPException(400, "Город, улица и дом должны быть указаны")

    # Проверка количества файлов
    if len(photos) > 5:
        raise HTTPException(400, "Нельзя загрузить больше 5 фотографий")

    yams_percent = round(seller_price * 0.03, 2)
    # Создаём сделку без фото
    new_deal = Deal_Model(
        name_deal=name_deal,
        seller_id=current_account.id,
        seller_price=seller_price,
        YAMS_percent=yams_percent,
        total_cost=yams_percent + seller_price,
        region_id=region_id,
        address_deal=address_deal,
        date_close=None,
        photos_url=[],  # Инициализируем пустым списком
        deal_type_id=deal_type_id,
        deal_details_id=active_status_id,
        deal_branch_id=deal_branch_id
    )
    db.add(new_deal)
    await db.commit()
    await db.refresh(new_deal)

    # Обработка фото
    saved_paths = []
    if photos:  # Проверяем, что photos не пустой список
        folder_path = Path(f"static/deals/{new_deal.id}")
        folder_path.mkdir(parents=True, exist_ok=True)

        for photo in photos:
            if not photo.filename:  # Пропускаем пустые файлы
                continue

            ext = Path(photo.filename).suffix
            filename = f"{uuid.uuid4().hex}{ext}"
            full_path = folder_path / filename

            try:
                with open(full_path, "wb") as f:
                    content = await photo.read()
                    f.write(content)
            except Exception as e:
                raise HTTPException(500, f"Ошибка при сохранении файла {photo.filename}: {str(e)}")

            saved_paths.append(f"/{full_path.as_posix()}")

        # Обновим пути к фото в сделке
        new_deal.photos_url = saved_paths
        await db.commit()
        await db.refresh(new_deal)

    return Deal(
        id=new_deal.id,
        name_deal=new_deal.name_deal,
        seller_id=new_deal.seller_id,
        seller_price=new_deal.seller_price,
        YAMS_percent=new_deal.YAMS_percent,
        total_cost=new_deal.total_cost,
        region_id=new_deal.region_id,
        address_deal=new_deal.address_deal,
        date_close=new_deal.date_close,
        photos_url=new_deal.photos_url,
        deal_type_id=new_deal.deal_type_id,
        deal_details_id=new_deal.deal_details_id,
        deal_branch_id=new_deal.deal_branch_id,
        created_at=new_deal.created_at,
    )

@router.put(
    "/update-deal/{deal_id}",
    response_model=Deal,
    summary="PUT на обновление данных по сделке",
    description=(
        "Обновить можно все данные, которые были для добавления. "
        "Если статус меняется на 'Продано вне YAMS', 'Продано (YAMS)' или 'Услуга закрыта', "
        "поле date_close заполняется текущей датой и временем. "
        "Максимум 5 фотографий, формат: .jpg, .jpeg, .png, размер до 5 МБ."
    )
)
async def update_deal(
    deal_id: int,
    name_deal: Optional[str] = Form(None),
    seller_price: Optional[float] = Form(None),
    region_id: Optional[int] = Form(None),
    address_deal: Optional[str] = Form(None),
    deal_details_id: Optional[int] = Form(None),
    photos: List[UploadFile] = File(default_factory=list),  # Изменяем на List с default_factory
    db: AsyncSession = Depends(get_db),
    current_account: Account_Model = Depends(get_current_account)
):
    # Получаем сделку
    result = await db.execute(
        select(Deal_Model)
        .options(joinedload(Deal_Model.deal_type), joinedload(Deal_Model.consumers))
        .filter(Deal_Model.id == deal_id)
    )
    deal = result.unique().scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")

    # Проверка прав
    if deal.seller_id != current_account.id or current_account.role != "company":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав для изменения сделки"
        )

    # Обновление данных
    if name_deal is not None:
        deal.name_deal = name_deal
    if seller_price is not None:
        deal.seller_price = seller_price
        yams_percent = round(seller_price * 0.03, 2)
        deal.YAMS_percent = yams_percent
        deal.total_cost = seller_price + yams_percent
    if region_id is not None:
        deal.region_id = region_id
    if address_deal is not None:
        # Валидация адреса
        parts = [p.strip() for p in address_deal.split(',')]
        if len(parts) < 3:
            raise HTTPException(400, "Неверный формат адреса. Введите: Город, улица, дом[, квартира]")
        if not parts[0] or not parts[1] or not parts[2]:
            raise HTTPException(400, "Город, улица и дом должны быть указаны")
        deal.address_deal = address_deal
    if deal_details_id is not None:
        # Получаем строковое значение нового статуса
        status_result = await db.execute(
            select(DealDetail.detail).where(DealDetail.id == deal_details_id)
        )
        new_status = status_result.scalar()

        if not new_status:
            raise HTTPException(400, detail="Недопустимый ID статуса")

        # Убрали "Забронировано", так как бронирование удалено
        allowed_common = ["Активно", "Не активно"]
        allowed_for_sale = ["Продано вне YAMS", "Продано (YAMS)"]
        allowed_for_service = ["Услуга закрыта"]

        deal_type_result = await db.execute(
            select(DealTypes.name).where(DealTypes.id == deal.deal_type_id)
        )
        deal_type_name = deal_type_result.scalar()

        if new_status in allowed_common:
            pass
        elif new_status in allowed_for_sale and deal_type_name == "Продажа товара":
            pass
        elif new_status in allowed_for_service and deal_type_name == "Услуга":
            pass
        else:
            raise HTTPException(
                400,
                detail=f"Статус '{new_status}' недопустим для типа сделки '{deal_type_name}'"
            )

        # Проверяем, нужно ли заполнить date_close
        closed_statuses = ["Продано вне YAMS", "Продано (YAMS)", "Услуга закрыта"]
        if new_status in closed_statuses:
            deal.date_close = func.timezone('Europe/Moscow', func.now())
        else:
            deal.date_close = None  # Если статус не закрывающий, сбрасываем date_close

        deal.deal_details_id = deal_details_id

        # Обработка фото
    if photos is not None and photos:  # Проверяем, что photos не None и не пустой список
        # Валидация количества фотографий
        if len(photos) > 5:
            raise HTTPException(400, "Нельзя загрузить больше 5 фотографий")

        # Валидация формата и размера
        ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
        MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 МБ

        for photo in photos:
            if not photo.filename:
                continue
            ext = Path(photo.filename).suffix.lower()
            if ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    400,
                    f"Файл {photo.filename} имеет недопустимый формат. Разрешённые форматы: {ALLOWED_EXTENSIONS}"
                )
            if photo.size > MAX_FILE_SIZE:
                raise HTTPException(400, f"Файл {photo.filename} превышает 5 МБ")

        # Создаём папку для фотографий
        folder_path = Path(f"static/deals/{deal.id}")
        try:
            # Создаём папку, если её нет
            await aio_os.makedirs(folder_path, exist_ok=True)

            # Удаляем старые файлы, если они есть
            if await aio_ospath.exists(folder_path):
                for file in folder_path.iterdir():
                    if file.is_file():
                        await aio_os.remove(file)  # Удаляем только файлы, а не папку

            saved_photo_urls = []

            # Сохраняем новые фотографии
            for photo in photos:
                if not photo.filename:
                    continue
                ext = Path(photo.filename).suffix
                filename = f"{uuid.uuid4().hex}{ext}"
                file_path = folder_path / filename

                async with aiofiles.open(file_path, "wb") as out_file:
                    content = await photo.read()
                    await out_file.write(content)

                saved_photo_urls.append(f"/{file_path.as_posix()}")

            # Обновляем пути в модели
            deal.photos_url = saved_photo_urls

        except Exception as e:
            raise HTTPException(500, f"Ошибка при сохранении фотографий: {str(e)}")

    await db.commit()
    await db.refresh(deal)

    return Deal(
        id=deal.id,
        name_deal=deal.name_deal,
        seller_id=deal.seller_id,
        seller_price=deal.seller_price,
        YAMS_percent=deal.YAMS_percent,
        total_cost=deal.total_cost,
        region_id=deal.region_id,
        address_deal=deal.address_deal,
        date_close=deal.date_close,
        photos_url=deal.photos_url,
        deal_type_id=deal.deal_type_id,
        deal_details_id=deal.deal_details_id,
        deal_branch_id=deal.deal_branch_id,
        created_at=deal.created_at,
        order_count=None  # Указываем order_count как None, если его нет в модели
    )

@router.post(
    "/buy-deal/{deal_id}",
    summary="POST на покупку",
    description=(
        "Покупка сделки и отправка email покупателю. Покупка возможна только если статус сделки 'Активно'. "
        "Повторная покупка разрешена."
    )
)
async def buy_deal(
    deal_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_account: Account_Model = Depends(get_current_account)
):
    # Получаем сделку
    result = await db.execute(
        select(Deal_Model)
        .options(joinedload(Deal_Model.consumers), joinedload(Deal_Model.deal_details))
        .filter(Deal_Model.id == deal_id)
    )
    result = result.unique()
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(404, detail="Сделка не найдена")

    # Проверка, что покупатель не продавец
    if deal.seller_id == current_account.id:
        raise HTTPException(403, detail="Нельзя купить собственную сделку")

    # Проверка текущего статуса сделки
    if deal.deal_details.detail != "Активно":
        raise HTTPException(
            status_code=400,
            detail=f"Покупка возможна только для сделок в статусе 'Активно'. Текущий статус: '{deal.deal_details.detail}'"
        )

    # Добавляем текущего пользователя в список покупателей
    # Разрешаем повторную покупку, поэтому не проверяем, есть ли пользователь в списке
    deal.consumers.append(current_account)

    await db.commit()
    await db.refresh(deal)

    # Получаем email покупателя
    buyer_result = await db.execute(select(Account_Model).filter(Account_Model.id == current_account.id))
    buyer = buyer_result.scalar_one_or_none()
    if not buyer or not buyer.email:
        raise HTTPException(500, detail="Не удалось получить email покупателя")

    # Отправка письма с чеком
    background_tasks.add_task(
        send_purchase_email,
        buyer.email,
        deal.name_deal,
        deal.seller_price,
        deal.YAMS_percent
    )

    return {"message": "Покупка завершена", "deal_id": deal.id}

@router.delete(
    "/delete-deal/{deal_id}",
    summary="DELETE сделки",
    description=(
        "Удалить сделку из базы"
    )
)
async def delete_deal(
        deal_id: int,
        db: AsyncSession = Depends(get_db),
        current_account: Account_Model = Depends(get_current_account)
):
    result = await db.execute(select(Deal_Model).filter(Deal_Model.id == deal_id))
    deal = result.scalar_one_or_none()

    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")

    if deal.seller_id != current_account.id or current_account.role not in ["company", "user"]:
        raise HTTPException(
            status_code=403,
            detail="Нет прав для удаления сделки"
        )

    photos_folder = f"static/deals/{deal_id}"
    if os.path.exists(photos_folder):
        shutil.rmtree(photos_folder)

    await db.delete(deal)
    await db.commit()
    return {"message": f"Сделка с id={deal_id} удалена успешно"}