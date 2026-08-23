from app.providers.base import PaymentProvider
from app.providers.mock_provider import MockPaymentProvider

_REGISTRY: dict[str, PaymentProvider] = {"mock": MockPaymentProvider()}


def get_payment_provider(name: str | None = None) -> PaymentProvider:
    from app.core.config import settings
    key = name or settings.PAYMENT_PROVIDER
    if key not in _REGISTRY:
        raise RuntimeError(f"Payment provider '{key}' не зарегистрирован. "
                            f"Добавьте реализацию PaymentProvider в providers/registry.py")
    return _REGISTRY[key]


def register_provider(p: PaymentProvider) -> None:
    """точка подключения ЮKassa / Tinkoff Pay / CloudPayments без правки остального кода."""
    _REGISTRY[p.name] = p
