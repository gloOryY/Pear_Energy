import asyncio
from decimal import Decimal
from datetime import datetime, timezone
import uuid

from sqlalchemy import select
from app.db.session import async_session_maker
from app.models.enums import ConnectorType, StationStatus
from app.models.station import Station
from app.models.hardware import Connector


SEED_STATIONS = [
    {
        "id": "st_schuko_01",
        "name": "ЭЗС Двор на Соборной (Розетка Schuko 220V)",
        "address": "г. Рязань, ул. Соборная, 14",
        "city": "Рязань",
        "latitude": Decimal("54.634100"),
        "longitude": Decimal("39.748200"),
        "max_power_kw": Decimal("3.5"),
        "connector_type": ConnectorType.schuko,
        "image_url": "https://images.unsplash.com/photo-1593941707882-a5bba14938c7?w=800&auto=format&fit=crop&q=80",
        "tariff_start": Decimal("0.00"),
        "tariff_per_minute": Decimal("2.50"),
        "connectors": [
            {"connector_number": 1, "type": ConnectorType.schuko, "max_power_kw": Decimal("3.5")},
        ],
    },
    {
        "id": "st_combo_02",
        "name": "ЭЗС ТРЦ Премьер (Type 2 & Schuko)",
        "address": "г. Рязань, Московское шоссе, 21",
        "city": "Рязань",
        "latitude": Decimal("54.638500"),
        "longitude": Decimal("39.698700"),
        "max_power_kw": Decimal("22.0"),
        "connector_type": ConnectorType.type2,
        "image_url": "https://images.unsplash.com/photo-1647891941746-fe1d53ddc7a6?w=800&auto=format&fit=crop&q=80",
        "tariff_start": Decimal("50.00"),
        "tariff_per_minute": Decimal("4.00"),
        "connectors": [
            {"connector_number": 1, "type": ConnectorType.type2, "max_power_kw": Decimal("22.0")},
            {"connector_number": 2, "type": ConnectorType.schuko, "max_power_kw": Decimal("3.5")},
        ],
    },
    {
        "id": "st_fast_03",
        "name": "ЭЗС Скоростной Хаб М5 (CCS 2 / CHAdeMO / GB/T)",
        "address": "г. Рязань, Первомайский проспект, 56",
        "city": "Рязань",
        "latitude": Decimal("54.628800"),
        "longitude": Decimal("39.715400"),
        "max_power_kw": Decimal("120.0"),
        "connector_type": ConnectorType.ccs2,
        "image_url": "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=800&auto=format&fit=crop&q=80",
        "tariff_start": Decimal("100.00"),
        "tariff_per_minute": Decimal("16.00"),
        "connectors": [
            {"connector_number": 1, "type": ConnectorType.ccs2, "max_power_kw": Decimal("120.0")},
            {"connector_number": 2, "type": ConnectorType.gbt_dc, "max_power_kw": Decimal("120.0")},
            {"connector_number": 3, "type": ConnectorType.chademo, "max_power_kw": Decimal("50.0")},
        ],
    },
    {
        "id": "st_park_04",
        "name": "ЭЗС Парк ЦПКиО (GB/T AC & Type 2)",
        "address": "г. Рязань, ул. Радищева, 28",
        "city": "Рязань",
        "latitude": Decimal("54.620500"),
        "longitude": Decimal("39.732100"),
        "max_power_kw": Decimal("22.0"),
        "connector_type": ConnectorType.type2,
        "image_url": "https://images.unsplash.com/photo-1558441719-aa34ab5fa3c3?w=800&auto=format&fit=crop&q=80",
        "tariff_start": Decimal("30.00"),
        "tariff_per_minute": Decimal("3.50"),
        "connectors": [
            {"connector_number": 1, "type": ConnectorType.type2, "max_power_kw": Decimal("22.0")},
            {"connector_number": 2, "type": ConnectorType.gbt_ac, "max_power_kw": Decimal("7.0")},
        ],
    },
]


async def seed() -> None:
    now = datetime.now(timezone.utc)
    async with async_session_maker() as session:
        result = await session.execute(select(Station).limit(1))
        if result.scalar_one_or_none():
            print("Seed: данные уже есть, пропускаем")
            return

        for data in SEED_STATIONS:
            conns_data = data.pop("connectors")
            station = Station(
                **data,
                status=StationStatus.available,
                max_current_a=Decimal("32.0"),
                tariff_per_kwh=Decimal("0.00"),
                tariff_per_minute_idle=Decimal("0.00"),
                min_launch_amount=Decimal("100.00"),
                booking_amount=Decimal("0.00"),
                supports_booking=True,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            session.add(station)
            await session.flush()

            for c in conns_data:
                conn = Connector(
                    id=str(uuid.uuid4()),
                    station_id=station.id,
                    connector_number=c["connector_number"],
                    type=c["type"],
                    max_power_kw=c["max_power_kw"],
                    status="available",
                    created_at=now,
                    updated_at=now,
                )
                session.add(conn)

        await session.commit()
        print("Seed: станции успешно добавлены!")


if __name__ == "__main__":
    asyncio.run(seed())