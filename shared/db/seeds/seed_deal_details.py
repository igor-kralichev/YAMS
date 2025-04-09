# Запуск в консоли через команду:
# python shared/db/seeds/seed_deal_details.py

import sys
import os
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from shared.core.config import settings
from shared.db.models.deal_details import DealDetail

# Добавляем корень проекта в sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))


async def seed_deal_details():
    # Создаем асинхронный движок
    engine = create_async_engine(settings.DATABASE_URL)

    # Создаем асинхронную сессию
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        try:
            # Проверяем наличие данных
            result = await session.execute(select(DealDetail).limit(1))
            if result.scalars().first():
                print("Таблица deal_details уже содержит данные. Пропускаем заполнение.")
                return

            # Список состояний сделок
            deal_details = [
                DealDetail(detail="Активно"),
                DealDetail(detail="Не активно"),
                DealDetail(detail="Продано (YAMS)"),
                DealDetail(detail="Продано вне YAMS"),
                DealDetail(detail="Услуга закрыта"),
            ]

            session.add_all(deal_details)
            await session.commit()
            print("Состояния сделок успешно добавлены в таблицу deal_details.")

        except Exception as e:
            print(f"Ошибка при добавлении состояний сделок: {e}")
            await session.rollback()
        finally:
            await session.close()


if __name__ == "__main__":
    asyncio.run(seed_deal_details())