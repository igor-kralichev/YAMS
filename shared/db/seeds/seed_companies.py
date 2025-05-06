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
from shared.security.security import get_password_hash

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
                    "legal_address": "г. Москва, ул. Арбат, д. 12",
                    "actual_address": "г. Москва, ул. Арбат, д. 12",
                    "phone_num": 74951231001,
                    "employees": 150,
                    "year_founded": datetime.date(2011, 6, 1),
                    "website": "https://dodopizza.ru",
                    "logo_url": "static/companies/dodo_pizza_logo.png",
                    "inn": "1234567890",
                    "kpp": "123456789",
                    "ogrn": "1234567890123",
                    "oktmo": "12345678",
                    "okpo": "12345678",
                    "director_full_name": "Иванов Иван Иванович",
                    "social_media_links": ["https://vk.com/dodopizza", "https://t.me/dodopizza"]
                },
                {
                    "name": "Тануки",
                    "email": "tanuki@mail.ru",
                    "description": "Сеть ресторанов японской кухни с акцентом на качественные и свежие ингредиенты.",
                    "slogan": "Настоящий вкус Японии.",
                    "region_id": 78,
                    "legal_address": "г. Москва, ул. Никольская, д. 5",
                    "actual_address": "г. Москва, ул. Никольская, д. 5",
                    "phone_num": 74951231002,
                    "employees": 80,
                    "year_founded": datetime.date(2008, 4, 15),
                    "website": "https://tanuki.ru",
                    "logo_url": "static/companies/tanuki_logo.png",
                    "inn": "2345678901",
                    "kpp": "234567890",
                    "ogrn": "2345678901234",
                    "oktmo": "23456789",
                    "okpo": "23456789",
                    "director_full_name": "Петров Петр Петрович",
                    "social_media_links": ["https://vk.com/tanuki", "https://t.me/tanuki"]
                },
                {
                    "name": "Кофе Хауз",
                    "email": "coffeehouse@mail.ru",
                    "description": "Сеть кофеен, предлагающая широкий ассортимент авторских напитков и десертов.",
                    "slogan": "Ваш заряд бодрости.",
                    "region_id": 78,
                    "legal_address": "г. Москва, ул. Тверская, д. 20",
                    "actual_address": "г. Москва, ул. Тверская, д. 20",
                    "phone_num": 74951231003,
                    "employees": 60,
                    "year_founded": datetime.date(2010, 9, 1),
                    "website": "https://coffeehouse.ru",
                    "logo_url": "static/companies/coffeehouse_logo.png",
                    "inn": "3456789012",
                    "kpp": "345678901",
                    "ogrn": "3456789012345",
                    "oktmo": "34567890",
                    "okpo": "34567890",
                    "director_full_name": "Сидоров Сидор Сидорович",
                    "social_media_links": ["https://vk.com/coffeehouse", "https://t.me/coffeehouse"]
                },
                {
                    "name": "Хлеб Насущный",
                    "email": "hlebnasush@mail.ru",
                    "description": "Сеть пекарен, известная свежей выпечкой и традиционными рецептами.",
                    "slogan": "Каждый день с любовью.",
                    "region_id": 78,
                    "legal_address": "г. Москва, ул. Пятницкая, д. 3",
                    "actual_address": "г. Москва, ул. Пятницкая, д. 3",
                    "phone_num": 74951231004,
                    "employees": 45,
                    "year_founded": datetime.date(2012, 3, 10),
                    "website": "https://hlebnasush.ru",
                    "logo_url": "static/companies/hlebnasush_logo.png",
                    "inn": "4567890123",
                    "kpp": "456789012",
                    "ogrn": "4567890123456",
                    "oktmo": "45678901",
                    "okpo": "45678901",
                    "director_full_name": "Кузнецов Алексей Викторович",
                    "social_media_links": ["https://vk.com/hlebnasush", "https://t.me/hlebnasush"]
                },
                # Московская область (region_id: 53) – 4 компании
                {
                    "name": "IT-Лаб",
                    "email": "itlab@mail.ru",
                    "description": "Небольшая IT-компания, предоставляющая услуги по разработке программного обеспечения.",
                    "slogan": "Ваш цифровой партнер.",
                    "region_id": 53,
                    "legal_address": "г. Подольск, ул. Ленина, д. 5",
                    "actual_address": "г. Подольск, ул. Ленина, д. 5",
                    "phone_num": 74951232005,
                    "employees": 30,
                    "year_founded": datetime.date(2015, 5, 20),
                    "website": "https://it-lab.ru",
                    "logo_url": "static/companies/it_lab_logo.png",
                    "inn": "5678901234",
                    "kpp": "567890123",
                    "ogrn": "5678901234567",
                    "oktmo": "56789012",
                    "okpo": "56789012",
                    "director_full_name": "Морозов Дмитрий Сергеевич",
                    "social_media_links": ["https://vk.com/itlab", "https://t.me/itlab"]
                },
                {
                    "name": "АртКод",
                    "email": "artkod@mail.ru",
                    "description": "Дизайнерское агентство, специализирующееся на графическом и веб-дизайне.",
                    "slogan": "Искусство в каждом пикселе.",
                    "region_id": 53,
                    "legal_address": "г. Подольск, ул. Советская, д. 7",
                    "actual_address": "г. Подольск, ул. Советская, д. 7",
                    "phone_num": 74951232006,
                    "employees": 20,
                    "year_founded": datetime.date(2016, 7, 15),
                    "website": "https://artkod.ru",
                    "logo_url": "static/companies/artkod_logo.png",
                    "inn": "6789012345",
                    "kpp": "678901234",
                    "ogrn": "6789012345678",
                    "oktmo": "67890123",
                    "okpo": "67890123",
                    "director_full_name": "Соколов Андрей Павлович",
                    "social_media_links": ["https://vk.com/artkod", "https://t.me/artkod"]
                },
                {
                    "name": "ВебДев",
                    "email": "webdev@mail.ru",
                    "description": "Компания по созданию и поддержке сайтов для малого бизнеса.",
                    "slogan": "Ваш сайт – наша забота.",
                    "region_id": 53,
                    "legal_address": "г. Подольск, ул. Московская, д. 9",
                    "actual_address": "г. Подольск, ул. Московская, д. 9",
                    "phone_num": 74951232007,
                    "employees": 15,
                    "year_founded": datetime.date(2017, 2, 28),
                    "website": "https://webdev.ru",
                    "logo_url": "static/companies/webdev_logo.png",
                    "inn": "7890123456",
                    "kpp": "789012345",
                    "ogrn": "7890123456789",
                    "oktmo": "78901234",
                    "okpo": "78901234",
                    "director_full_name": "Николаев Игорь Олегович",
                    "social_media_links": ["https://vk.com/webdev", "https://t.me/webdev"]
                },
                {
                    "name": "Стартап Лаб",
                    "email": "startuplab@mail.ru",
                    "description": "Коворкинг и инкубатор для молодых IT-проектов и стартапов.",
                    "slogan": "Где рождаются идеи.",
                    "region_id": 53,
                    "legal_address": "г. Подольск, ул. Инновационная, д. 3",
                    "actual_address": "г. Подольск, ул. Инновационная, д. 3",
                    "phone_num": 74951232008,
                    "employees": 25,
                    "year_founded": datetime.date(2018, 11, 5),
                    "website": "https://startuplab.ru",
                    "logo_url": "static/companies/startuplab_logo.png",
                    "inn": "8901234567",
                    "kpp": "890123456",
                    "ogrn": "8901234567890",
                    "oktmo": "89012345",
                    "okpo": "89012345",
                    "director_full_name": "Васильев Роман Александрович",
                    "social_media_links": ["https://vk.com/startuplab", "https://t.me/startuplab"]
                },
                # Ростовская область (region_id: 63) – 3 компании
                {
                    "name": "Экспресс Логистика",
                    "email": "expresslog@mail.ru",
                    "description": "Компания, предоставляющая услуги экспресс-доставки по Ростовской области.",
                    "slogan": "Быстро и надежно.",
                    "region_id": 63,
                    "legal_address": "г. Ростов-на-Дону, ул. Пушкина, д. 10",
                    "actual_address": "г. Ростов-на-Дону, ул. Пушкина, д. 10",
                    "phone_num": 78631232009,
                    "employees": 40,
                    "year_founded": datetime.date(2013, 3, 12),
                    "website": "https://express-log.ru",
                    "logo_url": "static/companies/expresslog_logo.png",
                    "inn": "9012345678",
                    "kpp": "901234567",
                    "ogrn": "9012345678901",
                    "oktmo": "90123456",
                    "okpo": "90123456",
                    "director_full_name": "Лебедев Сергей Николаевич",
                    "social_media_links": ["https://vk.com/expresslog", "https://t.me/expresslog"]
                },
                {
                    "name": "ТрансЭкспресс",
                    "email": "transexpress@mail.ru",
                    "description": "Малый транспортно-логистический оператор, обеспечивающий грузоперевозки.",
                    "slogan": "Доставляем вовремя.",
                    "region_id": 63,
                    "legal_address": "г. Ростов-на-Дону, ул. Лермонтова, д. 8",
                    "actual_address": "г. Ростов-на-Дону, ул. Лермонтова, д. 8",
                    "phone_num": 78631232010,
                    "employees": 35,
                    "year_founded": datetime.date(2014, 8, 20),
                    "website": "https://transexpress.ru",
                    "logo_url": "static/companies/transexpress_logo.png",
                    "inn": "0123456789",
                    "kpp": "012345678",
                    "ogrn": "0123456789012",
                    "oktmo": "01234567",
                    "okpo": "01234567",
                    "director_full_name": "Григорьев Павел Андреевич",
                    "social_media_links": ["https://vk.com/transexpress", "https://t.me/transexpress"]
                },
                {
                    "name": "ЛогистикСервис",
                    "email": "logisticservice@mail.ru",
                    "description": "Компания, оказывающая услуги по организации логистических процессов для малого бизнеса.",
                    "slogan": "Оптимизация в движении.",
                    "region_id": 63,
                    "legal_address": "г. Ростов-на-Дону, ул. Гагарина, д. 12",
                    "actual_address": "г. Ростов-на-Дону, ул. Гагарина, д. 12",
                    "phone_num": 78631232011,
                    "employees": 50,
                    "year_founded": datetime.date(2016, 1, 15),
                    "website": "https://logisticservice.ru",
                    "logo_url": "static/companies/logisticservice_logo.png",
                    "inn": "1234509876",
                    "kpp": "123450987",
                    "ogrn": "1234509876123",
                    "oktmo": "12345098",
                    "okpo": "12345098",
                    "director_full_name": "Егоров Виктор Михайлович",
                    "social_media_links": ["https://vk.com/logisticservice", "https://t.me/logisticservice"]
                },
                # Санкт-Петербург (region_id: 79) – 3 компании
                {
                    "name": "Модный Стиль",
                    "email": "modnyystil@mail.ru",
                    "description": "Бутик современной одежды для молодой аудитории.",
                    "slogan": "Стиль – это жизнь.",
                    "region_id": 79,
                    "legal_address": "г. Санкт-Петербург, ул. Невская, д. 20",
                    "actual_address": "г. Санкт-Петербург, ул. Невская, д. 20",
                    "phone_num": 78121232012,
                    "employees": 25,
                    "year_founded": datetime.date(2013, 5, 5),
                    "website": "https://modnyystil.ru",
                    "logo_url": "static/companies/modnyystil_logo.png",
                    "inn": "2345609871",
                    "kpp": "234560987",
                    "ogrn": "2345609871234",
                    "oktmo": "23456098",
                    "okpo": "23456098",
                    "director_full_name": "Федоров Олег Иванович",
                    "social_media_links": ["https://vk.com/modnyystil", "https://t.me/modnyystil"]
                },
                {
                    "name": "Бутик Элеганс",
                    "email": "elegance@mail.ru",
                    "description": "Магазин эксклюзивной женской одежды и аксессуаров.",
                    "slogan": "Элегантность в каждой детали.",
                    "region_id": 79,
                    "legal_address": "г. Санкт-Петербург, ул. Марата, д. 15",
                    "actual_address": "г. Санкт-Петербург, ул. Марата, д. 15",
                    "phone_num": 78121232013,
                    "employees": 18,
                    "year_founded": datetime.date(2014, 10, 10),
                    "website": "https://elegance.ru",
                    "logo_url": "static/companies/elegance_logo.png",
                    "inn": "3456098712",
                    "kpp": "345609871",
                    "ogrn": "3456098712345",
                    "oktmo": "34560987",
                    "okpo": "34560987",
                    "director_full_name": "Ковалев Артем Сергеевич",
                    "social_media_links": ["https://vk.com/elegance", "https://t.me/elegance"]
                },
                {
                    "name": "Ателье Мода",
                    "email": "atelie_moda@mail.ru",
                    "description": "Небольшое ателье по пошиву и ремонту одежды.",
                    "slogan": "Индивидуальный подход к стилю.",
                    "region_id": 79,
                    "legal_address": "г. Санкт-Петербург, ул. Советская, д. 7",
                    "actual_address": "г. Санкт-Петербург, ул. Советская, д. 7",
                    "phone_num": 78121232014,
                    "employees": 12,
                    "year_founded": datetime.date(2015, 7, 7),
                    "website": "https://atelie-moda.ru",
                    "logo_url": "static/companies/atelie_moda_logo.png",
                    "inn": "4567098712",
                    "kpp": "456709871",
                    "ogrn": "4567098712345",
                    "oktmo": "45670987",
                    "okpo": "45670987",
                    "director_full_name": "Зайцев Борис Викторович",
                    "social_media_links": ["https://vk.com/ateliemoda", "https://t.me/ateliemoda"]
                },
                # Краснодарский край (region_id: 26) – 2 компании
                {
                    "name": "ЭкоМаркет",
                    "email": "ekomarket@mail.ru",
                    "description": "Магазин натуральных и экологически чистых продуктов питания.",
                    "slogan": "Забота о природе и вас.",
                    "region_id": 26,
                    "legal_address": "г. Краснодар, ул. Северная, д. 15",
                    "actual_address": "г. Краснодар, ул. Северная, д. 15",
                    "phone_num": 78512232015,
                    "employees": 40,
                    "year_founded": datetime.date(2013, 4, 1),
                    "website": "https://ekomarket.ru",
                    "logo_url": "static/companies/ekomarket_logo.png",
                    "inn": "5678098712",
                    "kpp": "567809871",
                    "ogrn": "5678098712345",
                    "oktmo": "56780987",
                    "okpo": "56780987",
                    "director_full_name": "Михайлов Евгений Петрович",
                    "social_media_links": ["https://vk.com/ekomarket", "https://t.me/ekomarket"]
                },
                {
                    "name": "ФрешМаркет",
                    "email": "freshmarket@mail.ru",
                    "description": "Небольшая сеть магазинов свежих продуктов и деликатесов.",
                    "slogan": "Свежесть каждый день.",
                    "region_id": 26,
                    "legal_address": "г. Краснодар, ул. Красная, д. 22",
                    "actual_address": "г. Краснодар, ул. Красная, д. 22",
                    "phone_num": 78512232016,
                    "employees": 35,
                    "year_founded": datetime.date(2014, 6, 15),
                    "website": "https://freshmarket.ru",
                    "logo_url": "static/companies/freshmarket_logo.png",
                    "inn": "6789087123",
                    "kpp": "678908712",
                    "ogrn": "6789087123456",
                    "oktmo": "67890871",
                    "okpo": "67890871",
                    "director_full_name": "Смирнов Денис Александрович",
                    "social_media_links": ["https://vk.com/freshmarket", "https://t.me/freshmarket"]
                },
                # Иркутская область (region_id: 42) – 2 компании
                {
                    "name": "Рыбный Мир",
                    "email": "rybnymir@mail.ru",
                    "description": "Магазин свежей рыбы и морепродуктов с доставкой по городу.",
                    "slogan": "Свежесть моря у вас дома.",
                    "region_id": 42,
                    "legal_address": "г. Иркутск, ул. Советская, д. 7",
                    "actual_address": "г. Иркутск, ул. Советская, д. 7",
                    "phone_num": 73412232017,
                    "employees": 28,
                    "year_founded": datetime.date(2012, 9, 9),
                    "website": "https://rybnyimir.ru",
                    "logo_url": "static/companies/rybnymir_logo.png",
                    "inn": "7890871234",
                    "kpp": "789087123",
                    "ogrn": "7890871234567",
                    "oktmo": "78908712",
                    "okpo": "78908712",
                    "director_full_name": "Орлов Владимир Сергеевич",
                    "social_media_links": ["https://vk.com/rybnymir", "https://t.me/rybnymir"]
                },
                {
                    "name": "Винный Двор",
                    "email": "vinnydvor@mail.ru",
                    "description": "Специализированный магазин с широким выбором вин и алкогольной продукции.",
                    "slogan": "Вино для истинных ценителей.",
                    "region_id": 42,
                    "legal_address": "г. Иркутск, ул. Ленина, д. 3",
                    "actual_address": "г. Иркутск, ул. Ленина, д. 3",
                    "phone_num": 73412232018,
                    "employees": 20,
                    "year_founded": datetime.date(2013, 11, 20),
                    "website": "https://vinnydvor.ru",
                    "logo_url": "static/companies/vinnydvor_logo.png",
                    "inn": "8908712345",
                    "kpp": "890871234",
                    "ogrn": "8908712345678",
                    "oktmo": "89087123",
                    "okpo": "89087123",
                    "director_full_name": "Титов Юрий Николаевич",
                    "social_media_links": ["https://vk.com/vinnydvor", "https://t.me/vinnydvor"]
                },
                # Калужская область (region_id: 44) – 2 компании
                {
                    "name": "Книжный Дом",
                    "email": "knizhnymdom@mail.ru",
                    "description": "Небольшая сеть книжных магазинов с богатым выбором литературы.",
                    "slogan": "Знание – сила.",
                    "region_id": 44,
                    "legal_address": "г. Калуга, ул. Ленина, д. 3",
                    "actual_address": "г. Калуга, ул. Ленина, д. 3",
                    "phone_num": 48412232019,
                    "employees": 22,
                    "year_founded": datetime.date(2011, 2, 2),
                    "website": "https://knizhnymdom.ru",
                    "logo_url": "static/companies/knizhnymdom_logo.png",
                    "inn": "9087123456",
                    "kpp": "908712345",
                    "ogrn": "9087123456789",
                    "oktmo": "90871234",
                    "okpo": "90871234",
                    "director_full_name": "Беляев Антон Викторович",
                    "social_media_links": ["https://vk.com/knizhnymdom", "https://t.me/knizhnymdom"]
                },
                {
                    "name": "АртЛайн Дизайн",
                    "email": "artlaindesign@mail.ru",
                    "description": "Студия дизайна, предоставляющая услуги по оформлению интерьеров и брендингу.",
                    "slogan": "Креативные решения для вашего пространства.",
                    "region_id": 44,
                    "legal_address": "г. Калуга, ул. Победы, д. 10",
                    "actual_address": "г. Калуга, ул. Победы, д. 10",
                    "phone_num": 48412232020,
                    "employees": 18,
                    "year_founded": datetime.date(2012, 8, 18),
                    "website": "https://artlaindesign.ru",
                    "logo_url": "static/companies/artlaindesign_logo.png",
                    "inn": "0871234567",
                    "kpp": "087123456",
                    "ogrn": "0871234567890",
                    "oktmo": "08712345",
                    "okpo": "08712345",
                    "director_full_name": "Лазарев Максим Олегович",
                    "social_media_links": ["https://vk.com/artlaindesign", "https://t.me/artlaindesign"]
                },
                # Нижегородская область (region_id: 55) – 2 компании
                {
                    "name": "Мастер Плюс",
                    "email": "masterplus@mail.ru",
                    "description": "Сервис по ремонту и обслуживанию бытовой техники и электроники.",
                    "slogan": "Профессионально и вовремя.",
                    "region_id": 55,
                    "legal_address": "г. Нижний Новгород, ул. Минина, д. 8",
                    "actual_address": "г. Нижний Новгород, ул. Минина, д. 8",
                    "phone_num": 74951232021,
                    "employees": 32,
                    "year_founded": datetime.date(2014, 12, 1),
                    "website": "https://masterplus.ru",
                    "logo_url": "static/companies/masterplus_logo.png",
                    "inn": "8712345678",
                    "kpp": "871234567",
                    "ogrn": "8712345678901",
                    "oktmo": "87123456",
                    "okpo": "87123456",
                    "director_full_name": "Пономарев Илья Сергеевич",
                    "social_media_links": ["https://vk.com/masterplus", "https://t.me/masterplus"]
                },
                {
                    "name": "Ремонт+ Сервис",
                    "email": "remontplus@mail.ru",
                    "description": "Небольшая компания, оказывающая услуги по ремонту квартир и офисов.",
                    "slogan": "Делаем ваш дом уютнее.",
                    "region_id": 55,
                    "legal_address": "г. Нижний Новгород, ул. Советская, д. 6",
                    "actual_address": "г. Нижний Новгород, ул. Советская, д. 6",
                    "phone_num": 74951232022,
                    "employees": 28,
                    "year_founded": datetime.date(2015, 3, 22),
                    "website": "https://remontplus.ru",
                    "logo_url": "static/companies/remontplus_logo.png",
                    "inn": "7123456789",
                    "kpp": "712345678",
                    "ogrn": "7123456789012",
                    "oktmo": "71234567",
                    "okpo": "71234567",
                    "director_full_name": "Крылов Станислав Павлович",
                    "social_media_links": ["https://vk.com/remontplus", "https://t.me/remontplus"]
                },
                # Рязанская область (region_id: 64) – 2 компании
                {
                    "name": "СпортЛэнд",
                    "email": "sportland@mail.ru",
                    "description": "Магазин спортивных товаров для активного образа жизни.",
                    "slogan": "Будь в форме!",
                    "region_id": 64,
                    "legal_address": "г. Рязань, ул. Гагарина, д. 11",
                    "actual_address": "г. Рязань, ул. Гагарина, д. 11",
                    "phone_num": 74951232023,
                    "employees": 30,
                    "year_founded": datetime.date(2013, 7, 7),
                    "website": "https://sportland.ru",
                    "logo_url": "static/companies/sportland_logo.png",
                    "inn": "1234567809",
                    "kpp": "123456780",
                    "ogrn": "1234567809123",
                    "oktmo": "12345678",
                    "okpo": "12345678",
                    "director_full_name": "Шаров Константин Иванович",
                    "social_media_links": ["https://vk.com/sportland", "https://t.me/sportland"]
                },
                {
                    "name": "Фитнес Центр \"Энерджи\"",
                    "email": "energyfitness@mail.ru",
                    "description": "Небольшой фитнес-центр с современным оборудованием и групповыми программами.",
                    "slogan": "Энергия для жизни.",
                    "region_id": 64,
                    "legal_address": "г. Рязань, ул. Лесная, д. 5",
                    "actual_address": "г. Рязань, ул. Лесная, д. 5",
                    "phone_num": 74951232024,
                    "employees": 25,
                    "year_founded": datetime.date(2016, 5, 10),
                    "website": "https://energyfitness.ru",
                    "logo_url": "static/companies/energyfitness_logo.png",
                    "inn": "2345678091",
                    "kpp": "234567809",
                    "ogrn": "2345678091234",
                    "oktmo": "23456780",
                    "okpo": "23456780",
                    "director_full_name": "Романов Алексей Дмитриевич",
                    "social_media_links": ["https://vk.com/energyfitness", "https://t.me/energyfitness"]
                },
                # Ярославская область (region_id: 77) – 1 компания
                {
                    "name": "Домашний Уют",
                    "email": "domashniyuut@mail.ru",
                    "description": "Компания по производству и продаже мебели, текстиля и декора для дома.",
                    "slogan": "Создайте уют в своем доме.",
                    "region_id": 77,
                    "legal_address": "г. Ярославль, ул. Советская, д. 14",
                    "actual_address": "г. Ярославль, ул. Советская, д. 14",
                    "phone_num": 48512232025,
                    "employees": 40,
                    "year_founded": datetime.date(2014, 10, 30),
                    "website": "https://domashniyuut.ru",
                    "logo_url": "static/companies/domashniyuut_logo.png",
                    "inn": "3456780912",
                    "kpp": "345678091",
                    "ogrn": "3456780912345",
                    "oktmo": "34567809",
                    "okpo": "34567809",
                    "director_full_name": "Герасимов Николай Васильевич",
                    "social_media_links": ["https://vk.com/domashniyuut", "https://t.me/domashniyuut"]
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
                    legal_address=data["legal_address"],
                    actual_address=data["actual_address"],
                    logo_url=data["logo_url"],
                    employees=data["employees"],
                    year_founded=data["year_founded"],
                    website=data["website"],
                    inn=data["inn"],
                    kpp=data["kpp"],
                    ogrn=data["ogrn"],
                    oktmo=data["oktmo"],
                    okpo=data["okpo"],
                    director_full_name=data["director_full_name"],
                    social_media_links=data["social_media_links"],
                    partner_companies=[],  # Оставляем пустым
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