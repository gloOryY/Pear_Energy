from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Confirmation:
    type: str  # sbp_qr | sbp_deeplink | redirect
    sbp_payload: str | None = None
    url: str | None = None


@dataclass
class ProviderPayment:
    provider_payment_id: str
    status: str  # pending | succeeded | failed | cancelled
    confirmation: Confirmation | None = None
    raw: dict = field(default_factory=dict)


class PaymentProvider(ABC):
    """Слой интеграции эквайринга. Сервер доверяет только webhook/verify."""
    name: str = "abstract"

    @abstractmethod
    async def create_payment(self, *, amount: Decimal, currency: str, description: str,
                              return_url: str, idempotency_key: str,
                              metadata: dict | None = None) -> ProviderPayment: ...

    @abstractmethod
    async def verify_webhook(self, headers: dict, body: bytes) -> dict:
        """Проверить подпись и распарсить событие. Бросает исключение при невалидной подписи."""

    @abstractmethod
    async def refund(self, provider_payment_id: str, amount: Decimal,
                      idempotency_key: str) -> ProviderPayment: ...

    @abstractmethod
    async def fetch_status(self, provider_payment_id: str) -> ProviderPayment: ...
