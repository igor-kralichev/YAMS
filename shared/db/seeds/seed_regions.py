# Запуск в консоли через команду:
# python shared/db/seeds/seed_regions.py

import sys
import os
import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from shared.core.config import settings
from shared.db.models.regions import Region

# Добавляем корень проекта в sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))


async def seed_regions():
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
            result = await session.execute(select(Region).limit(1))
            if result.scalars().first():
                print("Таблица regions уже содержит данные. Пропускаем заполнение.")
                return

            # Список регионов РФ
            regions = [
                Region(name="Республика Адыгея"),
                Region(name="Республика Алтай"),
                Region(name="Республика Башкортостан"),
                Region(name="Республика Бурятия"),
                Region(name="Республика Дагестан"),
                Region(name="Республика Ингушетия"),
                Region(name="Кабардино-Балкарская Республика"),
                Region(name="Республика Калмыкия"),
                Region(name="Карачаево-Черкесская Республика"),
                Region(name="Республика Карелия"),
                Region(name="Республика Коми"),
                Region(name="Республика Крым"),
                Region(name="Республика Марий Эл"),
                Region(name="Республика Мордовия"),
                Region(name="Республика Саха (Якутия)"),
                Region(name="Республика Северная Осетия — Алания"),
                Region(name="Республика Татарстан"),
                Region(name="Республика Тыва"),
                Region(name="Удмуртская Республика"),
                Region(name="Республика Хакасия"),
                Region(name="Чеченская Республика"),
                Region(name="Чувашская Республика"),
                Region(name="Алтайский край"),
                Region(name="Забайкальский край"),
                Region(name="Камчатский край"),
                Region(name="Краснодарский край"),
                Region(name="Красноярский край"),
                Region(name="Пермский край"),
                Region(name="Приморский край"),
                Region(name="Ставропольский край"),
                Region(name="Хабаровский край"),
                Region(name="Амурская область"),
                Region(name="Архангельская область"),
                Region(name="Астраханская область"),
                Region(name="Белгородская область"),
                Region(name="Брянская область"),
                Region(name="Владимирская область"),
                Region(name="Волгоградская область"),
                Region(name="Вологодская область"),
                Region(name="Воронежская область"),
                Region(name="Ивановская область"),
                Region(name="Иркутская область"),
                Region(name="Калининградская область"),
                Region(name="Калужская область"),
                Region(name="Кемеровская область"),
                Region(name="Кировская область"),
                Region(name="Костромская область"),
                Region(name="Курганская область"),
                Region(name="Курская область"),
                Region(name="Ленинградская область"),
                Region(name="Липецкая область"),
                Region(name="Магаданская область"),
                Region(name="Московская область"),
                Region(name="Мурманская область"),
                Region(name="Нижегородская область"),
                Region(name="Новгородская область"),
                Region(name="Новосибирская область"),
                Region(name="Омская область"),
                Region(name="Оренбургская область"),
                Region(name="Орловская область"),
                Region(name="Пензенская область"),
                Region(name="Псковская область"),
                Region(name="Ростовская область"),
                Region(name="Рязанская область"),
                Region(name="Самарская область"),
                Region(name="Саратовская область"),
                Region(name="Сахалинская область"),
                Region(name="Свердловская область"),
                Region(name="Смоленская область"),
                Region(name="Тамбовская область"),
                Region(name="Тверская область"),
                Region(name="Томская область"),
                Region(name="Тульская область"),
                Region(name="Тюменская область"),
                Region(name="Ульяновская область"),
                Region(name="Челябинская область"),
                Region(name="Ярославская область"),
                Region(name="Москва"),
                Region(name="Санкт-Петербург"),
                Region(name="Севастополь"),
                Region(name="Еврейская автономная область"),
                Region(name="Ненецкий автономный округ"),
                Region(name="Ханты-Мансийский автономный округ — Югра"),
                Region(name="Чукотский автономный округ"),
                Region(name="Ямало-Ненецкий автономный округ"),
                Region(name="Донецкая Народная Республика"),
                Region(name="Луганская Народная Республика"),
                Region(name="Запорожская область"),
                Region(name="Херсонская область"),
            ]

            session.add_all(regions)
            await session.commit()
            print("Регионы успешно добавлены в таблицу regions.")

        except Exception as e:
            print(f"Ошибка при добавлении регионов: {e}")
            await session.rollback()
        finally:
            await session.close()


if __name__ == "__main__":
    asyncio.run(seed_regions())

