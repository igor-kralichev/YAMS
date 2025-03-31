from sqlalchemy.orm import Session
from app.db.models.user import User
from app.db.models.company import Company

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()

def get_company_by_email(db: Session, email: str) -> Company | None:
    return db.query(Company).filter(Company.email == email).first()