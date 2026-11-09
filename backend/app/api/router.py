from fastapi import APIRouter

from app.api.v1 import admin, auth, bookings, cars, charging, operator, payments, stations, support, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(cars.router)
api_router.include_router(stations.router)
api_router.include_router(bookings.router)
api_router.include_router(charging.router)
api_router.include_router(payments.router)
api_router.include_router(support.router)
api_router.include_router(operator.router)
api_router.include_router(admin.router)
