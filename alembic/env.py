import os
import sys
from logging.config import fileConfig
from pathlib import Path
from dotenv import load_dotenv


from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context
from shared.db import models


# Alembic Config object
config = context.config

# Настройка логирования из alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Загружаем переменные окружения из .env в корне проекта
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Получаем DATABASE_URL и приводим к синхронному виду
database_url = os.getenv('DATABASE_URL')
if not database_url:
    raise RuntimeError('DATABASE_URL не найден в .env')
sync_url = database_url.replace('+asyncpg', '')
# Перезаписываем настройку в config для alembic
config.set_main_option('sqlalchemy.url', sync_url)

# Добавляем корень проекта в PYTHONPATH
sys.path.insert(0, os.path.abspath(Path(__file__).parent.parent))

# Импортируем декларативный базовый класс из вашего приложения
from shared.db.base import Base

# Указываем метаданные для автогенерации миграций
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Используем engine_from_config, он подхватит перезаписанный url
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()