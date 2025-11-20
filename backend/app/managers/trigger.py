from typing import Optional, Union

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger


class EmitterTrigger:
    @staticmethod
    def normalize_time(time_str: str) -> int:
        try:
            return int(time_str)
        except ValueError:
            return 0

    @classmethod
    def create_trigger(cls,
                       seconds: str = "*",
                       minutes: str = "*",
                       hours: str = "*",
                       days: str = "*",
                       weeks: str = "*",
                       month: str = "*",
                       day_of_week: str = "*",
                       year: str = "*",
                       start_date: Optional[str] = None,
                       end_date: Optional[str] = None,
                       timezone: Optional[str] = None,
                       jitter: Optional[int] = None
                       ) -> Union[IntervalTrigger, CronTrigger]:
        """
        Фабрика триггера, которая возвращает либо IntervalTrigger, либо CronTrigger в зависимости от заданных полей.

        :param seconds: Интервал в секундах (для IntervalTrigger).
        :param minutes: Интервал в минутах (для IntervalTrigger).
        :param hours: Интервал в часах (для IntervalTrigger).
        :param days: Интервал в днях или день месяца (для обоих триггеров).
        :param weeks: Интервал в неделях (для IntervalTrigger).
        :param month: Месяц (для CronTrigger).
        :param day_of_week: День недели (для CronTrigger).
        :param year: Год (для CronTrigger).
        :param start_date: Дата начала (для обоих триггеров).
        :param end_date: Дата окончания (для обоих триггеров).
        :param timezone: Временная зона (для обоих триггеров).
        :param jitter: Случайное смещение в секундах (для обоих триггеров).
        :return: IntervalTrigger или CronTrigger.
        """
        if any(cls.normalize_time(param) != 0 for param in [seconds, minutes, hours, days, weeks]):
            return IntervalTrigger(
                seconds=cls.normalize_time(seconds),
                minutes=cls.normalize_time(minutes),
                hours=cls.normalize_time(hours),
                days=cls.normalize_time(days),
                weeks=cls.normalize_time(weeks),
                start_date=start_date,
                end_date=end_date,
                timezone=timezone,
                jitter=jitter
            )
        else:
            return CronTrigger(
                second=seconds,
                minute=minutes,
                hour=hours,
                day=days,
                month=month,
                year=year,
                day_of_week=day_of_week,
                start_date=start_date,
                end_date=end_date,
                timezone=timezone,
                jitter=jitter
            )
