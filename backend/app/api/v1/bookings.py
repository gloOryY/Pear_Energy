from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_driver
from app.db.base import utcnow
from app.db.session import get_db
from app.models import User
from app.models.booking import Booking
from app.models.enums import BookingStatus
from app.schemas.booking import BookingOut

router = APIRouter(tags=["bookings"])


@router.get("/bookings/me", response_model=list[BookingOut])
async def my_bookings(user: User = Depends(require_driver), db: AsyncSession = Depends(get_db)):
    return (await db.execute(select(Booking).where(Booking.user_id == user.id)
                              .order_by(Booking.starts_at.desc()).limit(50))).scalars().all()


@router.delete("/bookings/{bid}")
async def cancel_booking(bid: str, user: User = Depends(require_driver), db: AsyncSession = Depends(get_db)):
    b = await db.get(Booking, bid)
    if not b or b.user_id != user.id:
        raise HTTPException(404, "Не найдено")
    if b.status != BookingStatus.active:
        raise HTTPException(409, "Бронирование уже неактивно")
    if b.starts_at - utcnow() < timedelta(minutes=15):
        raise HTTPException(409, "Отменить можно не менее чем за 15 минут")
    b.status = BookingStatus.cancelled
    await db.commit()
    return {"ok": True}
