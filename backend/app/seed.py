"""Скрипт первичного наполнения базы данных (Seed Data).

Заполняет начальных пользователей (включая администратора),
тестовые станции зарядки и справочник заводских характеристик электромобилей.
"""

import asyncio
import logging
from typing import Any, Dict

from sqlalchemy import select

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed")

# 1. Безопасный импорт фабрики сессий
try:
    from app.db.session import async_session_maker
except ImportError:
    try:
        from app.db.session import AsyncSessionLocal as async_session_maker
    except ImportError as e:
        logger.error(
            "Не удалось импортировать фабрику сессий из app.db.session. "
            "Убедитесь, что объявлен async_session_maker или AsyncSessionLocal."
        )
        raise e

# 2. Безопасный импорт хэширования паролей
try:
    from app.core.security import get_password_hash
except ImportError:
    try:
        from app.core.security import hash_password as get_password_hash
    except ImportError:
        from passlib.context import CryptContext

        _pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        def get_password_hash(password: str) -> str:
            return _pwd_context.hash(password)


import uuid

# 3. Безопасный импорт моделей и перечислений
try:
    from app.models.user import User
    from app.models.enums import UserRole, ConnectorType, StationStatus
except ImportError:
    from app.models import User
    from app.models.enums import UserRole
    ConnectorType, StationStatus = None, None

try:
    from app.models.station import Station
except ImportError:
    try:
        from app.models import Station
    except ImportError:
        Station = None

try:
    from app.models.car import CarCatalog, UserCar
except ImportError:
    try:
        from app.models import CarCatalog, UserCar
    except ImportError:
        CarCatalog, UserCar = None, None

# 4. Безопасный импорт каталога авто
try:
    from app.services.car_catalog_data import CARS_CATALOG
except Exception as e:
    logger.warning(
        f"Не удалось загрузить CARS_CATALOG из app.services ({e}). "
        f"Используем встроенный резервный список авто."
    )
    CARS_CATALOG = [
        {
            "make": "Zeekr",
            "model": "001 (100 кВт·ч)",
            "battery_capacity_kwh": 100.0,
            "max_ac_power_kw": 22.0,
            "max_dc_power_kw": 200.0,
            "connector_type": "GB/T",
        },
        {
            "make": "Zeekr",
            "model": "X",
            "battery_capacity_kwh": 66.0,
            "max_ac_power_kw": 11.0,
            "max_dc_power_kw": 150.0,
            "connector_type": "GB/T",
        },
        {
            "make": "Geely",
            "model": "EX5 / Galaxy E5",
            "battery_capacity_kwh": 60.2,
            "max_ac_power_kw": 11.0,
            "max_dc_power_kw": 85.0,
            "connector_type": "GB/T",
        },
        {
            "make": "Tesla",
            "model": "Model 3 Long Range",
            "battery_capacity_kwh": 78.1,
            "max_ac_power_kw": 11.0,
            "max_dc_power_kw": 250.0,
            "connector_type": "CCS2",
        },
        {
            "make": "Tesla",
            "model": "Model Y Long Range",
            "battery_capacity_kwh": 78.1,
            "max_ac_power_kw": 11.0,
            "max_dc_power_kw": 250.0,
            "connector_type": "CCS2",
        },
        {
            "make": "BYD",
            "model": "Song Plus EV",
            "battery_capacity_kwh": 71.7,
            "max_ac_power_kw": 7.0,
            "max_dc_power_kw": 90.0,
            "connector_type": "GB/T",
        },
        {
            "make": "BYD",
            "model": "Han EV",
            "battery_capacity_kwh": 85.4,
            "max_ac_power_kw": 11.0,
            "max_dc_power_kw": 120.0,
            "connector_type": "GB/T",
        },
        {
            "make": "Li Auto",
            "model": "L7 / L8 / L9 (REEV)",
            "battery_capacity_kwh": 42.8,
            "max_ac_power_kw": 7.0,
            "max_dc_power_kw": 75.0,
            "connector_type": "GB/T",
        },
        {
            "make": "Volkswagen",
            "model": "ID.4 Crozz",
            "battery_capacity_kwh": 84.8,
            "max_ac_power_kw": 11.0,
            "max_dc_power_kw": 100.0,
            "connector_type": "GB/T",
        },
        {
            "make": "Evolute",
            "model": "i-Joy",
            "battery_capacity_kwh": 53.0,
            "max_ac_power_kw": 7.0,
            "max_dc_power_kw": 45.0,
            "connector_type": "CCS2",
        },
    ]


def _filter_model_fields(model_cls: Any, data: Dict[str, Any]) -> Dict[str, Any]:
    """Фильтрует словарь данных, оставляя только реальные колонки таблицы SQLAlchemy."""
    if not hasattr(model_cls, "__table__"):
        return data
    valid_cols = set(model_cls.__table__.columns.keys())
    return {k: v for k, v in data.items() if k in valid_cols}


async def seed_users(session) -> None:
    """Создает базового администратора и тестового пользователя."""
    logger.info("Проверка и сидирование пользователей...")
    user_cols = set(User.__table__.columns.keys())

# Автоматически определяем допустимые строковые значения для ролей из ENUM базы
    admin_role_val = "admin"
    client_role_val = "client"

    if UserRole is not None:
        # Если есть класс UserRole, берем реальные значения из него
        admin_role_val = getattr(UserRole, "ADMIN", "admin")
        client_role_val = getattr(UserRole, "CLIENT", getattr(UserRole, "USER", getattr(UserRole, "DRIVER", "client")))
    elif hasattr(User, "__table__") and "role" in User.__table__.columns:
        # Либо считываем список разрешенных ENUM прямо из описания таблицы SQLAlchemy
        enums = getattr(User.__table__.columns["role"].type, "enums", [])
        if enums:
            admin_role_val = next((e for e in enums if "admin" in e.lower()), enums[0])
            client_role_val = next((e for e in enums if "admin" not in e.lower()), enums[-1])

    users_to_seed = [
        {
            "email": "admin@example.com",
            "raw_password": "adminpassword123",
            "name": "Администратор",
            "phone": "+79991112233",
            "is_admin": True,
            "role": UserRole.admin,
        },
        {
            "email": "user@example.com",
            "raw_password": "userpassword123",
            "name": "Вячеслав",
            "phone": "+79998887766",
            "is_admin": False,
            "role": UserRole.driver,
        },
    ]

    for udata in users_to_seed:
        result = await session.execute(select(User).where(User.email == udata["email"]))
        existing_user = result.scalars().first()

        if not existing_user:
            create_payload = {
                "id": str(uuid.uuid4()),
                "email": udata["email"],
                "role": udata["role"],
            }

            # Пароль (в вашей модели поле называется password_hash)
            hashed_pwd = get_password_hash(udata["raw_password"])
            if "password_hash" in user_cols:
                create_payload["password_hash"] = hashed_pwd
            elif "hashed_password" in user_cols:
                create_payload["hashed_password"] = hashed_pwd

            # ФИО (в вашей модели поле называется full_name)
            if "full_name" in user_cols:
                create_payload["full_name"] = udata["name"]
            elif "name" in user_cols:
                create_payload["name"] = udata["name"]

            # Телефон
            if "phone" in user_cols:
                create_payload["phone"] = udata["phone"]

            # Активность
            if "is_active" in user_cols:
                create_payload["is_active"] = True

            session.add(User(**create_payload))
            logger.info(f"Добавлен пользователь: {udata['email']}")
        else:
            logger.info(f"Пользователь {udata['email']} уже существует.")

    await session.commit()


def _resolve_enum_value(model_cls: Any, col_name: str, preferred: str, enum_cls: Any = None) -> Any:
    """Определяет валидное значение ENUM из метаданных таблицы базы данных."""
    if hasattr(model_cls, "__table__") and col_name in model_cls.__table__.columns:
        col_type = model_cls.__table__.columns[col_name].type
        enums = getattr(col_type, "enums", None)
        if enums:
            pref = preferred.lower().replace("/", "_").replace("-", "_")
            for e in enums:
                val = str(e).lower().replace("/", "_").replace("-", "_")
                if pref in val or val in pref:
                    return e
            return enums[0]

    if enum_cls is not None:
        for attr in (preferred, preferred.lower(), preferred.upper()):
            if hasattr(enum_cls, attr):
                return getattr(enum_cls, attr)
    return preferred


async def seed_stations(session) -> None:
    """Создает тестовый пул зарядных станций для карты и зарядных сессий."""
    if Station is None:
        logger.info("Модель Station не найдена, пропускаем шаг.")
        return

    logger.info("Проверка и сидирование зарядных станций...")

    # Автоматическое определение валидных значений ENUM из базы
    conn_gbt = _resolve_enum_value(Station, "connector_type", "gbt_dc", ConnectorType)
    conn_ccs = _resolve_enum_value(Station, "connector_type", "ccs2", ConnectorType)
    conn_type2 = _resolve_enum_value(Station, "connector_type", "type2", ConnectorType)

    status_available = _resolve_enum_value(Station, "status", "available", StationStatus)
    status_busy = _resolve_enum_value(Station, "status", "busy", StationStatus)

    stations_data = [
        {
            "id": str(uuid.uuid4()),
            "public_id": "ST-001",
            "name": "Pear Energy — Иннопарк Сколково",
            "latitude": 55.6985,
            "longitude": 37.3594,
            "max_power_kw": 120.0,
            "connector_type": conn_gbt,
            "status": status_available,
            "tariff_per_kwh": 18.50,
            "is_active": True,
        },
        {
            "id": str(uuid.uuid4()),
            "public_id": "ST-002",
            "name": "Pear Energy — ТЦ Авиапарк",
            "latitude": 55.7905,
            "longitude": 37.5312,
            "max_power_kw": 150.0,
            "connector_type": conn_ccs,
            "status": status_available,
            "tariff_per_kwh": 19.00,
            "is_active": True,
        },
        {
            "id": str(uuid.uuid4()),
            "public_id": "ST-003",
            "name": "Pear Energy — Сити Пресня",
            "latitude": 55.7500,
            "longitude": 37.5370,
            "max_power_kw": 180.0,
            "connector_type": conn_gbt,
            "status": status_busy,
            "tariff_per_kwh": 21.00,
            "is_active": True,
        },
        {
            "id": str(uuid.uuid4()),
            "public_id": "ST-004",
            "name": "Pear Energy — Динамо Hub",
            "latitude": 55.7915,
            "longitude": 37.5590,
            "max_power_kw": 60.0,
            "connector_type": conn_type2,
            "status": status_available,
            "tariff_per_kwh": 17.50,
            "is_active": True,
        },
    ]

    for s_info in stations_data:
        pub_id = s_info["public_id"]
        s_name = s_info["name"]

        # Проверяем наличие станции до вставки
        query = select(Station)
        if hasattr(Station, "public_id"):
            query = query.where(Station.public_id == pub_id)
        else:
            query = query.where(Station.name == s_name)

        result = await session.execute(query)
        existing_station = result.scalars().first()

        if not existing_station:
            filtered = _filter_model_fields(Station, s_info)
            # Принудительно передаем UUID id
            filtered["id"] = s_info["id"]

            station_obj = Station(**filtered)
            station_obj.id = s_info["id"]
            session.add(station_obj)
            await session.commit()
            logger.info(f"Добавлена станция: {s_name}")
        else:
            logger.info(f"Станция {s_name} уже существует.")

async def seed_car_catalog(session) -> None:
    """Заполняет таблицу каталога электромобилей car_catalog."""
    if CarCatalog is None:
        logger.info("Модель CarCatalog не обнаружена, пропускаем каталог авто.")
        return

    logger.info("Проверка и сидирование каталога автомобилей...")
    added_count = 0

    for car in CARS_CATALOG:
        filtered = _filter_model_fields(CarCatalog, car)
        query = select(CarCatalog).where(
            CarCatalog.make == car["make"], CarCatalog.model == car["model"]
        )
        result = await session.execute(query)
        existing = result.scalars().first()

        if not existing:
            session.add(CarCatalog(**filtered))
            added_count += 1

    await session.commit()
    logger.info(f"Сидирование каталога авто завершено. Добавлено новых моделей: {added_count}")


async def seed() -> None:
    """Точка входа запуска процедур сидирования."""
    logger.info("=== Запуск скрипта начального наполнения БД ===")
    async with async_session_maker() as session:
        try:
            await seed_users(session)
            await seed_stations(session)
            await seed_car_catalog(session)
            logger.info("=== Все процедуры сидирования успешно выполнены ===")
        except Exception as exc:
            await session.rollback()
            logger.exception(f"Критическая ошибка при сидировании: {exc}")
            raise exc


if __name__ == "__main__":
    asyncio.run(seed())