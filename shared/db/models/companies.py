from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, ARRAY, Index
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from shared.db.base import Base

class Company_Model(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    slogan = Column(String(255), nullable=True)
    legal_address = Column(String(255), nullable=True)
    actual_address = Column(String(255), nullable=True)
    logo_url = Column(Text, nullable=True)
    employees = Column(Integer, nullable=True)
    year_founded = Column(Date, nullable=True, index=True)
    website = Column(String(255), nullable=True)
    inn = Column(String(10), nullable=True)
    kpp = Column(String(9), nullable=True)
    ogrn = Column(String(13), nullable=True)
    oktmo = Column(String(11), nullable=True)
    okpo = Column(String(8), nullable=True)
    director_full_name = Column(String(255), nullable=True)
    social_media_links = Column(ARRAY(String), nullable=True)
    partner_companies = Column(
        ARRAY(Integer),
        nullable=True
    )
    account_id = Column(
        Integer,
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # Связи
    account = relationship("Account_Model", back_populates="company")
    top_purchases = relationship("BuyTop", back_populates="company", cascade="all, delete-orphan")

    # Определяем GIN-индекс для partner_companies
    __table_args__ = (
        Index('idx_companies_partner_companies', 'partner_companies', postgresql_using='gin'),
    )