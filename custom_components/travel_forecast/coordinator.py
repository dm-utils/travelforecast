"""DataUpdateCoordinator that builds the hourly travel-time forecast."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import RoutePrediction, TomTomApiError, async_predict_travel_time
from .const import (
    CONF_DESTINATION_LAT,
    CONF_DESTINATION_LON,
    CONF_ORIGIN_LAT,
    CONF_ORIGIN_LON,
    CONF_REFRESH_INTERVAL,
    DEFAULT_REFRESH_INTERVAL_HOURS,
    DOMAIN,
    HORIZON_HOURS,
    MAX_CONCURRENT_REQUESTS,
)
from homeassistant.const import CONF_API_KEY

_LOGGER = logging.getLogger(__name__)


@dataclass
class ForecastPoint:
    timestamp: datetime
    duration_min: float
    distance_km: float


class TravelForecastCoordinator(DataUpdateCoordinator[list[ForecastPoint]]):
    """Fetches a HORIZON_HOURS-long, hourly-stepped travel-time forecast."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.api_key: str = entry.data[CONF_API_KEY]
        self.origin = (entry.data[CONF_ORIGIN_LAT], entry.data[CONF_ORIGIN_LON])
        self.destination = (entry.data[CONF_DESTINATION_LAT], entry.data[CONF_DESTINATION_LON])
        self._session = async_get_clientsession(hass)
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

        refresh_hours = entry.options.get(CONF_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL_HOURS)
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=refresh_hours),
        )

    def _hourly_timestamps(self) -> list[datetime]:
        start = (datetime.now() + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        return [start + timedelta(hours=i) for i in range(HORIZON_HOURS)]

    async def _fetch_one(self, timestamp: datetime) -> ForecastPoint:
        async with self._semaphore:
            prediction: RoutePrediction = await async_predict_travel_time(
                self._session, self.origin, self.destination, timestamp, self.api_key
            )
        return ForecastPoint(
            timestamp=timestamp,
            duration_min=prediction.duration_min,
            distance_km=prediction.distance_km,
        )

    async def _async_update_data(self) -> list[ForecastPoint]:
        timestamps = self._hourly_timestamps()
        try:
            results = await asyncio.gather(*(self._fetch_one(ts) for ts in timestamps))
        except TomTomApiError as err:
            raise UpdateFailed(str(err)) from err
        return sorted(results, key=lambda point: point.timestamp)
