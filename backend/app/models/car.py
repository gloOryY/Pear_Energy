from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base


class CarCatalog(Base):
    __tablename__ = "car_catalog"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    make = Column(String(64), nullable=False, index=True)       # Марка (напр., Zeekr, Geely, Tesla)
    model = Column(String(64), nullable=False, index=True)      # Модель (напр., 001, EX5, Model Y)
    battery_capacity_kwh = Column(Float, nullable=False)        # Полезная емкость батареи (кВт·ч)
    max_ac_power_kw = Column(Float, default=11.0)               # Макс. мощность AC (медленная зарядка, Type 2/GB/T AC)
    max_dc_power_kw = Column(Float, default=120.0)              # Макс. мощность DC (быстрая зарядка, CCS2/GB/T DC)
    connector_type = Column(String(32), default="GB/T")         # Основной порт (GB/T, CCS 2, Type 2)


class UserCar(Base):
    __tablename__ = "user_cars"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    catalog_car_id = Column(Integer, ForeignKey("car_catalog.id", ondelete="SET NULL"), nullable=True)

    # Пользовательские характеристики (копируются из каталога или вводятся вручную)
    make = Column(String(64), nullable=False)
    model = Column(String(64), nullable=False)
    battery_capacity_kwh = Column(Float, nullable=False)
    max_ac_power_kw = Column(Float, default=11.0)
    max_dc_power_kw = Column(Float, default=120.0)
    connector_type = Column(String(32), default="GB/T")

    is_active = Column(Boolean, default=True)                   # Текущее выбранное авто для зарядки
    is_custom = Column(Boolean, default=False)                  # Флаг кастомного авто
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    catalog_car = relationship("CarCatalog")
    user = relationship("User", back_populates="cars")