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

# Cap concurrent TomTom requests per refresh so we don't burst the free tier.
MAX_CONCURRENT_REQUESTS = 5
