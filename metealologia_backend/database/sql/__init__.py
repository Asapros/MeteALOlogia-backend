from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from metealologia_backend.database.sql.schema import metadata, reports
from metealologia_backend.database import Database, ReportUpload
from metealologia_backend.database.models import ReportData


class SQLDatabase(Database):
    connection: AsyncConnection | None = None

    async def connect(self, database_url: str):
        engine = create_async_engine(database_url)
        self.connection = await engine.connect()
        await self.connection.run_sync(metadata.create_all)
        await self.connection.commit()

    async def disconnect(self):
        await self.connection.close()

    async def upload_report(self, report: ReportUpload):
        await self.connection.execute(reports.insert(), report.model_dump())
        await self.connection.commit()

    async def get_reports(self, station_id: str, sensor_id: str, after: datetime, before: datetime, limit: int) -> list[ReportData]:
        result = await self.connection.execute(select(reports.columns.timestamp, reports.columns.data)
                                               .where(reports.columns.station_id == station_id)
                                               .where(reports.columns.sensor_id == sensor_id)
                                               .where(reports.columns.timestamp > after)
                                               .where(reports.columns.timestamp < before)
                                               .order_by(desc(reports.columns.timestamp))
                                               .limit(limit)
                                               )
        return [
            ReportData(timestamp=row.timestamp, data=row.data)
            for row in result.fetchall()
        ]


def instantiate() -> Database:
    return SQLDatabase()