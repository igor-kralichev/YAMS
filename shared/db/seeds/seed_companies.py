# Запуск в консоли через команду:
# python shared/db/seeds/seed_companies.py

import sys
import os
import datetime
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from shared.core.config import settings
from shared.db.models.accounts import Account_Model
from shared.db.models.companies import Company_Model
from shared.core.security import get_password_hash

# Добавляем корень проекта в sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))


async def seed_companies():
    engine = create_async_engine(settings.DATABASE_URL)

    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        try:
            # Проверка наличия данных
            result = await session.execute(select(Company_Model).limit(1))
            if result.scalars().first():
                print("Таблица companies уже содержит данные. Пропускаем заполнение.")
                return

            companies = []
            base_password = "123321_NNnn"
            hashed_pw = get_password_hash(base_password)

            companies_data = [
                # Москва (region_id: 78) – 4 компании
                {
                    "name": "Додо Пицца",
                    "email": "dodo_pizza@mail.ru",
                    "description": "Сеть пиццерий, известная своим быстрым обслуживанием и качественной продукцией.",
                    "slogan": "Вкус, проверенный временем.",
                    "region_id": 78,
                    "address": "г. Москва, ул. Арбат, д. 12",
                    "phone_num": 74951231001,
                    "employees": 150,
                    "year_founded": datetime.date(2011, 6, 1),
                    "website": "https://dodopizza.ru",
                    "logo_url": "static/companies/dodo_pizza_logo.png"
                },
                {
                    "name": "Тануки",
                    "email": "tanuki@mail.ru",
                    "description": "Сеть ресторанов японской кухни с акцентом на качественные и свежие ингредиенты.",
                    "slogan": "Настоящий вкус Японии.",
                    "region_id": 78,
                    "address": "г. Москва, ул. Никольская, д. 5",
                    "phone_num": 74951231002,
                    "employees": 80,
                    "year_founded": datetime.date(2008, 4, 15),
                    "website": "https://tanuki.ru",
                    "logo_url": "static/companies/tanuki_logo.png"
                },
                {
                    "name": "Кофе Хауз",
                    "email": "coffeehouse@mail.ru",
                    "description": "Сеть кофеен, предлагающая широкий ассортимент авторских напитков и десертов.",
                    "slogan": "Ваш заряд бодрости.",
                    "region_id": 78,
                    "address": "г. Москва, ул. Тверская, д. 20",
                    "phone_num": 74951231003,
                    "employees": 60,
                    "year_founded": datetime.date(2010, 9, 1),
                    "website": "https://coffeehouse.ru",
                    "logo_url": "static/companies/coffeehouse_logo.png"
                },
                {
                    "name": "Хлеб Насущный",
                    "email": "hlebnasush@mail.ru",
                    "description": "Сеть пекарен, известная свежей выпечкой и традиционными рецептами.",
                    "slogan": "Каждый день с любовью.",
                    "region_id": 78,
                    "address": "г. Москва, ул. Пятницкая, д. 3",
                    "phone_num": 74951231004,
                    "employees": 45,
                    "year_founded": datetime.date(2012, 3, 10),
                    "website": "https://hlebnasush.ru",
                    "logo_url": "static/companies/hlebnasush_logo.png"
                },
                # Московская область (region_id: 53) – 4 компании
                {
                    "name": "IT-Лаб",
                    "email": "itlab@mail.ru",
                    "description": "Небольшая IT-компания, предоставляющая услуги по разработке программного обеспечения.",
                    "slogan": "Ваш цифровой партнер.",
                    "region_id": 53,
                    "address": "г. Подольск, ул. Ленина, д. 5",
                    "phone_num": 74951232005,
                    "employees": 30,
                    "year_founded": datetime.date(2015, 5, 20),
                    "website": "https://it-lab.ru",
                    "logo_url": "static/companies/it_lab_logo.png"
                },
                {
                    "name": "АртКод",
                    "email": "artkod@mail.ru",
                    "description": "Дизайнерское агентство, специализирующееся на графическом и веб-дизайне.",
                    "slogan": "Искусство в каждом пикселе.",
                    "region_id": 53,
                    "address": "г. Подольск, ул. Советская, д. 7",
                    "phone_num": 74951232006,
                    "employees": 20,
                    "year_founded": datetime.date(2016, 7, 15),
                    "website": "https://artkod.ru",
                    "logo_url": "static/companies/artkod_logo.png"
                },
                {
                    "name": "ВебДев",
                    "email": "webdev@mail.ru",
                    "description": "Компания по созданию и поддержке сайтов для малого бизнеса.",
                    "slogan": "Ваш сайт – наша забота.",
                    "region_id": 53,
                    "address": "г. Подольск, ул. Московская, д. 9",
                    "phone_num": 74951232007,
                    "employees": 15,
                    "year_founded": datetime.date(2017, 2, 28),
                    "website": "https://webdev.ru",
                    "logo_url": "static/companies/webdev_logo.png"
                },
                {
                    "name": "Стартап Лаб",
                    "email": "startuplab@mail.ru",
                    "description": "Коворкинг и инкубатор для молодых IT-проектов и стартапов.",
                    "slogan": "Где рождаются идеи.",
                    "region_id": 53,
                    "address": "г. Подольск, ул. Инновационная, д. 3",
                    "phone_num": 74951232008,
                    "employees": 25,
                    "year_founded": datetime.date(2018, 11, 5),
                    "website": "https://startuplab.ru",
                    "logo_url": "static/companies/startuplab_logo.png"
                },
                # Ростовская область (region_id: 63) – 3 компании
                {
                    "name": "Экспресс Логистика",
                    "email": "expresslog@mail.ru",
                    "description": "Компания, предоставляющая услуги экспресс-доставки по Ростовской области.",
                    "slogan": "Быстро и надежно.",
                    "region_id": 63,
                    "address": "г. Ростов-на-Дону, ул. Пушкина, д. 10",
                    "phone_num": 78631232009,
                    "employees": 40,
                    "year_founded": datetime.date(2013, 3, 12),
                    "website": "https://express-log.ru",
                    "logo_url": "static/companies/expresslog_logo.png"
                },
                {
                    "name": "ТрансЭкспресс",
                    "email": "transexpress@mail.ru",
                    "description": "Малый транспортно-логистический оператор, обеспечивающий грузоперевозки.",
                    "slogan": "Доставляем вовремя.",
                    "region_id": 63,
                    "address": "г. Ростов-на-Дону, ул. Лермонтова, д. 8",
                    "phone_num": 78631232010,
                    "employees": 35,
                    "year_founded": datetime.date(2014, 8, 20),
                    "website": "https://transexpress.ru",
                    "logo_url": "static/companies/transexpress_logo.png"
                },
                {
                    "name": "ЛогистикСервис",
                    "email": "logisticservice@mail.ru",
                    "description": "Компания, оказывающая услуги по организации логистических процессов для малого бизнеса.",
                    "slogan": "Оптимизация в движении.",
                    "region_id": 63,
                    "address": "г. Ростов-на-Дону, ул. Гагарина, д. 12",
                    "phone_num": 78631232011,
                    "employees": 50,
                    "year_founded": datetime.date(2016, 1, 15),
                    "website": "https://logisticservice.ru",
                    "logo_url": "static/companies/logisticservice_logo.png"
                },
                # Санкт-Петербург (region_id: 79) – 3 компании
                {
                    "name": "Модный Стиль",
                    "email": "modnyystil@mail.ru",
                    "description": "Бутик современной одежды для молодой аудитории.",
                    "slogan": "Стиль – это жизнь.",
                    "region_id": 79,
                    "address": "г. Санкт-Петербург, ул. Невская, д. 20",
                    "phone_num": 78121232012,
                    "employees": 25,
                    "year_founded": datetime.date(2013, 5, 5),
                    "website": "https://modnyystil.ru",
                    "logo_url": "static/companies/modnyystil_logo.png"
                },
                {
                    "name": "Бутик Элеганс",
                    "email": "elegance@mail.ru",
                    "description": "Магазин эксклюзивной женской одежды и аксессуаров.",
                    "slogan": "Элегантность в каждой детали.",
                    "region_id": 79,
                    "address": "г. Санкт-Петербург, ул. Марата, д. 15",
                    "phone_num": 78121232013,
                    "employees": 18,
                    "year_founded": datetime.date(2014, 10, 10),
                    "website": "https://elegance.ru",
                    "logo_url": "static/companies/elegance_logo.png"
                },
                {
                    "name": "Ателье Мода",
                    "email": "atelie_moda@mail.ru",
                    "description": "Небольшое ателье по пошиву и ремонту одежды.",
                    "slogan": "Индивидуальный подход к стилю.",
                    "region_id": 79,
                    "address": "г. Санкт-Петербург, ул. Советская, д. 7",
                    "phone_num": 78121232014,
                    "employees": 12,
                    "year_founded": datetime.date(2015, 7, 7),
                    "website": "https://atelie-moda.ru",
                    "logo_url": "static/companies/atelie_moda_logo.png"
                },
                # Краснодарский край (region_id: 26) – 2 компании
                {
                    "name": "ЭкоМаркет",
                    "email": "ekomarket@mail.ru",
                    "description": "Магазин натуральных и экологически чистых продуктов питания.",
                    "slogan": "Забота о природе и вас.",
                    "region_id": 26,
                    "address": "г. Краснодар, ул. Северная, д. 15",
                    "phone_num": 78512232015,
                    "employees": 40,
                    "year_founded": datetime.date(2013, 4, 1),
                    "website": "https://ekomarket.ru",
                    "logo_url": "static/companies/ekomarket_logo.png"
                },
                {
                    "name": "ФрешМаркет",
                    "email": "freshmarket@mail.ru",
                    "description": "Небольшая сеть магазинов свежих продуктов и деликатесов.",
                    "slogan": "Свежесть каждый день.",
                    "region_id": 26,
                    "address": "г. Краснодар, ул. Красная, д. 22",
                    "phone_num": 78512232016,
                    "employees": 35,
                    "year_founded": datetime.date(2014, 6, 15),
                    "website": "https://freshmarket.ru",
                    "logo_url": "static/companies/freshmarket_logo.png"
                },
                # Иркутская область (region_id: 42) – 2 компании
                {
                    "name": "Рыбный Мир",
                    "email": "rybnymir@mail.ru",
                    "description": "Магазин свежей рыбы и морепродуктов с доставкой по городу.",
                    "slogan": "Свежесть моря у вас дома.",
                    "region_id": 42,
                    "address": "г. Иркутск, ул. Советская, д. 7",
                    "phone_num": 73412232017,
                    "employees": 28,
                    "year_founded": datetime.date(2012, 9, 9),
                    "website": "https://rybnyimir.ru",
                    "logo_url": "static/companies/rybnymir_logo.png"
                },
                {
                    "name": "Винный Двор",
                    "email": "vinnydvor@mail.ru",
                    "description": "Специализированный магазин с широким выбором вин и алкогольной продукции.",
                    "slogan": "Вино для истинных ценителей.",
                    "region_id": 42,
                    "address": "г. Иркутск, ул. Ленина, д. 3",
                    "phone_num": 73412232018,
                    "employees": 20,
                    "year_founded": datetime.date(2013, 11, 20),
                    "website": "https://vinnydvor.ru",
                    "logo_url": "static/companies/vinnydvor_logo.png"
                },
                # Калужская область (region_id: 44) – 2 компании
                {
                    "name": "Книжный Дом",
                    "email": "knizhnymdom@mail.ru",
                    "description": "Небольшая сеть книжных магазинов с богатым выбором литературы.",
                    "slogan": "Знание – сила.",
                    "region_id": 44,
                    "address": "г. Калуга, ул. Ленина, д. 3",
                    "phone_num": 48412232019,
                    "employees": 22,
                    "year_founded": datetime.date(2011, 2, 2),
                    "website": "https://knizhnymdom.ru",
                    "logo_url": "static/companies/knizhnymdom_logo.png"
                },
                {
                    "name": "АртЛайн Дизайн",
                    "email": "artlaindesign@mail.ru",
                    "description": "Студия дизайна, предоставляющая услуги по оформлению интерьеров и брендингу.",
                    "slogan": "Креативные решения для вашего пространства.",
                    "region_id": 44,
                    "address": "г. Калуга, ул. Победы, д. 10",
                    "phone_num": 48412232020,
                    "employees": 18,
                    "year_founded": datetime.date(2012, 8, 18),
                    "website": "https://artlaindesign.ru",
                    "logo_url": "static/companies/artlaindesign_logo.png"
                },
                # Нижегородская область (region_id: 55) – 2 компании
                {
                    "name": "Мастер Плюс",
                    "email": "masterplus@mail.ru",
                    "description": "Сервис по ремонту и обслуживанию бытовой техники и электроники.",
                    "slogan": "Профессионально и вовремя.",
                    "region_id": 55,
                    "address": "г. Нижний Новгород, ул. Минина, д. 8",
                    "phone_num": 74951232021,
                    "employees": 32,
                    "year_founded": datetime.date(2014, 12, 1),
                    "website": "https://masterplus.ru",
                    "logo_url": "static/companies/masterplus_logo.png"
                },
                {
                    "name": "Ремонт+ Сервис",
                    "email": "remontplus@mail.ru",
                    "description": "Небольшая компания, оказывающая услуги по ремонту квартир и офисов.",
                    "slogan": "Делаем ваш дом уютнее.",
                    "region_id": 55,
                    "address": "г. Нижний Новгород, ул. Советская, д. 6",
                    "phone_num": 74951232022,
                    "employees": 28,
                    "year_founded": datetime.date(2015, 3, 22),
                    "website": "https://remontplus.ru",
                    "logo_url": "static/companies/remontplus_logo.png"
                },
                # Рязанская область (region_id: 64) – 2 компании
                {
                    "name": "СпортЛэнд",
                    "email": "sportland@mail.ru",
                    "description": "Магазин спортивных товаров для активного образа жизни.",
                    "slogan": "Будь в форме!",
                    "region_id": 64,
                    "address": "г. Рязань, ул. Гагарина, д. 11",
                    "phone_num": 74951232023,
                    "employees": 30,
                    "year_founded": datetime.date(2013, 7, 7),
                    "website": "https://sportland.ru",
                    "logo_url": "static/companies/sportland_logo.png"
                },
                {
                    "name": "Фитнес Центр \"Энерджи\"",
                    "email": "energyfitness@mail.ru",
                    "description": "Небольшой фитнес-центр с современным оборудованием и групповыми программами.",
                    "slogan": "Энергия для жизни.",
                    "region_id": 64,
                    "address": "г. Рязань, ул. Лесная, д. 5",
                    "phone_num": 74951232024,
                    "employees": 25,
                    "year_founded": datetime.date(2016, 5, 10),
                    "website": "https://energyfitness.ru",
                    "logo_url": "static/companies/energyfitness_logo.png"
                },
                # Ярославская область (region_id: 77) – 1 компания
                {
                    "name": "Домашний Уют",
                    "email": "domashniyuut@mail.ru",
                    "description": "Компания по производству и продаже мебели, текстиля и декора для дома.",
                    "slogan": "Создайте уют в своем доме.",
                    "region_id": 77,
                    "address": "г. Ярославль, ул. Советская, д. 14",
                    "phone_num": 48512232025,
                    "employees": 40,
                    "year_founded": datetime.date(2014, 10, 30),
                    "website": "https://domashniyuut.ru",
                    "logo_url": "static/companies/domashniyuut_logo.png"
                }
            ]

            # Создание объектов
            for data in companies_data:
                account = Account_Model(
                    email=data["email"],
                    hashed_password=hashed_pw,
                    is_active=True,
                    is_verified=True,
                    verification_token=None,
                    role="company",
                    phone_num=data["phone_num"],
                    region_id=data["region_id"]
                )
                company = Company_Model(
                    name=data["name"],
                    description=data["description"],
                    slogan=data["slogan"],
                    address=data["address"],
                    logo_url=data["logo_url"],
                    employees=data["employees"],
                    year_founded=data["year_founded"],
                    website=data["website"],
                    account=account
                )
                companies.append(company)

            session.add_all(companies)
            await session.commit()
            print("Компании и аккаунты успешно добавлены!")

        except Exception as e:
            print(f"Ошибка: {e}")
            await session.rollback()
        finally:
            await session.close()


if __name__ == "__main__":
    asyncio.run(seed_companies())


