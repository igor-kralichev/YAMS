# Запуск в консоли через команду:
# python shared/db/seeds/seed_users.py

import sys
import os
import datetime
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from shared.core.config import settings
from shared.db.models.accounts import Account_Model
from shared.db.models.users import User_Model
from shared.core.security import get_password_hash

# Добавляем корень проекта в sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))


async def seed_users():
    engine = create_async_engine(settings.DATABASE_URL)

    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        try:
            # Проверка наличия данных
            result = await session.execute(select(User_Model).limit(1))
            if result.scalars().first():
                print("Таблица users уже содержит данные. Пропускаем заполнение.")
                return

            users = []
            base_password = "123321_NNnn"
            hashed_pw = get_password_hash(base_password)

            users_data = [
                {
                    "fullname": "Иванов Сергей Александрович",
                    "email": "example1@mail.ru",
                    "phone_num": 79161234567,
                    "region_id": 78  # Москва
                },
                {
                    "fullname": "Петрова Анна Викторовна",
                    "email": "example2@mail.ru",
                    "phone_num": 79261234568,
                    "region_id": 79  # Санкт-Петербург
                },
                {
                    "fullname": "Сидоров Алексей Иванович",
                    "email": "example3@mail.ru",
                    "phone_num": 79031234569,
                    "region_id": 53  # Московская область
                },
                {
                    "fullname": "Козлова Мария Сергеевна",
                    "email": "example4@mail.ru",
                    "phone_num": 79151234570,
                    "region_id": 63  # Ростовская область
                },
                {
                    "fullname": "Морозов Дмитрий Павлович",
                    "email": "example5@mail.ru",
                    "phone_num": 79271234571,
                    "region_id": 26  # Краснодарский край
                },
                {
                    "fullname": "Васильева Ольга Николаевна",
                    "email": "example6@mail.ru",
                    "phone_num": 79051234572,
                    "region_id": 42  # Иркутская область
                },
                {
                    "fullname": "Кузнецов Андрей Викторович",
                    "email": "example7@mail.ru",
                    "phone_num": 79181234573,
                    "region_id": 44  # Калужская область
                },
                {
                    "fullname": "Смирнова Екатерина Андреевна",
                    "email": "example8@mail.ru",
                    "phone_num": 79291234574,
                    "region_id": 55  # Нижегородская область
                },
                {
                    "fullname": "Николаев Павел Сергеевич",
                    "email": "example9@mail.ru",
                    "phone_num": 79061234575,
                    "region_id": 64  # Рязанская область
                },
                {
                    "fullname": "Федорова Наталья Ивановна",
                    "email": "example10@mail.ru",
                    "phone_num": 79171234576,
                    "region_id": 77  # Ярославская область
                }
            ]

            # Создание объектов
            for data in users_data:
                account = Account_Model(
                    email=data["email"],
                    hashed_password=hashed_pw,
                    is_active=True,
                    is_verified=True,
                    verification_token=None,
                    role="user",
                    phone_num=data["phone_num"],
                    region_id=data["region_id"]
                )
                user = User_Model(
                    fullname=data["fullname"],
                    photo_url=None,  # Оставляем пустым
                    account=account
                )
                users.append(user)

            session.add_all(users)
            await session.commit()
            print("Пользователи и аккаунты успешно добавлены!")

        except Exception as e:
            print(f"Ошибка: {e}")
            await session.rollback()
        finally:
            await session.close()


if __name__ == "__main__":
    asyncio.run(seed_users())