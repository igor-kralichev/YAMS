from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, distinct, case
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import joinedload
from redis.asyncio import Redis
import json

from shared.db.models import (
    Company_Model, Account_Model, Deal_Model, Feedback_Model,
    DealBranch, Region, deal_consumers as DealConsumers
)
from shared.db.session import get_db
from shared.services.auth import get_current_company
from rating_service.app.schemas.ratings import (
    CompanyShortSchema, CompanyDetailSchema, CompanyVikorSchema
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
    summary="Получение списка компаний с фильтрацией",
    description="Выводит компании по 30 на страницу, сначала из региона пользователя, затем остальные, с фильтрацией по региону и индустрии"
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
    # Формируем ключ кэша с учётом фильтров и пагинации
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

    # Основной запрос
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
    )

    # Фильтры
    if region_id:
        query = query.filter(Account_Model.region_id == region_id)
    if industry_id:
        query = query.filter(industries_subquery.c.industry_ids.contains([industry_id]))

    # Сортировка: сначала регион текущего пользователя, затем по средней оценке
    query = query.order_by(
        (Account_Model.region_id == current_company.account.region_id).desc(),
        func.coalesce(avg_rating_subquery.c.avg_rating, 0).desc()
    )

    # Пагинация
    companies = await paginate(db, query, params={"page": page, "size": size})

    # Формируем ответ
    result = []
    for company, avg_rating, industry_ids, industry_names in companies.items:
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
            "partners": partners
        })

    companies.items = result

    # Кэшируем результат
    await redis.setex(cache_key, 3600, json.dumps(companies.dict()))
    return companies

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
    summary="Рейтинг компаний по VIKOR",
    description="Выводит компании по 30 на страницу, ранжированные по 5 критериям с использованием VIKOR"
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

    ranked_companies = await calculate_company_rankings(db)

    result = [{
        "id": item["company"].id,
        "name": item["company"].name,
        "logo_url": item["company"].logo_url,
        "average_rating": item["avg_rating"],
        "feedback_count": item["feedback_count"],
        "order_count": item["order_count"],
        "repeat_customer_orders": item["repeat_customer_orders"],
        "vikor_score": item["score"]
    } for item in ranked_companies]

    start = (page - 1) * size
    end = start + size
    paginated_result = result[start:end]

    page_response = Page.create(
        items=paginated_result,
        total=len(result),
        page=page,
        size=size
    )

    await redis.setex(cache_key, 3600, json.dumps(page_response.dict()))
    return page_response

# Добавляем пагинацию
add_pagination(router)