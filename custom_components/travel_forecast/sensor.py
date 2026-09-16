"""Sensor platform for Travel Forecast."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_BEST_DURATION_MIN,
    ATTR_BEST_TIME,
    ATTR_DESTINATION,
    ATTR_FORECAST,
    ATTR_ORIGIN,
    ATTR_UPDATED_AT,
    CONF_DESTINATION,
    CONF_ORIGIN,
    DOMAIN,
)
from .coordinator import TravelForecastCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: TravelForecastCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            TravelForecastSensor(coordinator, entry),
            TravelForecastBestDepartureSensor(coordinator, entry),
        ]
    )


class TravelForecastSensor(CoordinatorEntity[TravelForecastCoordinator], SensorEntity):
    """State = predicted travel time (min) for the next hour; full 48h curve as an attribute."""

    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_icon = "mdi:car-clock"

    def __init__(self, coordinator: TravelForecastCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_forecast"
        self._attr_name = f"{entry.data[CONF_NAME]} travel time"

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None
        return round(self.coordinator.data[0].duration_min, 1)

    @property
    def extra_state_attributes(self) -> dict:
        if not self.coordinator.data:
            return {}
        return {
            ATTR_ORIGIN: self._entry.data[CONF_ORIGIN],
            ATTR_DESTINATION: self._entry.data[CONF_DESTINATION],
            ATTR_UPDATED_AT: self.coordinator.data[0].timestamp.isoformat(),
            ATTR_FORECAST: [
                {
                    "time": point.timestamp.isoformat(),
                    "duration_min": round(point.duration_min, 1),
                    "distance_km": round(point.distance_km, 1),
                }
                for point in self.coordinator.data
            ],
        }


class TravelForecastBestDepartureSensor(CoordinatorEntity[TravelForecastCoordinator], SensorEntity):
    """State = best duration (min) found in the forecast window; best_time as an attribute."""

    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_icon = "mdi:clock-check-outline"

    def __init__(self, coordinator: TravelForecastCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_best_departure"
        self._attr_name = f"{entry.data[CONF_NAME]} best departure"

    @property
    def _best_point(self):
        if not self.coordinator.data:
            return None
        return min(self.coordinator.data, key=lambda point: point.duration_min)

    @property
    def native_value(self) -> float | None:
        best = self._best_point
        return round(best.duration_min, 1) if best else None

    @property
    def extra_state_attributes(self) -> dict:
        best = self._best_point
        if not best:
            return {}
        return {
            ATTR_BEST_TIME: best.timestamp.isoformat(),
            ATTR_BEST_DURATION_MIN: round(best.duration_min, 1),
        }
