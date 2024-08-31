from datetime import datetime
from hashlib import sha256
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, Security, Query
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from metealologia_backend.config import Station, api_key_hashes, stations_schema, settings
from metealologia_backend.database.models import ReportData, ReportUpload
from metealologia_backend.database.session import database

station_key_header = APIKeyHeader(name="Authorization", auto_error=False)

def validate_sensor(station_id: str, sensor_id: str) -> Station | None:
    for station in stations_schema:
        if station.id == station_id:
            for sensor in station.sensors:
                if sensor.id == sensor_id:
                    return
            raise HTTPException(404, detail="Sensor with id={} doesn't exist on station id={}".format(sensor_id, station_id))
    raise HTTPException(404, detail="Station with id={} doesn't exist".format(station_id))


def check_authorization(station_id: str, station_key: Annotated[str | None, Security(station_key_header)]):
    if station_key is None:
        raise HTTPException(401, detail="Missing 'Authorization' header")
    if sha256(station_key.encode()).hexdigest() != api_key_hashes[station_id]:
        raise HTTPException(401, detail="Invalid station key")


report_router = APIRouter(prefix="/{station_id}/sensors/{sensor_id}", dependencies=[Depends(validate_sensor)])


class ReportBody(BaseModel):
    timestamp: datetime
    data: dict


@report_router.post("/reports", status_code=201, response_class=Response, responses={401: {"description": "Invalid API key"}}, dependencies=[Depends(check_authorization)])
async def upload_report(station_id: str, sensor_id: str, body: ReportBody):
    """Uploads a new report"""
    await database.upload_report(
        ReportUpload(station_id=station_id, sensor_id=sensor_id, timestamp=body.timestamp, data=body.data)
    )


@report_router.get("/reports", response_model=list[ReportData], responses={404: {"description": "Station not found"}})
async def get_reports(station_id: str, sensor_id: str, before: Annotated[datetime, Query(default_factory=datetime.now)], limit: Annotated[int, Query(le=settings.report_limit)] = settings.report_limit, after: datetime = 0):
    """Fetches reports created between 'after' and 'before' timestamps"""
    return await database.get_reports(station_id, sensor_id, after, before, limit)
