from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_driver
from app.core.config import settings
from app.db.session import get_db
from app.models import User
from app.models.charging import ChargingSession
from app.models.enums import PaymentMethod, SessionStatus
from app.models.payment import Payment, Receipt
from app.models.station import Station
from app.providers.mock_provider import MockPaymentProvider
from app.schemas.payment import CheckoutOut
from app.services.payment_service import build_mock_webhook_body, create_payment_for_session, handle_webhook, money

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/create", response_model=CheckoutOut)
async def create_payment(data: dict, user: User = Depends(require_driver), db: AsyncSession = Depends(get_db)):
    session_id, method = data.get("session_id"), data.get("method", "sbp_qr")
    return_url = data.get("return_url", "")
    session = await db.get(ChargingSession, session_id) if session_id else None
    if not session or session.user_id != user.id:
        raise HTTPException(404, "Не найдено")
    if session.status != SessionStatus.awaiting_payment:
        raise HTTPException(409, "Сессия уже оплачена или отменена")

    if session.selected_limit_type.value == "rub":
        amount = session.selected_limit_value
    elif session.selected_limit_type.value == "kwh":
        amount = session.selected_limit_value * session.tariff_per_kwh
    else:
        st = await db.get(Station, session.station_id)
        power = float(st.max_power_kw) if st else 7.4
        if session.selected_limit_type.value == "minutes":
            est_kwh = Decimal(str(power * 0.92)) * session.selected_limit_value / Decimal(60)
        else:  # until_stop -- оценка на 4 часа
            est_kwh = Decimal(str(power * 0.92 * 4))
        amount = est_kwh * session.tariff_per_kwh

    payment, confirmation = await create_payment_for_session(
        db, user_id=str(user.id), session_id=session.id, amount=money(amount),
        method=method if method in PaymentMethod._value2member_map_ else "sbp_qr",
        description=f"Зарядка, сессия {session.id[:8]}", return_url=return_url)
    session.payment_id = payment.id
    await db.commit()
    await db.refresh(payment)
    conf = confirmation or _confirmation_from_payment(payment)
    return CheckoutOut(payment=payment, confirmation=conf)


def _confirmation_from_payment(p: Payment) -> dict:
    if p.method.value == "sbp_qr":
        return {"type": "sbp_qr", "sbp_payload": p.sbp_payload}
    if p.method.value == "sbp_deeplink":
        return {"type": "sbp_deeplink", "url": p.confirmation_url}
    return {"type": "redirect", "url": p.confirmation_url}


@router.post("/webhook/{provider}")
async def webhook(provider: str, request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}
    try:
        result = await handle_webhook(db, provider, headers, body)
        await db.commit()
        return result
    except PermissionError:
        raise HTTPException(403, "Неверная подпись")
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.post("/mock/{payment_id}/simulate-success")
async def simulate_success(payment_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(require_driver)):
    """Для dev-стенда: эмулирует успешный webhook."""
    if settings.PAYMENT_PROVIDER != "mock":
        raise HTTPException(404, "Доступно только в режиме mock")
    payment = await db.get(Payment, payment_id)
    if not payment or payment.user_id != user.id:
        raise HTTPException(404, "Не найдено")
    body = build_mock_webhook_body(payment.provider_payment_id or payment.id)
    sig = MockPaymentProvider.sign(body)
    result = await handle_webhook(db, "mock", {"x-mock-signature": sig}, body)
    await db.commit()
    return result


@router.get("/me", response_model=list)
async def my_payments(user: User = Depends(require_driver), db: AsyncSession = Depends(get_db)):
    return (await db.execute(select(Payment).where(Payment.user_id == user.id)
                              .order_by(Payment.created_at.desc()).limit(100))).scalars().all()


@router.get("/{payment_id}/receipt")
async def receipt(payment_id: str, user: User = Depends(require_driver), db: AsyncSession = Depends(get_db)):
    pay = await db.get(Payment, payment_id)
    if not pay or pay.user_id != user.id:
        raise HTTPException(404, "Не найдено")
    rc = (await db.execute(select(Receipt).where(Receipt.payment_id == payment_id)
                            .order_by(Receipt.created_at.desc()))).scalars().first()
    if not rc:
        raise HTTPException(404, "Чек пока не готов")
    return {"number": rc.number, **rc.data}
