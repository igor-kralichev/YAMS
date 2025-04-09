# Запуск в консоли через команду:
# python shared/db/seeds/seed_deal_types.py

import sys
import os
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from shared.core.config import settings
from shared.db.models.deal_types import DealTypes

# Добавляем корень проекта в sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))


async def seed_deal_types():
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
            result = await session.execute(select(DealTypes).limit(1))
            if result.scalars().first():
                print("Таблица deal_types уже содержит данные. Пропускаем заполнение.")
                return

            # Список состояний сделок
            deal_types = [
                DealTypes(name="Продажа товара"),
                DealTypes(name="Услуга"),
            ]

            session.add_all(deal_types)
            await session.commit()
            print("Типы сделок успешно добавлены в таблицу deal_types.")

        except Exception as e:
            print(f"Ошибка при добавлении типов сделок: {e}")
            await session.rollback()
        finally:
            await session.close()


if __name__ == "__main__":
    asyncio.run(seed_deal_types())