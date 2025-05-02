from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from shared.db.models import Deal_Model, deal_consumers

async def get_purchase_history(account_id: int, db: AsyncSession) -> List[Dict]:
    # Выполняем запрос к базе данных
    result = await db.execute(
        select(
            Deal_Model.name_deal,        # Название сделки
            Deal_Model.total_cost,       # Стоимость покупки
            deal_consumers.c.created_at  # Время покупки
        )
        .join(deal_consumers, Deal_Model.id == deal_consumers.c.deal_id)
        .where(deal_consumers.c.consumer_id == account_id)
        .order_by(deal_consumers.c.created_at.desc())  # Сортировка по убыванию времени
    )
    purchases = result.all()

    # Формируем список словарей с данными
    history = [
        {
            "name_deal": row[0],
            "total_cost": float(row[1]),         # Преобразуем Numeric в float для сериализации
            "purchase_time": row[2].isoformat()  # Преобразуем DateTime в строку
        }
        for row in purchases
    ]
    return history