# Архитектура Pear Energy

См. общую схему и ключевые потоки в корневом `README.md`.

## Компоненты

- **Backend** (`backend/`): FastAPI (async), SQLAlchemy 2.0 + asyncpg, Alembic-миграции, JWT/RBAC (driver/operator/admin), Redis для кэша, rate-limit и WebSocket pub/sub.
- **Frontend** (`frontend/`): Next.js 15 App Router, TypeScript, Tailwind, React Hook Form + Zod, Zustand, Yandex Maps.
- **Станции**: ESP32 либо опрашивают `GET /api/v1/stations/{public_id}/commands/next` (режим `http`), либо эмулируются `MockStationGateway` + `SimulatorManager` (режим `mock`).

## Модели данных (13+ таблиц)

User, Vehicle, Location, Station, Connector, ChargingSession, PaymentIntent, Payment, PaymentWebhook, Refund, Receipt, Booking, StationTelemetry, StationCommand, AuditLog, Review, StationPhoto, Favorite, Notification, SupportTicket, Setting.

## Основной сценарий зарядки

1. Клиент запрашивает `quote` (оценка стоимости/времени/энергии по выбранному лимиту: kWh, рубли, минуты, до отключения).
2. `POST /charging-sessions/start` создаёт сессию в статусе `awaiting_payment`.
3. `POST /payments/create` создаёт `Payment` через `PaymentProvider` (мок генерирует QR СБП/deeplink/redirect).
4. Провайдер подтверждает оплату вебхуком (HMAC-подпись) → `payment_service.process_succeeded` идемпотентно переводит сессию в `preparing` и ставит `StationCommand(type=start)`.
5. Станция получает команду (polling `commands/next` либо мок-симулятор запускается напрямую) и присылает `command-result`.
6. Пока идёт зарядка, станция публикует `telemetry`; `watchdog` фоновым тиком проверяет лимиты по времени, потерю связи (>5 мин) и зависшие `awaiting_payment` сессии (>30 мин).
7. Остановка (по лимиту, пользователю, неисправности) финализирует сессию, считает `energy_kwh`/`total_amount`, создаёт чек `Receipt` и уведомление.

## Планы по замене моков

- Платёжный провайдер: реализовать `YooKassaProvider`/`TinkoffPayProvider` по интерфейсу `PaymentProvider` (`backend/app/providers/base.py`) и зарегистрировать в `providers/registry.py`.
- Реальные станции: `HttpStationGateway` уже умеет опрашивать статус станции; протокол `commands/next` / `command-result` / `telemetry` / `heartbeat` уже реализован в `api/v1/stations.py` — прошивка ESP32 подключается по токену устройства (`X-Station-Token`).
