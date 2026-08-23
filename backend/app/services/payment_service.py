import hashlib
import hmac
import json
import logging
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.providers.mock_provider import MockPaymentProvider
from app.providers.registry import get_payment_provider
from app.utils.audit import audit
from app.utils.ids import uid

log = logging.getLogger("payments")

Q2 = Decimal("0.01")


def money(v: Decimal | float | int) -> Decimal:
    return Decimal(v).quantize(Q2, rounding=ROUND_HALF_UP)


async def create_payment_for_session(
    db: AsyncSession, *, user_id: str, session_id: str, amount: Decimal,
    method: str, description: str, return_url: str = "",
    idempotency_key: str | None = None,
):
    """Идемпотентно создаёт Payment(status=pending) через провайдера."""
    from app.models.payment import Payment
    from app.models.enums import PaymentMethod, PaymentStatus

    key = idempotency_key or f"pay:{session_id}:{method}"
    existing = (await db.execute(select(Payment).where(Payment.idempotency_key == key))).scalar_one_or_none()
    if existing is not None:
        return existing, None

    provider = get_payment_provider()
    pp = await provider.create_payment(
        amount=money(amount), currency="RUB", description=description,
        return_url=return_url, idempotency_key=key,
        metadata={"session_id": session_id},
    )

    payment = Payment(
        id=uid(), user_id=user_id, session_id=session_id,
        provider=provider.name, provider_payment_id=pp.provider_payment_id,
        method=PaymentMethod(method), amount=money(amount), currency="RUB",
        status=PaymentStatus.pending, idempotency_key=key,
        description=description,
    )
    confirmation = None
    if isinstance(provider, MockPaymentProvider):
        confirmation = await provider.build_confirmation(method, payment.id, return_url)
        payment.sbp_payload = confirmation.sbp_payload
        payment.confirmation_url = confirmation.url
    db.add(payment)
    await db.flush()
    await audit(db, "payment.created", actor_id=user_id, entity_type="payment",
                entity_id=payment.id, meta={"amount": str(amount), "method": method})
    return payment, confirmation


async def process_succeeded(db: AsyncSession, payment) -> None:
    """Единая точка обработки успешной оплаты: идемпотентна.
    Запуск станции возможен тОЛьКО отсюда."""
    from app.models.enums import PaymentStatus
    from app.services.charging_service import confirm_after_payment

    if payment.status == PaymentStatus.succeeded:
        return  # идемпотентность повторных вебхуков
    payment.status = PaymentStatus.succeeded
    from app.db.base import utcnow
    payment.paid_at = utcnow()
    await audit(db, "payment.succeeded", actor_id=None, entity_type="payment",
                entity_id=payment.id, meta={"provider_payment_id": payment.provider_payment_id})
    if payment.session_id:
        await confirm_after_payment(db, payment)


async def handle_webhook(db: AsyncSession, provider_name: str, headers: dict, body: bytes) -> dict:
    from app.models.payment import Payment, PaymentWebhook
    from app.models.enums import PaymentStatus

    provider = get_payment_provider(provider_name)
    event = await provider.verify_webhook(headers, body)

    wh = PaymentWebhook(id=uid(), provider=provider_name, event_type=event.get("event", ""),
                         provider_payment_id=event.get("payment_id"), payload=event)
    db.add(wh)

    payment = (await db.execute(
        select(Payment).where(Payment.provider_payment_id == event["payment_id"])
    )).scalar_one_or_none()
    if payment is None:
        wh.error = "payment_not_found"
        return {"ok": True, "note": "payment_not_found"}

    if event["event"] == "payment.succeeded":
        await process_succeeded(db, payment)
    elif event["event"] == "payment.canceled":
        payment.status = PaymentStatus.cancelled
    elif event["event"] == "payment.refunded":
        payment.status = PaymentStatus.refunded
    wh.processed = True
    return {"ok": True}


def verify_mock_signature(headers: dict, body: bytes) -> None:
    sig = hmac.new(settings.PAYMENT_WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, headers.get("x-mock-signature", "")):
        raise PermissionError("bad signature")


def build_mock_webhook_body(provider_payment_id: str, event: str = "payment.succeeded") -> bytes:
    return json.dumps({"event": event, "payment_id": provider_payment_id}).encode()
