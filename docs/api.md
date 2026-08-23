# API Reference

## Auth

- `POST /api/v1/auth/register` — регистрация (phone, email, password, full_name)
- `POST /api/v1/auth/login` — вход (email, password) → {access_token, refresh_token}
- `POST /api/v1/auth/refresh` — обновление токена
- `POST /api/v1/auth/logout` — выход (refresh_token)
- `GET /api/v1/auth/me` — профиль текущего пользователя

## Stations

- `GET /api/v1/stations` — список (q, status, power, tariff_max, open_24, booking, venue)
- `GET /api/v1/stations/{public_id}` — детали станции
- `GET /api/v1/stations/{public_id}/reviews` — отзывы
- `GET /api/v1/stations/{public_id}/availability` — статус + бронирования
- `POST /api/v1/stations/{public_id}/booking` — создать бронирование
- `POST /api/v1/stations/{public_id}/telemetry` — телеметрия (device auth)
- `POST /api/v1/stations/{public_id}/heartbeat` — heartbeat (device auth)
- `GET /api/v1/stations/{public_id}/commands/next` — polling команд (device auth)
- `POST /api/v1/stations/{public_id}/command-result` — результат команды (device auth)

## Charging

- `POST /api/v1/charging-sessions/quote` — расчёт стоимости
- `POST /api/v1/charging-sessions/start` — старт сессии
- `POST /api/v1/charging-sessions/{id}/stop` — стоп сессии
- `POST /api/v1/charging-sessions/{id}/extend` — продление лимита
- `GET /api/v1/charging-sessions/{id}` — детали сессии
- `GET /api/v1/charging-sessions/me` — мои сессии

## Payments

- `POST /api/v1/payments/create` — создание платежа (session_id, method)
- `POST /api/v1/payments/webhook/{provider}` — вебхук от провайдера
- `POST /api/v1/payments/mock/{id}/simulate-success` — симуляция успешной оплаты (mock)
- `GET /api/v1/payments/me` — мои платежи
- `GET /api/v1/payments/{id}/receipt` — чек

## Bookings

- `GET /api/v1/bookings/me` — мои бронирования
- `DELETE /api/v1/bookings/{id}` — отмена бронирования

## Support

- `POST /api/v1/support/tickets` — создать тикет
- `GET /api/v1/support/tickets/me` — мои тикеты

## Operator

- `GET /api/v1/operator/stations` — мои станции
- `GET /api/v1/operator/stats` — статистика
- `GET /api/v1/operator/faults` — журнал ошибок
- `PATCH /api/v1/operator/stations/{public_id}` — обновление станции
- `PATCH /api/v1/operator/locations/{loc_id}` — обновление локации
- `POST /api/v1/operator/stations` — добавить станцию
- `POST /api/v1/operator/stations/{public_id}/photos` — добавить фото
- `GET /api/v1/operator/payments` — платежи
- `GET /api/v1/operator/export.csv` — экспорт CSV

## Admin

- `GET /api/v1/admin/users` — пользователи
- `PATCH /api/v1/admin/users/{user_id}` — редактирование
- `GET /api/v1/admin/stations` — все станции
- `POST /api/v1/admin/stations/{public_id}/lock` — lock/unlock
- `GET /api/v1/admin/commands` — история команд
- `GET /api/v1/admin/payments` — все платежи
- `POST /api/v1/admin/payments/{id}/refund` — возврат
- `GET /api/v1/admin/sessions` — сессии
- `GET /api/v1/admin/audit` — аудит-лог
- `GET /api/v1/admin/equipment-errors` — ошибки оборудования
- `GET /api/v1/admin/moderation/photos` — фото на модерации
- `PATCH /api/v1/admin/moderation/photos/{id}` — модерация фото
- `GET /api/v1/admin/moderation/reviews` — отзывы на модерации
- `PATCH /api/v1/admin/moderation/reviews/{id}` — модерация отзыва
- `GET /api/v1/admin/commissions` — комиссии
- `PUT /api/v1/admin/commissions` — установка комиссии

## WebSocket

- `WS /ws/stations/{public_id}` — канал станции (команды, статусы)
- `WS /ws/users/{user_id}/sessions?token=...` — канал пользователя (обновления сессий)
