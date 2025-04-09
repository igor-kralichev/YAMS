from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from shared.db.base import Base

class User_Model(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    fullname = Column(String(255), nullable=False)       # ФИО
    photo_url = Column(String(255), nullable=True)         # Путь до фото
    # ondelete CASCADE – при удалении аккаунта удаляется пользователь
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)

    # Связи
    account = relationship("Account_Model", back_populates="user", lazy="joined")
