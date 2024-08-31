from fastapi import APIRouter

from metealologia_backend.stations.reports import report_router
from metealologia_backend.config import Station, stations_schema

stations_router = APIRouter(prefix="/stations", tags=["sensors"])
stations_router.include_router(report_router)


@stations_router.get("", response_model=list[Station])
async def get_all_stations():
    """Returns metadata of the all stations"""
    return stations_schema
