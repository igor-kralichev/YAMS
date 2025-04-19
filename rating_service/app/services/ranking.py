from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct
from shared.db.models import (
    Company_Model, Account_Model, Deal_Model, Feedback_Model,
    deal_consumers as DealConsumers, Region
)
import numpy as np
import logging

logger = logging.getLogger(__name__)

async def calculate_company_rankings(db: AsyncSession) -> List[Dict]:
    logger.info("Starting VIKOR ranking calculation with Z-Score normalization")

    # Подзапросы для критериев
    avg_rating_subquery = (
        select(
            Deal_Model.seller_id,
            func.avg(Feedback_Model.stars).label("avg_rating"),
            func.count(Feedback_Model.id).label("feedback_count")
        )
        .join(Feedback_Model, Feedback_Model.deal_id == Deal_Model.id)
        .group_by(Deal_Model.seller_id)
        .subquery()
    )

    order_count_subquery = (
        select(
            Deal_Model.seller_id,
            func.count(Deal_Model.id).label("order_count")
        )
        .group_by(Deal_Model.seller_id)
        .subquery()
    )

    repeat_customer_subquery = (
        select(
            Deal_Model.seller_id,
            func.count(distinct(DealConsumers.c.consumer_id)).label("repeat_customer_orders")
        )
        .join(DealConsumers, DealConsumers.c.deal_id == Deal_Model.id)
        .group_by(Deal_Model.seller_id)
        .having(func.count(DealConsumers.c.deal_id) > 1)
        .subquery()
    )

    # Основной запрос
    query = (
        select(
            Company_Model,
            func.coalesce(avg_rating_subquery.c.avg_rating, 0).label("avg_rating"),
            func.coalesce(avg_rating_subquery.c.feedback_count, 0).label("feedback_count"),
            func.coalesce(order_count_subquery.c.order_count, 0).label("order_count"),
            func.coalesce(repeat_customer_subquery.c.repeat_customer_orders, 0).label("repeat_customer_orders"),
            func.coalesce(func.extract('year', Company_Model.year_founded), 1900).label("year_founded"),
            Account_Model.region_id,
            Region.name.label("region_name")
        )
        .join(Account_Model, Company_Model.account_id == Account_Model.id)
        .join(Region, Account_Model.region_id == Region.id)
        .outerjoin(avg_rating_subquery, avg_rating_subquery.c.seller_id == Company_Model.account_id)
        .outerjoin(order_count_subquery, order_count_subquery.c.seller_id == Company_Model.account_id)
        .outerjoin(repeat_customer_subquery, repeat_customer_subquery.c.seller_id == Company_Model.account_id)
    )

    result = await db.execute(query)
    companies = result.all()

    # VIKOR с Z-Score нормализацией
    scores = []
    if not companies:
        logger.warning("No companies found for ranking")
        return scores

    # Преобразуем данные в float для избежания проблем с Decimal
    companies_data = []
    for company, avg_rating, feedback_count, order_count, repeat_customer_orders, year_founded, region_id, region_name in companies:
        companies_data.append({
            "company": company,
            "avg_rating": float(avg_rating),
            "feedback_count": float(feedback_count),
            "order_count": float(order_count),
            "repeat_customer_orders": float(repeat_customer_orders),
            "year_founded": float(year_founded),
            "region_id": region_id,
            "region_name": region_name
        })

    # Веса критериев
    weights = {
        "rating": 0.4,
        "feedback": 0.2,
        "repeat": 0.2,
        "orders": 0.1,
        "year_founded": 0.1
    }

    # Извлекаем данные для Z-Score
    ratings = [d["avg_rating"] for d in companies_data]
    feedbacks = [d["feedback_count"] for d in companies_data]
    orders = [d["order_count"] for d in companies_data]
    repeats = [d["repeat_customer_orders"] for d in companies_data]
    years = [d["year_founded"] for d in companies_data]

    logger.debug(f"Extracted metrics: ratings={ratings[:5]}, feedbacks={feedbacks[:5]}, orders={orders[:5]}, repeats={repeats[:5]}, years={years[:5]}")

    # Вычисляем среднее и стандартное отклонение
    mean_rating = np.mean(ratings)
    std_rating = np.std(ratings, ddof=1) or 1  # ddof=1 для выборочного std, защита от деления на 0
    mean_feedback = np.mean(feedbacks)
    std_feedback = np.std(feedbacks, ddof=1) or 1
    mean_orders = np.mean(orders)
    std_orders = np.std(orders, ddof=1) or 1
    mean_repeat = np.mean(repeats)
    std_repeat = np.std(repeats, ddof=1) or 1
    mean_year = np.mean(years)
    std_year = np.std(years, ddof=1) or 1

    logger.debug(f"Means: rating={mean_rating}, feedback={mean_feedback}, orders={mean_orders}, repeat={mean_repeat}, year={mean_year}")
    logger.debug(f"Stds: rating={std_rating}, feedback={std_feedback}, orders={std_orders}, repeat={std_repeat}, year={std_year}")

    # Z-Score нормализация
    normalized = []
    for data in companies_data:
        company = data["company"]
        # Z-Score
        z_rating = (data["avg_rating"] - mean_rating) / std_rating
        z_feedback = (data["feedback_count"] - mean_feedback) / std_feedback
        z_orders = (data["order_count"] - mean_orders) / std_orders
        z_repeat = (data["repeat_customer_orders"] - mean_repeat) / std_repeat
        z_year = (data["year_founded"] - mean_year) / std_year

        normalized.append({
            "company": company,
            "avg_rating": z_rating,
            "feedback_count": z_feedback,
            "order_count": z_orders,
            "repeat_customer_orders": z_repeat,
            "year_founded": z_year,
            "region_id": data["region_id"],
            "region_name": data["region_name"],
            "original_metrics": {
                "avg_rating": data["avg_rating"],
                "feedback_count": data["feedback_count"],
                "order_count": data["order_count"],
                "repeat_customer_orders": data["repeat_customer_orders"],
                "year_founded": data["year_founded"]
            }
        })

    # Масштабирование Z-Score значений к [0, 1] для VIKOR
    z_ratings = [d["avg_rating"] for d in normalized]
    z_feedbacks = [d["feedback_count"] for d in normalized]
    z_orders = [d["order_count"] for d in normalized]
    z_repeats = [d["repeat_customer_orders"] for d in normalized]
    z_years = [d["year_founded"] for d in normalized]

    min_rating, max_rating = min(z_ratings, default=0), max(z_ratings, default=1)
    min_feedback, max_feedback = min(z_feedbacks, default=0), max(z_feedbacks, default=1)
    min_orders, max_orders = min(z_orders, default=0), max(z_orders, default=1)
    min_repeat, max_repeat = min(z_repeats, default=0), max(z_repeats, default=1)
    min_year, max_year = min(z_years, default=0), max(z_years, default=1)

    # Находим лучшие и худшие значения (для VIKOR)
    best_values = {
        "rating": max(z_ratings, default=1),  # Максимизируем рейтинг
        "feedback": max(z_feedbacks, default=1),  # Максимизируем количество отзывов
        "orders": max(z_orders, default=1),  # Максимизируем количество заказов
        "repeat": max(z_repeats, default=1),  # Максимизируем повторные заказы
        "year_founded": max(z_years, default=1)  # Максимизируем год основания (новые компании лучше)
    }
    worst_values = {
        "rating": min(z_ratings, default=0),
        "feedback": min(z_feedbacks, default=0),
        "orders": min(z_orders, default=0),
        "repeat": min(z_repeats, default=0),
        "year_founded": min(z_years, default=0)
    }

    logger.debug(f"Best values: {best_values}")
    logger.debug(f"Worst values: {worst_values}")

    # Нормализованная матрица и расчёт S и R
    s_values = []  # Групповая полезность
    r_values = []  # Индивидуальное сожаление
    scores = []  # Инициализируем scores здесь
    for data in normalized:
        company = data["company"]
        # Нормализация Z-Score к [0, 1] для VIKOR
        norm_rating = (
            (best_values["rating"] - data["avg_rating"]) / (best_values["rating"] - worst_values["rating"])
            if best_values["rating"] != worst_values["rating"] else 0
        )
        norm_feedback = (
            (best_values["feedback"] - data["feedback_count"]) / (best_values["feedback"] - worst_values["feedback"])
            if best_values["feedback"] != worst_values["feedback"] else 0
        )
        norm_orders = (
            (best_values["orders"] - data["order_count"]) / (best_values["orders"] - worst_values["orders"])
            if best_values["orders"] != worst_values["orders"] else 0
        )
        norm_repeat = (
            (best_values["repeat"] - data["repeat_customer_orders"]) / (best_values["repeat"] - worst_values["repeat"])
            if best_values["repeat"] != worst_values["repeat"] else 0
        )
        norm_year = (
            (best_values["year_founded"] - data["year_founded"]) / (best_values["year_founded"] - worst_values["year_founded"])
            if best_values["year_founded"] != worst_values["year_founded"] else 0
        )

        # Взвешенные нормализованные значения
        weighted_rating = weights["rating"] * norm_rating
        weighted_feedback = weights["feedback"] * norm_feedback
        weighted_orders = weights["orders"] * norm_orders
        weighted_repeat = weights["repeat"] * norm_repeat
        weighted_year = weights["year_founded"] * norm_year

        # S (групповая полезность) — сумма взвешенных отклонений
        s = weighted_rating + weighted_feedback + weighted_orders + weighted_repeat + weighted_year
        # R (индивидуальное сожаление) — максимальное взвешенное отклонение
        r = max(weighted_rating, weighted_feedback, weighted_orders, weighted_repeat, weighted_year)

        s_values.append(s)
        r_values.append(r)

        scores.append({
            "company": company,
            "region_id": data["region_id"],  # Используем data из normalized
            "region_name": data["region_name"],  # Используем data из normalized
            "avg_rating": data["original_metrics"]["avg_rating"],
            "feedback_count": data["original_metrics"]["feedback_count"],
            "order_count": data["original_metrics"]["order_count"],
            "repeat_customer_orders": data["original_metrics"]["repeat_customer_orders"],
            "year_founded": data["original_metrics"]["year_founded"],
            "s": s,
            "r": r
        })

    # Находим минимальные и максимальные S и R
    s_min = min(s_values, default=0)
    s_max = max(s_values, default=1)
    r_min = min(r_values, default=0)
    r_max = max(r_values, default=1)

    logger.debug(f"S range: min={s_min}, max={s_max}")
    logger.debug(f"R range: min={r_min}, max={r_max}")

    # Параметр компромисса (v = 0.5 — баланс между S и R)
    v = 0.5

    # Вычисляем Q для каждой компании
    for i, score in enumerate(scores):
        s = score["s"]
        r = score["r"]
        # Формула Q
        q = (
            v * (s - s_min) / (s_max - s_min) if s_max != s_min else 0
        ) + (
            (1 - v) * (r - r_min) / (r_max - r_min) if r_max != r_min else 0
        )
        score["score"] = q

    # Сортируем по Q (меньше — лучше)
    scores.sort(key=lambda x: x["score"])
    logger.info(f"Calculated VIKOR scores for {len(scores)} companies")
    return scores