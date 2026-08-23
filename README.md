# Pear Energy

Платформа управления зарядными станциями для электромобилей: FastAPI backend, Next.js frontend, ESP32-станции.

## Архитектура

```
┌─────────────────────────────────────────────┐
│                 Nginx :80                    │
│  /        → frontend:3000                    │
│  /api,/ws → backend:8000                      │
└──────────────┬────────────────────────────────┘
               │
   ┌───────────┼──────────────────────────────┐
   ▼           ▼                              ▼
┌───────────┐ ┌────────────────┐   ┌────────────────┐
│ Next.js 15│ │    FastAPI      │   │  ESP32-станции │
│ App Router│ │   (async)       │   │  HTTPS polling │
│ TS/Tailwind/RHF/Zod/Zustand │◄──►│ JWT/RBAC       │◄──►│ /commands/next │
│ Yandex Maps│ │ SQLAlchemy 2.0  │   │ /telemetry     │
└───────────┘ └───┬────────┬────┘   └────────────────┘
                   │        │
            ┌──────▼─┐  ┌──▼──────────┐
            │Postgres│  │   Redis 7    │
            │16 модели│  │ кэш/pub-sub │
            └────────┘  └─────────────┘
```

### Ключевой поток «Оплата → старт зарядки»

1. `POST /charging-sessions/start` → сессия `status=awaiting_payment`
2. `POST /payments/create` → `Payment(status=pending)` через `PaymentProvider`
3. Пользователь платит (СБП QR / deeplink / карта)
4. `POST /payments/webhook/{provider}` → HMAC-проверка → `payment.status=succeeded`
5. Только тогда создаётся `StationCommand(type=start)` с идемпотентным ключом
6. Станция получает команду (polling или WebSocket) → статус транслируется клиенту по WS
7. Телеметрия обновляет метры сессии → WS пользователю

### Абстракции для замены моков на прод

- `PaymentProvider` (ABC) — сейчас `MockPaymentProvider`; в дальнейшем `YooKassaProvider`, `TinkoffPayProvider` — регистрируются по имени из `.env` (`PAYMENT_PROVIDER`).
- `StationGateway` (ABC) — `MockStationGateway` (симулятор телеметрии) и `HttpStationGateway` (реальный ESP32 сам опрашивает `commands/next`). Переключение через `STATION_MODE=mock|http`.

Безопасность: станция не доверяет backend полностью — лимиты дублируются локально в payload команды `start`; при потере связи станция сама останавливает сессию.

## Структура репозитория

```
Pear_Energy/
├── docker-compose.yml
├── .env.example
├── infra/nginx/nginx.conf
├── backend/            FastAPI приложение (app/, alembic/, tests/)
├── frontend/           Next.js 15 приложение (scaffold: конфиги, lib, ui-kit, layout)
└── docs/architecture.md
```

## Быстрый старт

```bash
cp .env.example .env
docker compose up --build
```

- Backend: http://localhost:8000/docs
- Frontend: http://localhost:3000
- Через Nginx: http://localhost

При старте backend автоматически прогоняет alembic-миграции и сид тестовых данных (`python -m app.seed`).

## Тестовые аккаунты (после seed)

| Роль | Email | Пароль |
|---|---|---|
| Водитель | driver@example.com | Password123! |
| Оператор | operator@example.com | Password123! |
| Администратор | admin@example.com | Password123! |

## Статус фронтенда

В этом коммите добавлен базовый каркас фронтенда (конфигурация, API/WS клиент, стор авторизации, UI-кит, шапка сайта). Страницы `/map`, `/stations/[id]`, `/auth/*`, `/account/*`, `/operator`, `/admin` описаны в исходном техническом задании и подлежат дальнейшей реализации по той же архитектуре (см. `docs/architecture.md`).
