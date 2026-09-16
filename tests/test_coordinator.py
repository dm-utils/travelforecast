"""Tests for the Travel Forecast coordinator."""

from datetime import timedelta

from homeassistant.const import CONF_API_KEY, CONF_NAME
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.travel_forecast.const import (
    CONF_DESTINATION,
    CONF_DESTINATION_LAT,
    CONF_DESTINATION_LON,
    CONF_ORIGIN,
    CONF_ORIGIN_LAT,
    CONF_ORIGIN_LON,
    DOMAIN,
    HORIZON_HOURS,
)
from custom_components.travel_forecast.coordinator import TravelForecastCoordinator

ROUTE_RESPONSE = {
    "routes": [
        {
            "summary": {
                "lengthInMeters": 367200,
                "travelTimeInSeconds": 12000,
                "trafficDelayInSeconds": 0,
                "arrivalTime": "2026-09-17T03:00:00+02:00",
            }
        }
    ]
}


async def test_coordinator_builds_full_forecast(hass: HomeAssistant, aioclient_mock) -> None:
    """One refresh should produce HORIZON_HOURS sorted, hourly-spaced points."""
    aioclient_mock.get(
        "https://api.tomtom.com/routing/1/calculateRoute/51.9,4.4:51.2,8.6/json",
        json=ROUTE_RESPONSE,
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_NAME: "Home to Office",
            CONF_API_KEY: "fake-key",
            CONF_ORIGIN: "Origin Address",
            CONF_ORIGIN_LAT: 51.9,
            CONF_ORIGIN_LON: 4.4,
            CONF_DESTINATION: "Destination Address",
            CONF_DESTINATION_LAT: 51.2,
            CONF_DESTINATION_LON: 8.6,
        },
    )
    entry.add_to_hass(hass)

    coordinator = TravelForecastCoordinator(hass, entry)
    await coordinator.async_refresh()

    assert coordinator.last_update_success
    assert len(coordinator.data) == HORIZON_HOURS
    assert aioclient_mock.call_count == HORIZON_HOURS

    for point in coordinator.data:
        assert point.duration_min == 200.0
        assert point.distance_km == 367.2

    timestamps = [point.timestamp for point in coordinator.data]
    assert timestamps == sorted(timestamps)
    for earlier, later in zip(timestamps, timestamps[1:]):
        assert later - earlier == timedelta(hours=1)
