from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from shared.db.base import Base

class DealBranch(Base):
    __tablename__ = "deal_branch"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  # ИТ/сельское хозяйство/промышленность и т.д.

    # Связи
    deals = relationship("Deal_Model", back_populates="deal_branch")
