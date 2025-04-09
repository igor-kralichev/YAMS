from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey
from sqlalchemy.orm import relationship
from shared.db.base import Base

class Company_Model(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)          # Название конторы
    description = Column(Text, nullable=True)             # Описание конторы
    slogan = Column(String(255), nullable=True)           # Слоган
    address = Column(String(255), nullable=True)          # Адрес
    logo_url = Column(Text, nullable=True)                # Путь до лого
    employees = Column(Integer, nullable=True)            # Количество сотрудников
    year_founded = Column(Date, nullable=True)            # Год основания
    website = Column(String(255), nullable=True)          # Ссылка на сайт
    # ondelete CASCADE – если удалится аккаунт, то и связь с компанией исчезнет
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=True)

    # Связи
    account = relationship("Account_Model", back_populates="company")
    top_purchases = relationship("BuyTop", back_populates="company", cascade="all, delete-orphan")
