import hashlib
import hmac
import json
import uuid

from app.core.config import settings
from app.providers.base import Confirmation, PaymentProvider, ProviderPayment


class MockPaymentProvider(PaymentProvider):
    """Мок-эквайринг для локальной разработки.
    Подтверждение оплаты: POST /payments/mock/{id}/simulate-success
    прогоняет событие через тот же обработчик, что и настоящий webhook."""
    name = "mock"

    async def create_payment(self, *, amount, currency, description, return_url,
                              idempotency_key, metadata=None) -> ProviderPayment:
        pp_id = f"mock_{uuid.uuid4().hex[:20]}"
        return ProviderPayment(
            provider_payment_id=pp_id,
            status="pending",
            raw={"metadata": metadata or {}},
        )

    async def build_confirmation(self, method: str, payment_id: str, return_url: str) -> Confirmation:
        if method == "sbp_qr":
            return Confirmation(type="sbp_qr",
                                 sbp_payload=f"https://qr.nspk.ru/AS10{(abs(hash(payment_id)) % 10**10):010d}"
                                             f"?bank=100000000111")
        if method == "sbp_deeplink":
            return Confirmation(type="sbp_deeplink", url=f"bank100000000111://qr.nspk.ru/AS10MOCK{payment_id[-8:]}")
        return Confirmation(type="redirect", url=f"{return_url}?mock_payment={payment_id}")

    async def verify_webhook(self, headers: dict, body: bytes) -> dict:
        sig = hmac.new(settings.PAYMENT_WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
        provided = headers.get("x-mock-signature", "")
        if not hmac.compare_digest(sig, provided):
            raise PermissionError("Invalid webhook signature")
        event = json.loads(body)
        if event.get("event") not in {"payment.succeeded", "payment.canceled", "payment.refunded"}:
            raise ValueError("Unsupported event")
        return event

    @staticmethod
    def sign(body: bytes) -> str:
        return hmac.new(settings.PAYMENT_WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()

    async def refund(self, provider_payment_id, amount, idempotency_key) -> ProviderPayment:
        return ProviderPayment(provider_payment_id=provider_payment_id, status="refunded")

    async def fetch_status(self, provider_payment_id: str) -> ProviderPayment:
        return ProviderPayment(provider_payment_id=provider_payment_id, status="pending")
