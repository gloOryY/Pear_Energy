from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.security import hash_password, verify_password
from app.db.session import get_db
from app.models import Favorite, Notification, User, Vehicle
from app.schemas.user import NotificationOut, PasswordChange, ProfileUpdate, UserOut, VehicleIn, VehicleOut
from app.utils.ids import uid

router = APIRouter(tags=["me"])


@router.patch("/me", response_model=UserOut)
async def update_profile(data: ProfileUpdate, user: User = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db)):
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.phone is not None:
        user.phone = data.phone
    if data.email is not None:
        user.email = data.email.lower()
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/me/password")
async def change_password(data: PasswordChange, user: User = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(400, "Старый пароль неверный")
    user.password_hash = hash_password(data.new_password)
    db.add(user)
    await db.commit()
    return {"ok": True}


@router.delete("/me")
async def delete_account(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user.is_active = False
    user.email = f"deleted-{user.id}@pear.local"
    user.phone = f"+70000000{user.id[:3]}"
    db.add(user)
    await db.execute(delete(Favorite).where(Favorite.user_id == user.id))
    await db.commit()
    return {"ok": True, "message": "аккаунт деактивирован"}


@router.get("/me/vehicles", response_model=list[VehicleOut])
async def list_vehicles(user: User = Depends(get_current_user)):
    return user.vehicles


@router.post("/me/vehicles", response_model=VehicleOut, status_code=201)
async def add_vehicle(data: VehicleIn, user: User = Depends(get_current_user),
                       db: AsyncSession = Depends(get_db)):
    v = Vehicle(id=uid(), user_id=user.id, **data.model_dump())
    db.add(v)
    await db.commit()
    await db.refresh(v)
    return v


@router.delete("/me/vehicles/{vid}")
async def remove_vehicle(vid: str, user: User = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db)):
    v = await db.get(Vehicle, vid)
    if not v or v.user_id != user.id:
        raise HTTPException(404, "Не найдено")
    await db.delete(v)
    await db.commit()
    return {"ok": True}


@router.get("/me/notifications", response_model=list[NotificationOut])
async def my_notifications(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return (await db.execute(select(Notification).where(Notification.user_id == user.id)
                              .order_by(Notification.created_at.desc()).limit(50))).scalars().all()


@router.post("/me/notifications/read-all")
async def read_all_notifications(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Notification).where(
        Notification.user_id == user.id, Notification.is_read == False))).scalars().all()  # noqa: E712
    for n in rows:
        n.is_read = True
    await db.commit()
    return {"ok": True, "updated": len(rows)}


@router.get("/me/favorites", response_model=list[str])
async def my_favorites(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Favorite.station_id).where(Favorite.user_id == user.id))).scalars().all()
    return list(rows)


@router.post("/me/favorites/{station_id}", status_code=201)
async def add_favorite(station_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    exists = (await db.execute(select(Favorite).where(
        Favorite.user_id == user.id, Favorite.station_id == station_id))).scalar_one_or_none()
    if not exists:
        db.add(Favorite(user_id=user.id, station_id=station_id))
        await db.commit()
    return {"ok": True}


@router.delete("/me/favorites/{station_id}")
async def remove_favorite(station_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(delete(Favorite).where(Favorite.user_id == user.id, Favorite.station_id == station_id))
    await db.commit()
    return {"ok": True}
