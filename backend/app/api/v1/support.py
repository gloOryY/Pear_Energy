from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_operator
from app.db.session import get_db
from app.models import SupportTicket, User
from app.utils.ids import uid

router = APIRouter(tags=["support"])


class TicketIn(BaseModel):
    subject: str = Field(min_length=3, max_length=255)
    message: str = Field(min_length=5)
    station_public_id: str | None = None


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    subject: str
    message: str
    reply: str | None
    status: str


@router.post("/support/tickets", response_model=TicketOut, status_code=201)
async def create_ticket(data: TicketIn, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    t = SupportTicket(id=uid(), user_id=user.id, subject=data.subject, message=data.message,
                       station_id=data.station_public_id)
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return t


@router.get("/support/tickets/me", response_model=list[TicketOut])
async def my_tickets(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return (await db.execute(select(SupportTicket).where(SupportTicket.user_id == user.id)
                              .order_by(SupportTicket.created_at.desc()))).scalars().all()


@router.get("/operator/tickets", response_model=list[TicketOut])
async def all_tickets(user: User = Depends(require_operator), db: AsyncSession = Depends(get_db)):
    return (await db.execute(select(SupportTicket).order_by(SupportTicket.created_at.desc())
                              .limit(200))).scalars().all()


@router.patch("/operator/tickets/{tid}", response_model=TicketOut)
async def reply_ticket(tid: str, reply: str, user: User = Depends(require_operator), db: AsyncSession = Depends(get_db)):
    t = await db.get(SupportTicket, tid)
    if not t:
        raise HTTPException(404, "Не найдено")
    t.reply, t.status = reply, "closed"
    await db.commit()
    await db.refresh(t)
    return t
