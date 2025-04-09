# Запуск в консоли через команду:
# python shared/db/seeds/seed_deal_branches.py

import sys
import os
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from shared.core.config import settings
from shared.db.models import DealBranch

# Добавляем корень проекта в sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))


async def seed_deal_branches():
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
            result = await session.execute(select(DealBranch).limit(1))
            if result.scalars().first():
                print("Таблица deal_branch уже содержит данные. Пропускаем заполнение.")
                return

            # Список отраслей
            deal_branches = [
                DealBranch(name="Сельское хозяйство"),
                DealBranch(name="Рыболовство и аквакультура"),
                DealBranch(name="Добыча нефти и газа"),
                DealBranch(name="Горнодобывающая промышленность (руды, уголь)"),
                DealBranch(name="Лесное хозяйство"),
                DealBranch(name="Обрабатывающая промышленность"),
                DealBranch(name="Энергетика"),
                DealBranch(name="Строительство"),
                DealBranch(name="Транспорт"),
                DealBranch(name="Логистика"),
                DealBranch(name="IT и ПО"),
                DealBranch(name="Телекоммуникации"),
                DealBranch(name="Финансы"),
                DealBranch(name="Страхование"),
                DealBranch(name="Розничная торговля"),
                DealBranch(name="Оптовая торговля"),
                DealBranch(name="Электронная коммерция"),
                DealBranch(name="Туризм"),
                DealBranch(name="Гостиничный бизнес"),
                DealBranch(name="Здравоохранение"),
                DealBranch(name="Фармацевтика"),
                DealBranch(name="Образование"),
                DealBranch(name="Научные исследования"),
                DealBranch(name="Культура"),
                DealBranch(name="Развлечения"),
                DealBranch(name="Недвижимость"),
                DealBranch(name="Государственное управление"),
                DealBranch(name="Оборона и безопасность"),
                DealBranch(name="Юридические услуги"),
                DealBranch(name="Консалтинг"),
                DealBranch(name="Реклама и маркетинг"),
                DealBranch(name="Креативные индустрии"),
                DealBranch(name="Экология"),
                DealBranch(name="Водоснабжение"),
                DealBranch(name="Утилизация отходов"),
                DealBranch(name="Социальные услуги"),
                DealBranch(name="Религиозные организации"),
                DealBranch(name="Общественные объединения"),
                DealBranch(name="Космическая индустрия"),
                DealBranch(name="Авиастроение"),
                DealBranch(name="Автомобилестроение"),
                DealBranch(name="Химическая промышленность"),
                DealBranch(name="Металлургия"),
                DealBranch(name="Легкая промышленность"),
                DealBranch(name="Пищевая промышленность"),
            ]

            session.add_all(deal_branches)
            await session.commit()
            print("Отрасли успешно добавлены в таблицу deal_branch.")

        except Exception as e:
            print(f"Ошибка при добавлении отраслей: {e}")
            await session.rollback()
        finally:
            await session.close()


if __name__ == "__main__":
    asyncio.run(seed_deal_branches())
