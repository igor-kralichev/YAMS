from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from celery import shared_task
from shared.db.models import RefreshToken, BuyTop

engine = create_engine('postgresql+asyncpg://postgres:123@localhost:5432/yams_db')
Session = sessionmaker(bind=engine)

@shared_task
async def delete_expired_tokens():
    session = Session()
    try:
        # Удаление просроченных refresh_token
        session.query(RefreshToken).filter(RefreshToken.expires_at < datetime.now()).delete()
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()