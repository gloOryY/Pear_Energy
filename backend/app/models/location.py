from sqlalchemy import JSON, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Location(Base, TimestampMixin):
    __tablename__ = "locations"

    id: Mapped[str] = mapped_column(primary_key=True)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    address: Mapped[str] = mapped_column(Text)
    latitude: Mapped[float] = mapped_column(Numeric(9, 6))
    longitude: Mapped[float] = mapped_column(Numeric(9, 6))
    city: Mapped[str] = mapped_column(String(128), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    amenities: Mapped[list] = mapped_column(JSON, default=list)  # ["wc","cafe","wifi","hotel","parking"]
    schedule: Mapped[dict] = mapped_column(JSON, default=dict)   # {"always_open": true} | {"mon":[["08:00","22:00"]],...}
    venue_types: Mapped[list] = mapped_column(JSON, default=list)  # ["hotel","motel","cafe","parking","highway"]
    photo_urls: Mapped[list] = mapped_column(JSON, default=list)
    owner_share_percent: Mapped[float] = mapped_column(default=90.0)  # доля владельца локации, остальное — платформа

    stations = relationship("Station", back_populates="location", lazy="selectin")
