"""Constants for the Travel Forecast integration."""

DOMAIN = "travel_forecast"

CONF_ORIGIN = "origin"
CONF_ORIGIN_LAT = "origin_lat"
CONF_ORIGIN_LON = "origin_lon"
CONF_DESTINATION = "destination"
CONF_DESTINATION_LAT = "destination_lat"
CONF_DESTINATION_LON = "destination_lon"
CONF_REFRESH_INTERVAL = "refresh_interval_hours"

DEFAULT_REFRESH_INTERVAL_HOURS = 2
HORIZON_HOURS = 48

ATTR_FORECAST = "forecast"
ATTR_ORIGIN = "origin"
ATTR_DESTINATION = "destination"
ATTR_UPDATED_AT = "updated_at"
ATTR_BEST_TIME = "best_time"
ATTR_BEST_DURATION_MIN = "best_duration_min"

TOMTOM_GEOCODE_URL = "https://api.tomtom.com/search/2/geocode/{query}.json"
TOMTOM_ROUTE_URL = "https://api.tomtom.com/routing/1/calculateRoute/{origin}:{destination}/json"

# TomTom's free tier throttles bursts (confirmed via a live 429 while testing
# the config flow, which fired 48 near-simultaneous requests). Fetch the
# forecast sequentially with a small pause between requests instead.
REQUEST_DELAY_SECONDS = 0.3
