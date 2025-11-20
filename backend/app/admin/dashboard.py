import datetime
from fastadmin import DashboardWidgetAdmin, DashboardWidgetType, WidgetType, register_widget
from sqlalchemy import select, func, text
from app.database import sessionmanager
from app.models import (
    BotModel, UserModel, MessageModel, SessionModel, 
    StepModel, WidgetModel, ChannelModel, EmitterModel
)


@register_widget
class BotsDashboardWidgetAdmin(DashboardWidgetAdmin):
    title = "Боты"
    dashboard_widget_type = DashboardWidgetType.ChartLine

    x_field = "date"
    x_field_filter_widget_type = WidgetType.DatePicker
    x_field_filter_widget_props = {"picker": "month"}
    x_field_periods = ["day", "week", "month", "year"]
    y_field = "count"

    async def get_data(
        self,
        min_x_field: str | None = None,
        max_x_field: str | None = None,
        period_x_field: str | None = None,
    ) -> dict:
        async with sessionmanager.session() as session:
            # Обработка параметров фильтрации
            if not min_x_field:
                min_x_field_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
            else:
                min_x_field_date = datetime.datetime.fromisoformat(min_x_field)

            if not max_x_field:
                max_x_field_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
            else:
                max_x_field_date = datetime.datetime.fromisoformat(max_x_field)

            if not period_x_field or period_x_field not in (self.x_field_periods or []):
                period_x_field = "day"

            # Определяем date_trunc в зависимости от периода
            date_trunc_map = {
                "day": "day",
                "week": "week", 
                "month": "month",
                "year": "year",
            }
            date_trunc = date_trunc_map.get(period_x_field, "day")

            # SQL запрос с фильтрацией и группировкой
            result = await session.execute(
                text(f"""
                    SELECT
                        to_char(date_trunc('{date_trunc}', subscriber.created_at)::date, 'YYYY-MM-DD') as date,
                        COUNT(subscriber.id) as count
                    FROM subscriber
                    JOIN bot ON subscriber.id = bot.id
                    WHERE subscriber.created_at >= :min_date AND subscriber.created_at <= :max_date
                    GROUP BY date_trunc('{date_trunc}', subscriber.created_at)::date
                    ORDER BY date_trunc('{date_trunc}', subscriber.created_at)::date
                """),
                {
                    "min_date": min_x_field_date.replace(tzinfo=None),
                    "max_date": max_x_field_date.replace(tzinfo=None)
                }
            )
            
            results = [{"date": row[0], "count": int(row[1])} for row in result.fetchall()]
            
            return {
                "results": results,
                "min_x_field": min_x_field_date.strftime('%Y-%m-%d'),
                "max_x_field": max_x_field_date.strftime('%Y-%m-%d'),
                "period_x_field": period_x_field,
            }


@register_widget
class MessagesDashboardWidgetAdmin(DashboardWidgetAdmin):
    title = "Сообщения"
    dashboard_widget_type = DashboardWidgetType.ChartColumn

    x_field = "date"
    x_field_filter_widget_type = WidgetType.DatePicker
    x_field_filter_widget_props = {"picker": "month"}
    x_field_periods = ["day", "week", "month", "year"]
    y_field = "count"

    async def get_data(
        self,
        min_x_field: str | None = None,
        max_x_field: str | None = None,
        period_x_field: str | None = None,
    ) -> dict:
        async with sessionmanager.session() as session:
            if not min_x_field:
                min_x_field_date = datetime.datetime.now() - datetime.timedelta(days=30)
            else:
                min_x_field_date = datetime.datetime.fromisoformat(min_x_field.replace('Z', '+00:00')).replace(tzinfo=None)

            if not max_x_field:
                max_x_field_date = datetime.datetime.now() + datetime.timedelta(days=1)
            else:
                max_x_field_date = datetime.datetime.fromisoformat(max_x_field.replace('Z', '+00:00')).replace(tzinfo=None)

            if not period_x_field or period_x_field not in (self.x_field_periods or []):
                period_x_field = "day"

            # SQL запрос для получения данных по сообщениям
            if period_x_field == "day":
                date_trunc = "day"
            elif period_x_field == "week":
                date_trunc = "week"
            elif period_x_field == "month":
                date_trunc = "month"
            else:  # year
                date_trunc = "year"

            result = await session.execute(
                text(f"""
                    SELECT
                        to_char(date_trunc('{date_trunc}', message.created_at)::date, 'YYYY-MM-DD') as date,
                        COUNT(message.id) as count
                    FROM message
                    WHERE message.created_at >= :min_date AND message.created_at <= :max_date
                    GROUP BY date_trunc('{date_trunc}', message.created_at)::date
                    ORDER BY date_trunc('{date_trunc}', message.created_at)::date
                """),
                {
                    "min_date": min_x_field_date.replace(tzinfo=None),
                    "max_date": max_x_field_date.replace(tzinfo=None)
                }
            )
            
            results = [{"date": row[0], "count": int(row[1])} for row in result.fetchall()]
            
            return {
                "results": results,
                "min_x_field": min_x_field_date.strftime('%Y-%m-%d'),
                "max_x_field": max_x_field_date.strftime('%Y-%m-%d'),
                "period_x_field": period_x_field,
            }


@register_widget
class UsersDashboardWidgetAdmin(DashboardWidgetAdmin):
    title = "Пользователи"
    dashboard_widget_type = DashboardWidgetType.ChartLine

    x_field = "date"
    x_field_filter_widget_type = WidgetType.DatePicker
    x_field_filter_widget_props = {"picker": "month"}
    x_field_periods = ["day", "week", "month", "year"]
    y_field = "count"

    async def get_data(
        self,
        min_x_field: str | None = None,
        max_x_field: str | None = None,
        period_x_field: str | None = None,
    ) -> dict:
        async with sessionmanager.session() as session:
            # Обработка параметров фильтрации
            if not min_x_field:
                min_x_field_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
            else:
                min_x_field_date = datetime.datetime.fromisoformat(min_x_field)

            if not max_x_field:
                max_x_field_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
            else:
                max_x_field_date = datetime.datetime.fromisoformat(max_x_field)

            if not period_x_field or period_x_field not in (self.x_field_periods or []):
                period_x_field = "day"

            # Определяем date_trunc в зависимости от периода
            date_trunc_map = {
                "day": "day",
                "week": "week", 
                "month": "month",
                "year": "year",
            }
            date_trunc = date_trunc_map.get(period_x_field, "day")

            # SQL запрос с фильтрацией и группировкой
            result = await session.execute(
                text(f"""
                    SELECT
                        to_char(date_trunc('{date_trunc}', subscriber.created_at)::date, 'YYYY-MM-DD') as date,
                        COUNT(subscriber.id) as count
                    FROM subscriber
                    WHERE subscriber.type = 'user' 
                    AND subscriber.created_at >= :min_date AND subscriber.created_at <= :max_date
                    GROUP BY date_trunc('{date_trunc}', subscriber.created_at)::date
                    ORDER BY date_trunc('{date_trunc}', subscriber.created_at)::date
                """),
                {
                    "min_date": min_x_field_date.replace(tzinfo=None),
                    "max_date": max_x_field_date.replace(tzinfo=None)
                }
            )
            
            results = [{"date": row[0], "count": int(row[1])} for row in result.fetchall()]
            
            return {
                "results": results,
                "min_x_field": min_x_field_date.strftime('%Y-%m-%d'),
                "max_x_field": max_x_field_date.strftime('%Y-%m-%d'),
                "period_x_field": period_x_field,
            }


@register_widget
class SessionsDashboardWidgetAdmin(DashboardWidgetAdmin):
    title = "Активные сессии"
    dashboard_widget_type = DashboardWidgetType.ChartArea

    x_field = "date"
    x_field_filter_widget_type = WidgetType.DatePicker
    x_field_filter_widget_props = {"picker": "month"}
    x_field_periods = ["day", "week", "month", "year"]
    y_field = "count"

    async def get_data(
        self,
        min_x_field: str | None = None,
        max_x_field: str | None = None,
        period_x_field: str | None = None,
    ) -> dict:
        async with sessionmanager.session() as session:
            # Обработка параметров фильтрации
            if not min_x_field:
                min_x_field_date = datetime.datetime.now() - datetime.timedelta(days=7)
            else:
                min_x_field_date = datetime.datetime.fromisoformat(min_x_field.replace('Z', '+00:00')).replace(tzinfo=None)

            if not max_x_field:
                max_x_field_date = datetime.datetime.now() + datetime.timedelta(days=1)
            else:
                max_x_field_date = datetime.datetime.fromisoformat(max_x_field.replace('Z', '+00:00')).replace(tzinfo=None)

            if not period_x_field or period_x_field not in (self.x_field_periods or []):
                period_x_field = "day"

            # Определяем date_trunc в зависимости от периода
            date_trunc_map = {
                "day": "day",
                "week": "week", 
                "month": "month",
                "year": "year",
            }
            date_trunc = date_trunc_map.get(period_x_field, "day")

            # SQL запрос для активных сессий с фильтрацией
            result = await session.execute(
                text(f"""
                    SELECT
                        to_char(date_trunc('{date_trunc}', session.updated_at)::date, 'YYYY-MM-DD') as date,
                        COUNT(session.id) as count
                    FROM session
                    WHERE session.updated_at >= :min_date AND session.updated_at <= :max_date
                    GROUP BY date_trunc('{date_trunc}', session.updated_at)::date
                    ORDER BY date_trunc('{date_trunc}', session.updated_at)::date
                """),
                {
                    "min_date": min_x_field_date.replace(tzinfo=None),
                    "max_date": max_x_field_date.replace(tzinfo=None)
                }
            )
            
            results = [{"date": row[0], "count": int(row[1])} for row in result.fetchall()]
            
            return {
                "results": results,
                "min_x_field": min_x_field_date.strftime('%Y-%m-%d'),
                "max_x_field": max_x_field_date.strftime('%Y-%m-%d'),
                "period_x_field": period_x_field,
            }