"""Thin async client for the TomTom Search (geocode) and Routing APIs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from aiohttp import ClientSession

from .const import TOMTOM_GEOCODE_URL, TOMTOM_ROUTE_URL


class TomTomApiError(Exception):
    """Raised when TomTom returns a non-2xx response."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"TomTom API error {status}: {message}")
        self.status = status


class TomTomAuthError(TomTomApiError):
    """Raised on 401/403 — bad key or a product not (yet) enabled on it."""


@dataclass
class GeoPoint:
    lat: float
    lon: float
    display_name: str


@dataclass
class RoutePrediction:
    duration_min: float
    distance_km: float


async def async_geocode(session: ClientSession, address: str, api_key: str) -> GeoPoint:
    """Resolve a free-text address to coordinates. Called once, at config time."""
    url = TOMTOM_GEOCODE_URL.format(query=address)
    async with session.get(url, params={"key": api_key, "limit": 1}) as resp:
        if resp.status in (401, 403):
            raise TomTomAuthError(resp.status, await resp.text())
        if resp.status != 200:
            raise TomTomApiError(resp.status, await resp.text())
        data = await resp.json()

    results = data.get("results") or []
    if not results:
        raise ValueError(f"No geocode result for address: {address}")

    pos = results[0]["position"]
    display_name = results[0].get("address", {}).get("freeformAddress", address)
    return GeoPoint(lat=pos["lat"], lon=pos["lon"], display_name=display_name)


async def async_predict_travel_time(
    session: ClientSession,
    origin: tuple[float, float],
    destination: tuple[float, float],
    depart_at: datetime,
    api_key: str,
) -> RoutePrediction:
    """Predict travel time for a future departure. Traffic-aware duration
    already reflects the time-of-day-adjusted historical traffic; TomTom's
    separate trafficDelayInSeconds field stays 0 for a future departAt and
    is not used here (confirmed via dev/test_tomtom_route.py)."""
    origin_str = f"{origin[0]},{origin[1]}"
    dest_str = f"{destination[0]},{destination[1]}"
    url = TOMTOM_ROUTE_URL.format(origin=origin_str, destination=dest_str)
    params = {
        "key": api_key,
        "traffic": "true",
        "departAt": depart_at.replace(microsecond=0).isoformat(),
    }
    async with session.get(url, params=params) as resp:
        if resp.status in (401, 403):
            raise TomTomAuthError(resp.status, await resp.text())
        if resp.status != 200:
            raise TomTomApiError(resp.status, await resp.text())
        data = await resp.json()

    summary = data["routes"][0]["summary"]
    return RoutePrediction(
        duration_min=summary["travelTimeInSeconds"] / 60,
        distance_km=summary["lengthInMeters"] / 1000,
    )
