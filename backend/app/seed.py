import asyncio
from sqlalchemy import select
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import Location, Review, Station, StationPhoto, User, Vehicle
from app.models.enums import ConnectorType, ModerationStatus, StationStatus, UserRole
from app.utils.ids import uid

PHOTO = "https://picsum.photos/seed/{seed}/800/500"

LOCATIONS = [
    {"name": "Кофемания", "city": "Москва", "address": "ул. Тверская, 9", "lat": 55.7297, "lon": 37.6035, "amenities": ["wc", "cafe", "wifi", "parking"], "venues": ["cafe", "parking"]},
    {"name": "Парковка", "city": "Москва", "address": "Кутузовский пр., 5", "lat": 55.8890, "lon": 37.4370, "amenities": ["wc", "cafe", "wifi", "parking"], "venues": ["parking"]},
    {"name": "Отель", "city": "Санкт-Петербург", "address": "Невский пр., 39", "lat": 59.9330, "lon": 30.3150, "amenities": ["wc", "wifi", "hotel", "parking"], "venues": ["hotel", "parking"]},
    {"name": "Кафе", "city": "Казань", "address": "ул. Баумана, 141", "lat": 55.7680, "lon": 49.2040, "amenities": ["wc", "cafe", "wifi", "parking"], "venues": ["cafe", "parking"]},
    {"name": "Паркинг", "city": "Нижний Новгород", "address": "Большая Покровская, 4", "lat": 56.3300, "lon": 44.0090, "amenities": ["wc", "cafe", "wifi", "parking"], "venues": ["cafe", "parking"]},
    {"name": "Отель", "city": "Сочи", "address": "Курортный пр., 4", "lat": 43.5810, "lon": 39.7180, "amenities": ["wc", "wifi", "hotel", "cafe", "parking"], "venues": ["hotel", "parking"]},
    {"name": "М4-98", "city": "Владимир", "address": "М4, 98-й км", "lat": 54.8340, "lon": 38.2930, "amenities": ["wc", "cafe", "wifi", "parking"], "venues": ["highway", "motel", "parking"]},
    {"name": "М4-220", "city": "Воронеж", "address": "М4, 220-й км", "lat": 53.9500, "lon": 38.3200, "amenities": ["wc", "wifi", "motel", "parking"], "venues": ["highway", "motel", "parking"]},
]

STATIONS = [
    (0, "Станция 1", 22, 32, 18.0, True, StationStatus.available),
    (0, "Станция 2", 7.4, 32, 15.0, False, StationStatus.charging),
    (1, "Станция 3", 11, 16, 16.5, True, StationStatus.available),
    (2, "Станция 4", 3.7, 16, 14.0, True, StationStatus.available),
    (3, "Станция 5", 22, 32, 17.0, True, StationStatus.vehicle_connected),
    (4, "NN-1", 7.4, 32, 15.5, False, StationStatus.available),
    (5, "Станция 7", 11, 32, 19.0, True, StationStatus.available),
    (6, "М4-98-1", 22, 32, 20.0, True, StationStatus.available),
    (6, "М4-98-2", 7.4, 32, 16.0, False, StationStatus.offline),
    (7, "М4-220", 3.7, 16, 13.0, False, StationStatus.faulted),
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as db:
        if (await db.execute(select(User).limit(1))).scalar_one_or_none():
            print("Seed: данные уже есть, пропускаем")
            return
        users = {}
        for email, name, role in [
            ("driver@example.com", "", UserRole.driver),
            ("operator@example.com", "", UserRole.operator),
            ("admin@example.com", "", UserRole.admin),
        ]:
            u = User(
                id=uid(),
                phone=f"+7900{email[:5].replace('@', '').ljust(6, '0')}",
                email=email,
                full_name=name,
                role=role,
                password_hash=hash_password("Password123!"),
            )
            db.add(u)
            users[email] = u
            await db.flush()
        db.add(Vehicle(id=uid(), user_id=users["driver@example.com"].id, brand="Tesla", model="Model 3", plate_number="77777", connector_type=ConnectorType.type2))
        seq = 0
        stations = []
        for i, L in enumerate(LOCATIONS):
            loc = Location(
                id=uid(),
                owner_id=users["operator@example.com"].id,
                name=L["name"],
                address=L["address"],
                city=L["city"],
                latitude=L["lat"],
                longitude=L["lon"],
                description=f"{L['name']}, {L['city']}",
                amenities=L["amenities"],
                schedule={"always_open": True},
                venue_types=L["venues"],
                photo_urls=[PHOTO.format(seed=i)],
            )
            db.add(loc)
            await db.flush()
            for li, name, kw, amp, tariff, bookable, status in [(s[0], s[1], s[2], s[3], s[4], s[5], s[6]) for s in STATIONS if s[0] == i]:
                prefix = {"Москва": "MSK", "Санкт-Петербург": "SPB", "Казань": "KZN", "Нижний Новгород": "NN", "Сочи": "SOCHI"}.get(L["city"], "M4" if "-4" in L["address"] else "MO")
                seq += 1
                st = Station(
                    id=uid(),
                    location_id=loc.id,
                    public_id=f"CP-{prefix}-{seq:03d}",
                    name=name,
                    serial_number=f"SN{seq:08d}",
                    device_token=f"devtok{uid()[:24]}",
                    connector_type=ConnectorType.type2,
                    max_power_kw=kw,
                    max_current_a=amp,
                    status=status,
                    tariff_per_kwh=tariff,
                    tariff_per_minute_idle=2,
                    min_launch_amount=100,
                    booking_amount=100 if bookable else 0,
                    supports_booking=bookable,
                    parking_info="",
                    latitude=L["lat"] + 0.0004 * seq,
                    longitude=L["lon"] - 0.0003 * seq,
                )
                db.add(st)
                stations.append(st)
                await db.flush()
        db.add(StationPhoto(id=uid(), station_id=stations[0].id, url=PHOTO.format(seed=stations[0].id), status=ModerationStatus.approved.value))
        db.add(Review(id=uid(), user_id=users["driver@example.com"].id, station_id=stations[0].id, rating=5, text="Отличная станция, быстрая зарядка!", status=ModerationStatus.approved.value))
        await db.commit()
        print(f"Seed: {len(users)} пользователей, {len(stations)} станций")


if __name__ == "__main__":
    asyncio.run(seed())
