"""Config flow for Travel Forecast."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_API_KEY, CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TomTomAuthError, async_geocode
from .const import (
    CONF_DESTINATION,
    CONF_DESTINATION_LAT,
    CONF_DESTINATION_LON,
    CONF_ORIGIN,
    CONF_ORIGIN_LAT,
    CONF_ORIGIN_LON,
    CONF_REFRESH_INTERVAL,
    DEFAULT_REFRESH_INTERVAL_HOURS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): str,
        vol.Required(CONF_ORIGIN): str,
        vol.Required(CONF_DESTINATION): str,
        vol.Required(CONF_API_KEY): str,
    }
)


class TravelForecastConfigFlow(ConfigFlow, domain=DOMAIN):
    """One config entry = one origin/destination route."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> Any:
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            try:
                origin = await async_geocode(session, user_input[CONF_ORIGIN], user_input[CONF_API_KEY])
                destination = await async_geocode(
                    session, user_input[CONF_DESTINATION], user_input[CONF_API_KEY]
                )
            except TomTomAuthError as err:
                _LOGGER.warning("TomTom auth error during config flow: %s", err)
                errors["base"] = "invalid_auth"
            except ValueError as err:
                _LOGGER.warning("TomTom geocode error during config flow: %s", err)
                errors["base"] = "address_not_found"
            except Exception:  # noqa: BLE001 - surfaced to the user as a generic error
                _LOGGER.exception("Unexpected error during config flow")
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(
                    f"{origin.lat},{origin.lon}->{destination.lat},{destination.lon}"
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data={
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_API_KEY: user_input[CONF_API_KEY],
                        CONF_ORIGIN: origin.display_name,
                        CONF_ORIGIN_LAT: origin.lat,
                        CONF_ORIGIN_LON: origin.lon,
                        CONF_DESTINATION: destination.display_name,
                        CONF_DESTINATION_LAT: destination.lat,
                        CONF_DESTINATION_LON: destination.lon,
                    },
                )

        return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        return TravelForecastOptionsFlow()


class TravelForecastOptionsFlow(OptionsFlow):
    """Lets you tune the refresh interval after setup (e.g. if you add more routes)."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> Any:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options.get(CONF_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL_HOURS)
        schema = vol.Schema(
            {vol.Required(CONF_REFRESH_INTERVAL, default=current): vol.All(int, vol.Range(min=1, max=12))}
        )
        return self.async_show_form(step_id="init", data_schema=schema)
