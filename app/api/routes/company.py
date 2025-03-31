from fastapi import APIRouter, Depends
from app.db.models.company import Company as CompanyModel
from app.schemas.company import Company as CompanySchema
from app.api.dependencies import get_current_company

router = APIRouter()

@router.get("/me", response_model=CompanySchema)
def read_companies_me(current_company: CompanyModel = Depends(get_current_company)):
    return current_company