# Запуск в консоли через команду:
# python shared/db/seeds/seed_deals.py

import sys
import os
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from shared.core.config import settings
from shared.db.models.deals import Deal_Model

# Добавляем корень проекта в sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))


async def seed_deals():
    engine = create_async_engine(settings.DATABASE_URL)

    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        try:
            # Проверка наличия данных
            result = await session.execute(select(Deal_Model).limit(1))
            if result.scalars().first():
                print("Таблица deals уже содержит данные. Пропускаем заполнение.")
                return

            deals = []
            YAMS_PERCENT_RATE = 0.03  # 3% от seller_price

            # Данные компаний из дампа
            companies_data = [
                {"seller_id": 1, "name": "Додо Пицца", "region_id": 78, "address": "г. Москва, ул. Арбат, д. 12", "branch_id": 45},  # Пищевая промышленность
                {"seller_id": 2, "name": "Тануки", "region_id": 78, "address": "г. Москва, ул. Никольская, д. 5", "branch_id": 45},
                {"seller_id": 3, "name": "Кофе Хауз", "region_id": 78, "address": "г. Москва, ул. Тверская, д. 20", "branch_id": 45},
                {"seller_id": 4, "name": "Хлеб Насущный", "region_id": 78, "address": "г. Москва, ул. Пятницкая, д. 3", "branch_id": 45},
                {"seller_id": 5, "name": "IT-Лаб", "region_id": 53, "address": "г. Подольск, ул. Ленина, д. 5", "branch_id": 11},  # IT и ПО
                {"seller_id": 6, "name": "АртКод", "region_id": 53, "address": "г. Подольск, ул. Советская, д. 7", "branch_id": 32},  # Креативные индустрии
                {"seller_id": 7, "name": "ВебДев", "region_id": 53, "address": "г. Подольск, ул. Московская, д. 9", "branch_id": 11},
                {"seller_id": 8, "name": "Стартап Лаб", "region_id": 53, "address": "г. Подольск, ул. Инновационная, д. 3", "branch_id": 11},
                {"seller_id": 9, "name": "Экспресс Логистика", "region_id": 63, "address": "г. Ростов-на-Дону, ул. Пушкина, д. 10", "branch_id": 10},  # Логистика
                {"seller_id": 10, "name": "ТрансЭкспресс", "region_id": 63, "address": "г. Ростов-на-Дону, ул. Лермонтова, д. 8", "branch_id": 10},
                {"seller_id": 11, "name": "ЛогистикСервис", "region_id": 63, "address": "г. Ростов-на-Дону, ул. Гагарина, д. 12", "branch_id": 10},
                {"seller_id": 12, "name": "Модный Стиль", "region_id": 79, "address": "г. Санкт-Петербург, ул. Невская, д. 20", "branch_id": 15},  # Розничная торговля
                {"seller_id": 13, "name": "Бутик Элеганс", "region_id": 79, "address": "г. Санкт-Петербург, ул. Марата, д. 15", "branch_id": 15},
                {"seller_id": 14, "name": "Ателье Мода", "region_id": 79, "address": "г. Санкт-Петербург, ул. Советская, д. 7", "branch_id": 44},  # Легкая промышленность
                {"seller_id": 15, "name": "ЭкоМаркет", "region_id": 26, "address": "г. Краснодар, ул. Северная, д. 15", "branch_id": 15},
                {"seller_id": 16, "name": "ФрешМаркет", "region_id": 26, "address": "г. Краснодар, ул. Красная, д. 22", "branch_id": 15},
                {"seller_id": 17, "name": "Рыбный Мир", "region_id": 42, "address": "г. Иркутск, ул. Советская, д. 7", "branch_id": 2},  # Рыболовство
                {"seller_id": 18, "name": "Винный Двор", "region_id": 42, "address": "г. Иркутск, ул. Ленина, д. 3", "branch_id": 15},
                {"seller_id": 19, "name": "Книжный Дом", "region_id": 44, "address": "г. Калуга, ул. Ленина, д. 3", "branch_id": 15},
                {"seller_id": 20, "name": "АртЛайн Дизайн", "region_id": 44, "address": "г. Калуга, ул. Победы, д. 10", "branch_id": 32},
                {"seller_id": 21, "name": "Мастер Плюс", "region_id": 55, "address": "г. Нижний Новгород, ул. Минина, д. 8", "branch_id": 6},  # Обрабатывающая промышленность
                {"seller_id": 22, "name": "Ремонт+ Сервис", "region_id": 55, "address": "г. Нижний Новгород, ул. Советская, д. 6", "branch_id": 8},  # Строительство
                {"seller_id": 23, "name": "СпортЛэнд", "region_id": 64, "address": "г. Рязань, ул. Гагарина, д. 11", "branch_id": 15},
                {"seller_id": 24, "name": "Фитнес Центр \"Энерджи\"", "region_id": 64, "address": "г. Рязань, ул. Лесная, д. 5", "branch_id": 25},  # Развлечения
                {"seller_id": 25, "name": "Домашний Уют", "region_id": 77, "address": "г. Ярославль, ул. Советская, д. 14", "branch_id": 15},
            ]

            # Список сделок для каждой компании (товары и услуги вперемешку)
            deal_templates = {
                1: [("Пицца Маргарита", 1, 1200), ("Пицца Четыре сыра", 1, 1400), ("Доставка пиццы", 2, 500), ("Пицца Пепперони", 1, 1300), ("Заказ банкета", 2, 3000), ("Пицца Гавайская", 1, 1250), ("Кейтеринг", 2, 5000), ("Пицца с морепродуктами", 1, 1500)],
                2: [("Суши сет малый", 1, 1000), ("Ужин на двоих", 2, 2000), ("Роллы Филадельфия", 1, 800), ("Доставка суши", 2, 600), ("Сет Тануки", 1, 1500), ("Обед в ресторане", 2, 1800), ("Роллы Калифорния", 1, 900), ("Закуски к суши", 1, 700)],
                3: [("Кофе Латте", 1, 300), ("Капучино с собой", 2, 250), ("Чай зеленый", 1, 200), ("Десерт тирамису", 1, 400), ("Кофе Американо", 1, 250), ("Кофе на вынос", 2, 200), ("Пончик", 1, 150), ("Кофе Эспрессо", 1, 200)],
                4: [("Багет свежий", 1, 150), ("Круассан с шоколадом", 1, 200), ("Выпечка на заказ", 2, 1000), ("Хлеб ржаной", 1, 120), ("Пирог с яблоками", 1, 300), ("Торт на заказ", 2, 1500), ("Булочка с корицей", 1, 180), ("Хлеб белый", 1, 130)],
                5: [("Разработка сайта", 2, 10000), ("Программа учета", 1, 5000), ("Техподдержка", 2, 2000), ("Мобильное приложение", 2, 15000), ("Лицензия ПО", 1, 3000), ("Обновление ПО", 2, 2500), ("Скрипт автоматизации", 2, 4000), ("Антивирус", 1, 1000)],
                6: [("Дизайн логотипа", 2, 3000), ("Плакат А3", 1, 500), ("Брендинг", 2, 8000), ("Дизайн сайта", 2, 5000), ("Визитки", 1, 300), ("Флаер", 1, 400), ("Дизайн упаковки", 2, 3500), ("Баннер", 1, 600)],
                7: [("Сайт-визитка", 2, 5000), ("Домен и хостинг", 1, 1000), ("SEO оптимизация", 2, 3000), ("Лендинг", 2, 7000), ("Сайт-магазин", 2, 12000), ("Хостинг на год", 1, 1500), ("Редизайн сайта", 2, 4000), ("Сайт-каталог", 2, 8000)],
                8: [("Аренда офиса", 2, 2000), ("Стол офисный", 1, 3000), ("Коворкинг на день", 2, 500), ("Кресло офисное", 1, 2500), ("Место в коворкинге", 2, 1500), ("Шкаф офисный", 1, 2000), ("Консультация стартапа", 2, 1000), ("Офисная лампа", 1, 800)],
                9: [("Экспресс доставка", 2, 800), ("Коробка упаковочная", 1, 200), ("Доставка посылки", 2, 1000), ("Упаковка груза", 1, 300), ("Срочная доставка", 2, 1500), ("Пакет для отправки", 1, 150), ("Курьерская доставка", 2, 1200), ("Контейнер малый", 1, 500)],
                10: [("Грузоперевозка 1т", 2, 2000), ("Ящик для груза", 1, 400), ("Перевозка мебели", 2, 2500), ("Контейнер большой", 1, 1000), ("Доставка грузов", 2, 1800), ("Паллета", 1, 600), ("Перевозка техники", 2, 3000), ("Упаковочный материал", 1, 250)],
                11: [("Логистика груза", 2, 1500), ("Складская коробка", 1, 300), ("Оптимизация маршрута", 2, 2000), ("Ящик складской", 1, 400), ("Управление доставкой", 2, 2500), ("Контейнер складской", 1, 500), ("Планирование логистики", 2, 1800), ("Пакет для склада", 1, 200)],
                12: [("Футболка белая", 1, 800), ("Подбор гардероба", 2, 1500), ("Джинсы классик", 1, 1200), ("Примерка одежды", 2, 500), ("Куртка весенняя", 1, 2000), ("Свитер теплый", 1, 1000), ("Консультация стилиста", 2, 1000), ("Шарф", 1, 400)],
                13: [("Платье вечернее", 1, 3000), ("Консультация по стилю", 2, 1200), ("Сумка кожаная", 1, 2500), ("Подбор аксессуаров", 2, 800), ("Юбка карандаш", 1, 1500), ("Туфли", 1, 2000), ("Стиль на мероприятие", 2, 1500), ("Палантин", 1, 600)],
                14: [("Пошив платья", 2, 3000), ("Ткань хлопок", 1, 500), ("Ремонт куртки", 2, 1000), ("Нитки швейные", 1, 200), ("Подгонка костюма", 2, 1500), ("Шерсть для пошива", 1, 600), ("Пошив рубашки", 2, 2000), ("Пуговицы", 1, 150)],
                15: [("Овощи эко", 1, 300), ("Доставка эко продуктов", 2, 400), ("Фрукты свежие", 1, 350), ("Эко подписка", 2, 1000), ("Мед натуральный", 1, 500), ("Злаки эко", 1, 250), ("Эко доставка на дом", 2, 600), ("Ягоды свежие", 1, 400)],
                16: [("Мясо свежее", 1, 600), ("Подписка на продукты", 2, 1500), ("Сыр местный", 1, 400), ("Доставка деликатесов", 2, 700), ("Рыба копченая", 1, 500), ("Колбаса домашняя", 1, 450), ("Продукты на неделю", 2, 2000), ("Оливки", 1, 300)],
                17: [("Лосось свежий", 1, 800), ("Доставка рыбы", 2, 600), ("Креветки", 1, 700), ("Рыбная дегустация", 2, 1000), ("Форель", 1, 600), ("Мидии", 1, 500), ("Заказ морепродуктов", 2, 1200), ("Икра красная", 1, 900)],
                18: [("Вино красное", 1, 1000), ("Винная дегустация", 2, 1500), ("Вино белое", 1, 900), ("Консультация сомелье", 2, 800), ("Шампанское", 1, 1200), ("Вино розовое", 1, 950), ("Дегустация вин", 2, 2000), ("Бокалы для вина", 1, 300)],
                19: [("Книга детектив", 1, 500), ("Литературный вечер", 2, 300), ("Роман классика", 1, 600), ("Чтение для детей", 2, 200), ("Фантастика", 1, 550), ("Поэзия", 1, 400), ("Книжный клуб", 2, 400), ("Журнал", 1, 250)],
                20: [("Дизайн кухни", 2, 5000), ("Картина маслом", 1, 2000), ("Оформление офиса", 2, 7000), ("Панно декоративное", 1, 1500), ("Дизайн спальни", 2, 6000), ("Скульптура малая", 1, 1000), ("Редизайн интерьера", 2, 4000), ("Подушка декор", 1, 500)],
                21: [("Ремонт ноутбука", 2, 2000), ("Батарея для телефона", 1, 800), ("Ремонт телевизора", 2, 2500), ("Кабель HDMI", 1, 300), ("Обслуживание ПК", 2, 1500), ("Зарядка для ноутбука", 1, 600), ("Чистка техники", 2, 1000), ("Динамик", 1, 400)],
                22: [("Ремонт ванной", 2, 10000), ("Плитка керамическая", 1, 2000), ("Покраска стен", 2, 3000), ("Ламинат дуб", 1, 1500), ("Ремонт комнаты", 2, 5000), ("Обои виниловые", 1, 1000), ("Установка дверей", 2, 4000), ("Краска белая", 1, 500)],
                23: [("Кроссовки беговые", 1, 3000), ("Тренировка персональная", 2, 1500), ("Велосипед городской", 1, 10000), ("Фитнес занятие", 2, 1000), ("Гантели 5кг", 1, 800), ("Коврик спортивный", 1, 500), ("Тренировка групповая", 2, 800), ("Мяч фитнес", 1, 300)],
                24: [("Абонемент в зал", 2, 3000), ("Штанга 20кг", 1, 2500), ("Занятие пилатес", 2, 1200), ("Тренажер беговой", 1, 15000), ("Йога занятие", 2, 1000), ("Гиря 10кг", 1, 1000), ("Фитнес программа", 2, 2000), ("Пояс для зала", 1, 400)],
                25: [("Диван угловой", 1, 20000), ("Сборка мебели", 2, 2000), ("Стол обеденный", 1, 5000), ("Установка шкафа", 2, 1500), ("Кресло мягкое", 1, 7000), ("Подушка спальная", 1, 800), ("Монтаж кухни", 2, 3000), ("Тумба ТВ", 1, 3000)],
            }

            # Генерация 200 сделок
            deal_counter = 0
            for company in companies_data:
                templates = deal_templates.get(company["seller_id"], [("Сделка", 1, 1000)])
                # Каждой компании случайное количество сделок (от 5 до 10)
                num_deals = min(len(templates), 7)  # Ограничим максимум 10 сделок на компанию
                for i in range(num_deals):
                    if deal_counter >= 100:  # Ограничение на 100 сделок
                        break
                    deal_counter += 1
                    name, deal_type_id, price = templates[i % len(templates)]  # Циклически используем шаблоны
                    yams_percent = price * YAMS_PERCENT_RATE  # 3% от seller_price
                    total_cost = price + yams_percent

                    deal = Deal_Model(
                        name_deal=f"{name}",
                        seller_id=company["seller_id"],
                        seller_price=float(price),
                        YAMS_percent=float(yams_percent),
                        total_cost=float(total_cost),
                        region_id=company["region_id"],
                        address_deal=company["address"],
                        date_close=None,
                        photos_url=[],
                        deal_details_id=1,  # Активно
                        deal_branch_id=company["branch_id"],
                        deal_type_id=deal_type_id
                    )
                    deals.append(deal)

            session.add_all(deals)
            await session.commit()
            print(f"{len(deals)} сделок успешно добавлены!")

        except Exception as e:
            print(f"Ошибка: {e}")
            await session.rollback()
        finally:
            await session.close()


if __name__ == "__main__":
    asyncio.run(seed_deals())