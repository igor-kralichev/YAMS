from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, distinct, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import joinedload
from redis.asyncio import Redis
from datetime import datetime, timedelta
import json

from starlette.background import BackgroundTasks
from rating_service.app.services.mail import send_top_purchase_email
from shared.db.models import (
    Company_Model, Account_Model, Deal_Model, Feedback_Model,
    DealBranch, Region, BuyTop, deal_consumers as DealConsumers
)
from shared.db.session import get_db
from shared.services.auth import get_current_company
from rating_service.app.schemas.ratings import (
    CompanyShortSchema, CompanyDetailSchema, CompanyVikorSchema,
    BuyingTopCreate, BuyingTopPublic
)
from rating_service.app.services.ranking import calculate_company_rankings

router = APIRouter()

# Зависимость для Redis
async def get_redis() -> Redis:
    from redis.asyncio import Redis
    return Redis(host="localhost", port=6379, db=0, decode_responses=True)

@router.get(
    "/regions",
    response_model=list[dict],
    summary="GET регионы нашей страны на 2025 год",
    description="Для фильтров выборка по регионам"
)
async def get_regions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Region.id, Region.name))
    regions = result.all()
    return [{"id": r[0], "name": r[1]} for r in regions]

@router.get(
    "/industries",
    response_model=list[dict],
    summary="GET на получение отраслей (выбрал основные, можно добавить)",
    description="ИТ/сельское хозяйство и т.д., см в seed_deal_branches"
)
async def get_deal_branches(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DealBranch.id, DealBranch.name))
    branches = result.all()
    return [{"id": r[0], "name": r[1]} for r in branches]

@router.get(
    "/companies",
    response_model=Page[CompanyShortSchema],
    summary="Получение списка компаний с фильтрацией и учетом топ-позиций",
    description="Выводит компании по 30 на страницу, сначала с активной топ-позицией (по убыванию time_stop), затем по региону пользователя и средней оценке, с фильтрацией по региону и индустрии"
)
async def get_companies(
    region_id: Optional[int] = Query(None, description="Фильтр по ID региона"),
    industry_id: Optional[int] = Query(None, description="Фильтр по ID отрасли"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(30, ge=1, le=100, description="Количество записей на странице"),
    current_company: Company_Model = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    cache_key = f"companies:region_{region_id or 'all'}:industry_{industry_id or 'all'}:page_{page}:size_{size}"
    cached = await redis.get(cache_key)
    if cached:
        return Page(**json.loads(cached))

    # Подзапрос для средней оценки
    avg_rating_subquery = (
        select(
            Deal_Model.seller_id,
            func.avg(Feedback_Model.stars).label("avg_rating")
        )
        .join(Feedback_Model, Feedback_Model.deal_id == Deal_Model.id)
        .group_by(Deal_Model.seller_id)
        .subquery()
    )

    # Подзапрос для индустрий
    industries_subquery = (
        select(
            Deal_Model.seller_id,
            func.array_agg(distinct(DealBranch.id)).label("industry_ids"),
            func.array_agg(distinct(DealBranch.name)).label("industry_names")
        )
        .join(DealBranch, Deal_Model.deal_branch_id == DealBranch.id)
        .group_by(Deal_Model.seller_id)
        .subquery()
    )

    # Запрос для компаний с активной топ-позицией
    top_companies_query = (
        select(
            Company_Model,
            avg_rating_subquery.c.avg_rating,
            industries_subquery.c.industry_ids,
            industries_subquery.c.industry_names,
            BuyTop.time_stop
        )
        .join(Account_Model, Company_Model.account_id == Account_Model.id)
        .join(BuyTop, BuyTop.id_company == Company_Model.id)
        .outerjoin(avg_rating_subquery, avg_rating_subquery.c.seller_id == Company_Model.account_id)
        .outerjoin(industries_subquery, industries_subquery.c.seller_id == Company_Model.account_id)
        .where(BuyTop.time_stop >= func.now())
        .order_by(BuyTop.time_stop.desc())
    )

    top_companies_result = await db.execute(top_companies_query)
    top_companies = top_companies_result.all()

    # Основной запрос для остальных компаний
    query = (
        select(
            Company_Model,
            avg_rating_subquery.c.avg_rating,
            industries_subquery.c.industry_ids,
            industries_subquery.c.industry_names
        )
        .join(Account_Model, Company_Model.account_id == Account_Model.id)
        .outerjoin(avg_rating_subquery, avg_rating_subquery.c.seller_id == Company_Model.account_id)
        .outerjoin(industries_subquery, industries_subquery.c.seller_id == Company_Model.account_id)
        .where(~Company_Model.id.in_([c[0].id for c in top_companies]))  # Исключаем топ-компании
    )

    # Фильтры
    if region_id:
        query = query.filter(Account_Model.region_id == region_id)
    if industry_id:
        query = query.filter(industries_subquery.c.industry_ids.contains([industry_id]))

    # Сортировка: по региону текущего пользователя, затем по средней оценке
    query = query.order_by(
        (Account_Model.region_id == current_company.account.region_id).desc(),
        func.coalesce(avg_rating_subquery.c.avg_rating, 0).desc()
    )

    # Пагинация для остальных компаний
    other_companies = await paginate(db, query, params={"page": 1, "size": size * page})

    # Формируем объединенный результат
    result = []

    # Добавляем топ-компании
    for company, avg_rating, industry_ids, industry_names, _ in top_companies:
        partners = []
        if company.partner_companies:
            partner_result = await db.execute(
                select(Account_Model.id, Company_Model.name)
                .join(Company_Model, Company_Model.account_id == Account_Model.id)
                .where(Account_Model.id.in_(company.partner_companies))
            )
            partners = [{"id": row[0], "name": row[1]} for row in partner_result.all()]

        industries = [
            {"id": id, "name": name}
            for id, name in zip(industry_ids or [], industry_names or [])
        ]

        result.append({
            "id": company.id,
            "name": company.name,
            "logo_url": company.logo_url,
            "description": company.description,
            "director_full_name": company.director_full_name,
            "average_rating": avg_rating,
            "industries": industries,
            "partners": partners,
            "is_top": True
        })

    # Добавляем остальные компании
    for company, avg_rating, industry_ids, industry_names in other_companies.items:
        partners = []
        if company.partner_companies:
            partner_result = await db.execute(
                select(Account_Model.id, Company_Model.name)
                .join(Company_Model, Company_Model.account_id == Account_Model.id)
                .where(Account_Model.id.in_(company.partner_companies))
            )
            partners = [{"id": row[0], "name": row[1]} for row in partner_result.all()]

        industries = [
            {"id": id, "name": name}
            for id, name in zip(industry_ids or [], industry_names or [])
        ]

        result.append({
            "id": company.id,
            "name": company.name,
            "logo_url": company.logo_url,
            "description": company.description,
            "director_full_name": company.director_full_name,
            "average_rating": avg_rating,
            "industries": industries,
            "partners": partners,
            "is_top": False
        })

    # Пагинация для объединенного результата
    start = (page - 1) * size
    end = start + size
    paginated_result = result[start:end]

    page_response = Page.create(
        items=paginated_result,
        total=len(result),
        page=page,
        size=size
    )

    # Кэшируем результат
    await redis.setex(cache_key, 3600, json.dumps(page_response.dict()))
    return page_response

@router.get(
    "/companies/{company_id}",
    response_model=CompanyDetailSchema,
    summary="Получение подробной информации о компании",
    description="Возвращает полные данные компании по её ID"
)
async def get_company_details(
    company_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Company_Model)
        .where(Company_Model.id == company_id)
        .options(joinedload(Company_Model.account))
    )
    company = result.scalars().first()
    if not company:
        raise HTTPException(status_code=404, detail="Компания не найдена")

    partners = []
    if company.partner_companies:
        partner_result = await db.execute(
            select(Account_Model.id, Company_Model.name)
            .join(Company_Model, Company_Model.account_id == Account_Model.id)
            .where(Account_Model.id.in_(company.partner_companies))
        )
        partners = [{"id": row[0], "name": row[1]} for row in partner_result.all()]

    return {
        "id": company.id,
        "name": company.name,
        "logo_url": company.logo_url,
        "slogan": company.slogan,
        "description": company.description,
        "legal_address": company.legal_address,
        "actual_address": company.actual_address,
        "employees": company.employees,
        "year_founded": company.year_founded,
        "website": company.website,
        "inn": company.inn,
        "social_media_links": company.social_media_links,
        "partners": partners
    }

@router.get(
    "/ranking-vikor-companies",
    response_model=Page[CompanyVikorSchema],
    summary="Рейтинг компаний по VIKOR с учетом топ-позиций",
    description="Выводит компании по 30 на страницу, сначала компании с активной топ-позицией (по убыванию time_stop), затем по VIKOR"
)
async def get_vikor_companies(
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(30, ge=1, le=100, description="Количество записей на странице"),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    cache_key = f"vikor_companies:page_{page}:size_{size}"
    cached = await redis.get(cache_key)
    if cached:
        return Page(**json.loads(cached))

    # Получаем компании с активной топ-позицией
    top_companies_query = (
        select(
            Company_Model,
            BuyTop.time_stop,
            func.coalesce(
                (select(func.avg(Feedback_Model.stars))
                 .join(Deal_Model, Feedback_Model.deal_id == Deal_Model.id)
                 .where(Deal_Model.seller_id == Company_Model.account_id)
                 .scalar_subquery()), 0
            ).label("avg_rating"),
            func.coalesce(
                (select(func.count(Feedback_Model.id))
                 .join(Deal_Model, Feedback_Model.deal_id == Deal_Model.id)
                 .where(Deal_Model.seller_id == Company_Model.account_id)
                 .scalar_subquery()), 0
            ).label("feedback_count"),
            func.coalesce(
                (select(func.count(Deal_Model.id))
                 .where(Deal_Model.seller_id == Company_Model.account_id)
                 .scalar_subquery()), 0
            ).label("order_count"),
            func.coalesce(
                (select(func.count(distinct(DealConsumers.c.consumer_id)))
                 .join(Deal_Model, DealConsumers.c.deal_id == Deal_Model.id)
                 .where(Deal_Model.seller_id == Company_Model.account_id)
                 .group_by(Deal_Model.seller_id)
                 .having(func.count(DealConsumers.c.deal_id) > 1)
                 .scalar_subquery()), 0
            ).label("repeat_customer_orders")
        )
        .join(BuyTop, BuyTop.id_company == Company_Model.id)
        .where(BuyTop.time_stop >= func.now())
        .order_by(BuyTop.time_stop.desc())
    )

    top_companies_result = await db.execute(top_companies_query)
    top_companies = top_companies_result.all()

    # Получаем VIKOR-рейтинг для остальных компаний
    ranked_companies = await calculate_company_rankings(db)

    # Исключаем компании с топ-позицией из VIKOR-рейтинга
    top_company_ids = {c[0].id for c in top_companies}
    ranked_companies = [c for c in ranked_companies if c["company"].id not in top_company_ids]

    # Формируем объединенный результат
    result = []

    # Добавляем топ-компании
    for company, time_stop, avg_rating, feedback_count, order_count, repeat_customer_orders in top_companies:
        result.append({
            "id": company.id,
            "name": company.name,
            "logo_url": company.logo_url,
            "average_rating": avg_rating,
            "feedback_count": feedback_count,
            "order_count": order_count,
            "repeat_customer_orders": repeat_customer_orders,
            "vikor_score": 0.0,  # Топ-компании не используют VIKOR
            "is_top": True
        })

    # Добавляем компании из VIKOR-рейтинга
    for item in ranked_companies:
        result.append({
            "id": item["company"].id,
            "name": item["company"].name,
            "logo_url": item["company"].logo_url,
            "average_rating": item["avg_rating"],
            "feedback_count": item["feedback_count"],
            "order_count": item["order_count"],
            "repeat_customer_orders": item["repeat_customer_orders"],
            "vikor_score": item["score"],
            "is_top": False
        })

    # Пагинация
    start = (page - 1) * size
    end = start + size
    paginated_result = result[start:end]

    page_response = Page.create(
        items=paginated_result,
        total=len(result),
        page=page,
        size=size
    )

    # Кэшируем результат
    await redis.setex(cache_key, 3600, json.dumps(page_response.dict()))
    return page_response

@router.post(
    "/buy-top",
    response_model=BuyingTopPublic,
    summary="Покупка топ-позиции для компании",
    description="Покупает топ-позицию на указанное количество суток (500 руб./сутки). Суммирует время, если топ активен, или обновляет время окончания, если топ неактивен."
)
async def buy_top_position(
    data: BuyingTopCreate,
    background_tasks: BackgroundTasks,
    current_company: Company_Model = Depends(get_current_company),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    # Проверяем, что компания покупает топ для себя
    if data.id_company != current_company.id:
        raise HTTPException(status_code=403, detail="Можно покупать топ только для своей компании")

    # Параметры покупки
    days = data.days  # Количество суток
    if days < 1:
        raise HTTPException(status_code=400, detail="Количество суток должно быть больше 0")

    cost_per_day = 500.00  # Стоимость за сутки
    total_cost = days * cost_per_day  # Общая стоимость покупки

    # Проверяем, есть ли запись о топ-позиции (активной или неактивной)
    existing_top = (
        await db.execute(
            select(BuyTop)
            .where(BuyTop.id_company == current_company.id)
        )
    ).scalar_one_or_none()

    if existing_top:
        # Если запись существует, проверяем, активна ли она
        is_active = existing_top.time_stop >= func.now()
        new_time_stop = (
            existing_top.time_stop + timedelta(days=days)
            if is_active
            else func.now() + timedelta(days=days)
        )
        await db.execute(
            update(BuyTop)
            .where(BuyTop.id == existing_top.id)
            .values(
                time_stop=new_time_stop,
                total_spent=existing_top.total_spent + total_cost,
                purchase_count=existing_top.purchase_count + 1
            )
        )
        await db.commit()
        await db.refresh(existing_top)
        result = existing_top
    else:
        # Создаем новую запись о покупке топа
        new_top = BuyTop(
            id_company=current_company.id,
            time_stop=func.now() + timedelta(days=days),
            total_spent=total_cost,
            purchase_count=1
        )
        db.add(new_top)
        await db.commit()
        await db.refresh(new_top)
        result = new_top

    # Отправка письма с чеком в фоновом режиме, включая time_stop
    background_tasks.add_task(
        send_top_purchase_email,
        current_company.account.email,
        days,
        total_cost,
        result.time_stop
    )

    # Очищаем кэш рейтингов, чтобы обновить списки с учетом новой топ-позиции
    await redis.delete("vikor_companies:*")
    await redis.delete("companies:*")

    return BuyingTopPublic.from_orm_with_company(result, current_company.name)

# Добавляем пагинацию
add_pagination(router)