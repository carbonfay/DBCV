import uuid
from datetime import datetime
from typing import Optional, List, Union
from sqlalchemy import ForeignKey, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel, UUID
from app.config import settings
from app.managers import EmitterTrigger


class CronModel(BaseModel):
    __tablename__ = "cron"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4, type_=UUID)
    name: Mapped[str]
    year: Mapped[Optional[str]] = mapped_column(server_default="*")
    month: Mapped[Optional[str]] = mapped_column(server_default="*")
    day: Mapped[Optional[str]] = mapped_column(server_default="*")
    day_of_week: Mapped[Optional[str]] = mapped_column(server_default="*")
    hour: Mapped[Optional[str]] = mapped_column(server_default="*")
    minute: Mapped[Optional[str]] = mapped_column(server_default="*")
    second: Mapped[Optional[str]] = mapped_column(server_default="*")
    start_date: Mapped[datetime | None] = mapped_column(TIMESTAMP, default=None)
    end_date: Mapped[datetime | None] = mapped_column(TIMESTAMP, default=None)
    timezone: Mapped[str] = mapped_column(server_default=settings.TIME_ZONE)
    jitter: Mapped[int | None] = mapped_column(default=None)

    emitters: Mapped[List["EmitterModel"]] = relationship("EmitterModel", back_populates="cron", lazy="select",
                                                          load_on_pending=True, uselist=True)

    def get_cron_trigger(self):
        return EmitterTrigger.create_trigger(year=self.year,
                                             month=self.month,
                                             days=self.day,
                                             day_of_week=self.day_of_week,
                                             hours=self.hour,
                                             minutes=self.minute,
                                             seconds=self.second,
                                             start_date=self.start_date,
                                             end_date=self.end_date,
                                             timezone=self.timezone,
                                             jitter=self.jitter)

    def __str__(self):
        return f"{self.__tablename__.capitalize()}(id={self.id}, name={self.name!r})"

    def __repr__(self):
        return str(self)
