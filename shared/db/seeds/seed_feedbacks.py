# Запуск в консоли через команду:
# python shared/db/seeds/seed_feedback.py

import sys
import os
import random
import asyncio

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from shared.core.config import settings
from shared.db.models.feedback import Feedback_Model
from shared.db.models.deal_consumers import DealConsumers

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))

FEEDBACK_TEMPLATES = [
    "Отличный сервис, всё быстро и качественно!",
    "Немного задержали доставку, но в целом доволен.",
    "Качество на высоте, рекомендую всем!",
    "Ожидал большего, цена не оправдывает.",
    "Удобно и просто, буду заказывать ещё.",
    "Средненько, могло быть лучше.",
    "Всё супер, спасибо за работу!",
    "Проблемы с заказом, но решили быстро.",
    "Не понравилось, ожидания не оправдались.",
    "Прекрасный опыт, всё идеально!",
]


async def seed_feedback():
    engine = create_async_engine(settings.DATABASE_URL)

    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        try:
            result = await session.execute(select(Feedback_Model).limit(1))
            if result.scalars().first():
                print("Таблица feedback уже содержит данные. Пропускаем заполнение.")
                return

            deal_consumers_result = await session.execute(select(DealConsumers))
            deal_consumers = deal_consumers_result.fetchall()
            deal_purchasers = {}
            for dc in deal_consumers:
                deal_id = dc.deal_id
                consumer_id = dc.consumer_id
                if deal_id not in deal_purchasers:
                    deal_purchasers[deal_id] = set()
                deal_purchasers[deal_id].add(consumer_id)

            all_accounts = list(range(1, 36))  # 50 аккаунтов
            all_deal_ids = list(range(1, 51))  # 50 сделок

            feedbacks = []
            feedback_tracking = {}  # {deal_id: set(author_ids)}

            # 1. Генерация отзывов от покупателей (примерно 70% от 200 = 140)
            purchaser_feedbacks = []
            for deal_id, purchasers in deal_purchasers.items():
                # Каждый покупатель оставляет отзыв с вероятностью 80%
                for author_id in purchasers:
                    if random.random() < 0.8 and (deal_id not in feedback_tracking or author_id not in feedback_tracking.get(deal_id, set())):
                        if deal_id not in feedback_tracking:
                            feedback_tracking[deal_id] = set()
                        feedback = Feedback_Model(
                            deal_id=deal_id,
                            stars=random.randint(1, 5),
                            details=random.choice(FEEDBACK_TEMPLATES),
                            author_id=author_id,
                            is_purchaser=True
                        )
                        purchaser_feedbacks.append(feedback)
                        feedback_tracking[deal_id].add(author_id)

            # Ограничиваем до 140 отзывов от покупателей
            if len(purchaser_feedbacks) > 140:
                purchaser_feedbacks = random.sample(purchaser_feedbacks, 140)
            feedbacks.extend(purchaser_feedbacks)

            # 2. Дополнение отзывами от случайных аккаунтов (до 200)
            current_count = len(feedbacks)
            if current_count < 200:
                extra_feedbacks = 200 - current_count
                available_combinations = [(deal_id, author_id)
                                        for deal_id in all_deal_ids
                                        for author_id in all_accounts
                                        if deal_id not in feedback_tracking or author_id not in feedback_tracking[deal_id]]
                extra_pairs = random.sample(available_combinations, min(extra_feedbacks, len(available_combinations)))
                for deal_id, author_id in extra_pairs:
                    if deal_id not in feedback_tracking:
                        feedback_tracking[deal_id] = set()
                    is_purchaser = (
                        deal_id in deal_purchasers and
                        author_id in deal_purchasers[deal_id]
                    )
                    feedback = Feedback_Model(
                        deal_id=deal_id,
                        stars=random.randint(1, 5),
                        details=random.choice(FEEDBACK_TEMPLATES),
                        author_id=author_id,
                        is_purchaser=is_purchaser
                    )
                    feedbacks.append(feedback)
                    feedback_tracking[deal_id].add(author_id)

            feedback_stats = {}
            purchase_stats = {}
            for f in feedbacks:
                deal_id = f.deal_id
                feedback_stats[deal_id] = feedback_stats.get(deal_id, 0) + 1
            for dc in deal_consumers:
                deal_id = dc.deal_id
                purchase_stats[deal_id] = purchase_stats.get(deal_id, 0) + 1


            session.add_all(feedbacks)
            await session.commit()
            print(f"{len(feedbacks)} отзывов успешно добавлены в таблицу feedback!")

        except Exception as e:
            print(f"Ошибка: {e}")
            await session.rollback()
        finally:
            await session.close()


if __name__ == "__main__":
    asyncio.run(seed_feedback())