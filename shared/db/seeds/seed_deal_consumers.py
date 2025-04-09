# Запуск в консоли через команду:
# python shared/db/seeds/seed_deal_consumers.py

import sys
import os
import random
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from shared.core.config import settings
from shared.db.models.deal_consumers import DealConsumers

# Добавляем корень проекта в sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))


async def seed_deal_consumers():
    engine = create_async_engine(settings.DATABASE_URL)

    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        try:
            # Проверка наличия данных
            result = await session.execute(select(DealConsumers).limit(1))
            if result.first():
                print("Таблица deal_consumers уже содержит данные. Пропускаем заполнение.")
                return

            deal_consumers = []

            # Список компаний (account_id с 1 по 25)
            companies = [
                {"account_id": 1, "name": "Додо Пицца"},
                {"account_id": 2, "name": "Тануки"},
                {"account_id": 3, "name": "Кофе Хауз"},
                {"account_id": 4, "name": "Хлеб Насущный"},
                {"account_id": 5, "name": "IT-Лаб"},
                {"account_id": 6, "name": "АртКод"},
                {"account_id": 7, "name": "ВебДев"},
                {"account_id": 8, "name": "Стартап Лаб"},
                {"account_id": 9, "name": "Экспресс Логистика"},
                {"account_id": 10, "name": "ТрансЭкспресс"},
                {"account_id": 11, "name": "ЛогистикСервис"},
                {"account_id": 12, "name": "Модный Стиль"},
                {"account_id": 13, "name": "Бутик Элеганс"},
                {"account_id": 14, "name": "Ателье Мода"},
                {"account_id": 15, "name": "ЭкоМаркет"},
                {"account_id": 16, "name": "ФрешМаркет"},
                {"account_id": 17, "name": "Рыбный Мир"},
                {"account_id": 18, "name": "Винный Двор"},
                {"account_id": 19, "name": "Книжный Дом"},
                {"account_id": 20, "name": "АртЛайн Дизайн"},
                {"account_id": 21, "name": "Мастер Плюс"},
                {"account_id": 22, "name": "Ремонт+ Сервис"},
                {"account_id": 23, "name": "СпортЛэнд"},
                {"account_id": 24, "name": "Фитнес Центр \"Энерджи\""},
                {"account_id": 25, "name": "Домашний Уют"},
            ]

            # Список пользователей (account_id с 26 по 35)
            users = [
                {"account_id": 26, "fullname": "Иванов Сергей Александрович"},
                {"account_id": 27, "fullname": "Петрова Анна Викторовна"},
                {"account_id": 28, "fullname": "Сидоров Алексей Иванович"},
                {"account_id": 29, "fullname": "Козлова Мария Сергеевна"},
                {"account_id": 30, "fullname": "Морозов Дмитрий Павлович"},
                {"account_id": 31, "fullname": "Васильева Ольга Николаевна"},
                {"account_id": 32, "fullname": "Кузнецов Андрей Викторович"},
                {"account_id": 33, "fullname": "Смирнова Екатерина Андреевна"},
                {"account_id": 34, "fullname": "Николаев Павел Сергеевич"},
                {"account_id": 35, "fullname": "Федорова Наталья Ивановна"},
            ]

            # Все сделки (ID от 1 до 100)
            all_deal_ids = list(range(1, 101))  # 1–100 + большая сделка 81

            # Генерация покупок для компаний
            for company in companies:
                num_purchases = min(int(random.expovariate(0.1)), 30)  # От 0 до 30 покупок
                if num_purchases > 0:
                    for _ in range(num_purchases):
                        deal_id = random.choice(all_deal_ids)
                        deal_consumer = {
                            "deal_id": deal_id,
                            "consumer_id": company["account_id"],
                        }
                        deal_consumers.append(deal_consumer)

            # Генерация покупок для пользователей
            for user in users:
                num_purchases = min(int(random.expovariate(0.1)), 30)  # От 0 до 30 покупок
                if num_purchases > 0:
                    for _ in range(num_purchases):
                        deal_id = random.choice(all_deal_ids)
                        deal_consumer = {
                            "deal_id": deal_id,
                            "consumer_id": user["account_id"],
                        }
                        deal_consumers.append(deal_consumer)

            # Убедимся, что общее количество около 400
            current_count = len(deal_consumers)
            if current_count < 400:
                extra_purchases = 400 - current_count
                all_accounts = [c["account_id"] for c in companies] + [u["account_id"] for u in users]
                for _ in range(extra_purchases):
                    consumer_id = random.choice(all_accounts)
                    deal_id = random.choice(all_deal_ids)
                    deal_consumer = {
                        "deal_id": deal_id,
                        "consumer_id": consumer_id,
                    }
                    deal_consumers.append(deal_consumer)
            elif current_count > 400:
                # Если больше 400, урезаем случайным образом
                deal_consumers = random.sample(deal_consumers, 400)

            # Добавление записей в таблицу
            for dc in deal_consumers:
                stmt = DealConsumers.insert().values(
                    deal_id=dc["deal_id"],
                    consumer_id=dc["consumer_id"]
                )
                await session.execute(stmt)

            await session.commit()
            print(f"{len(deal_consumers)} покупок успешно добавлены в таблицу deal_consumers!")

        except Exception as e:
            print(f"Ошибка: {e}")
            await session.rollback()
        finally:
            await session.close()


if __name__ == "__main__":
    asyncio.run(seed_deal_consumers())