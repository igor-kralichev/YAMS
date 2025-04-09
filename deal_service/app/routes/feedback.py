from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.db.session import get_db
from shared.moderation.profanity_filter import filter
from shared.services.auth import get_current_account
from shared.db.models import Feedback_Model, Deal_Model, Account_Model
from shared.db.models.deal_consumers import DealConsumers as deal_consumers
from shared.db.schemas.feedback import FeedbackCreate, Feedback as FeedbackSchema

router = APIRouter()

@router.get(
    "/{deal_id}",
    response_model=list[FeedbackSchema],
    summary="GET отзывы по сделке",
    description=(
        "Получение списка всех отзывов, связанных с указанной сделкой."
    )
)
async def get_feedbacks_for_deal(
    deal_id: int,
    db: AsyncSession = Depends(get_db)
):
    # Проверяем, существует ли сделка
    deal_result = await db.execute(
        select(Deal_Model)
        .where(Deal_Model.id == deal_id)
    )
    deal = deal_result.scalar_one_or_none()

    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")

    # Получаем все отзывы для этой сделки
    feedbacks_result = await db.execute(
        select(Feedback_Model)
        .where(Feedback_Model.deal_id == deal_id)
        .order_by(Feedback_Model.created_at.desc())
    )
    feedbacks = feedbacks_result.scalars().all()

    return feedbacks

@router.post(
    "/create-feedback/{deal_id}",
    response_model=FeedbackSchema,
    summary="POST на создание отзыва",
    description=(
        "Добавление отзыва на сделку. Пользователи, которые покупали сделку, помечаются меткой is_purchaser."
    )
)
async def create_feedback(
    feedback_data: FeedbackCreate,
    deal_id: int,  # Добавляем deal_id как параметр пути
    db: AsyncSession = Depends(get_db),
    current_account: Account_Model = Depends(get_current_account)
):
    # Получаем сделку
    deal_result = await db.execute(
        select(Deal_Model)
        .where(Deal_Model.id == deal_id)
    )
    deal = deal_result.scalar_one_or_none()

    if not deal:
        raise HTTPException(status_code=404, detail="Сделка не найдена")

    # Проверка, что пользователь не является продавцом
    if deal.seller_id == current_account.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Продавец не может оставлять отзыв о своей сделке"
        )

    # Проверка существующего отзыва
    existing_feedback = await db.execute(
        select(Feedback_Model)
        .where(Feedback_Model.deal_id == deal_id)
        .where(Feedback_Model.author_id == current_account.id)
    )
    if existing_feedback.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вы уже оставили отзыв для этой сделки"
        )

    # Проверка на матные слова
    if not filter.is_clean_exact(feedback_data.details):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Маты это плохо"
        )

    # Проверяем, покупал ли пользователь эту сделку
    purchase_check = await db.execute(
        select(deal_consumers)
        .where(deal_consumers.c.deal_id == deal_id)
        .where(deal_consumers.c.consumer_id == current_account.id)
    )
    is_purchaser = purchase_check.first() is not None

    # Создание отзыва
    new_feedback = Feedback_Model(
        deal_id=deal_id,
        stars=feedback_data.stars,
        details=feedback_data.details,
        author_id=current_account.id,
        is_purchaser=is_purchaser  # Устанавливаем метку
    )

    db.add(new_feedback)
    await db.commit()
    await db.refresh(new_feedback)

    return new_feedback