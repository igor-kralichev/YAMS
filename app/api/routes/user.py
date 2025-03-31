from fastapi import APIRouter, Depends
from app.db.models.user import User as UserModel
from app.schemas.user import User as UserSchema
from app.api.dependencies import get_current_user

router = APIRouter()

@router.get("/me", response_model=UserSchema)
def read_users_me(current_user: UserModel = Depends(get_current_user)):
    return current_user