"""Tests for the Travel Forecast config flow."""

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.travel_forecast.const import (
    CONF_DESTINATION,
    CONF_DESTINATION_LAT,
    CONF_DESTINATION_LON,
    CONF_ORIGIN,
    CONF_ORIGIN_LAT,
    CONF_ORIGIN_LON,
    DOMAIN,
)

ORIGIN_ADDRESS = "Origin Address"
DESTINATION_ADDRESS = "Destination Address"
USER_INPUT = {
    CONF_NAME: "Home to Office",
    CONF_ORIGIN: ORIGIN_ADDRESS,
    CONF_DESTINATION: DESTINATION_ADDRESS,
    CONF_API_KEY: "fake-key",
}


def _geocode_url(address: str) -> str:
    return f"https://api.tomtom.com/search/2/geocode/{address.replace(' ', '%20')}.json"


def _mock_geocode(aioclient_mock, address: str, lat: float, lon: float) -> None:
    aioclient_mock.get(
        _geocode_url(address),
        json={
            "results": [
                {
                    "position": {"lat": lat, "lon": lon},
                    "address": {"freeformAddress": address},
                }
            ]
        },
    )


async def test_user_flow_creates_entry(hass: HomeAssistant, aioclient_mock) -> None:
    """A valid origin/destination + key should geocode both and create an entry."""
    _mock_geocode(aioclient_mock, ORIGIN_ADDRESS, 51.9, 4.4)
    _mock_geocode(aioclient_mock, DESTINATION_ADDRESS, 51.2, 8.6)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Home to Office"
    assert result["data"][CONF_ORIGIN_LAT] == 51.9
    assert result["data"][CONF_ORIGIN_LON] == 4.4
    assert result["data"][CONF_DESTINATION_LAT] == 51.2
    assert result["data"][CONF_DESTINATION_LON] == 8.6


async def test_user_flow_invalid_auth(hass: HomeAssistant, aioclient_mock) -> None:
    """A 403 from TomTom should surface as an invalid_auth form error, not a crash."""
    aioclient_mock.get(_geocode_url(ORIGIN_ADDRESS), status=403, json={"detailedError": {}})

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_user_flow_address_not_found(hass: HomeAssistant, aioclient_mock) -> None:
    """An empty geocode result should surface as address_not_found, not a crash."""
    aioclient_mock.get(_geocode_url(ORIGIN_ADDRESS), json={"results": []})

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "address_not_found"}
