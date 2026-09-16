# Travel Forecast

Home Assistant custom integration that predicts driving travel time for a
given origin/destination **per hour, up to 48 hours ahead** — instead of only
the live "right now" travel time that `google_travel_time` and
`waze_travel_time` already provide.

Uses the [TomTom Routing API](https://developer.tomtom.com/routing-api)
(`departAt` + traffic-aware duration) to build an hourly forecast curve, plus
a `best_departure` sensor that surfaces the cheapest travel-time window in
that curve.

Status: v1 working, verified end to end on a real Home Assistant OS
install — real route showed 224 min at 10:00, peaking at 242 min around
17:00 rush hour, down to 200 min overnight. Not yet packaged for HACS
install (manual copy into `custom_components/` for now). See
[DESIGN.md](DESIGN.md) for the implementation plan.

## Installation (manual, pre-HACS)

Copy `custom_components/travel_forecast/` into your Home Assistant
`config/custom_components/` directory, restart Home Assistant, then add
it via Settings → Devices & services → Add integration → Travel Forecast.
You'll need a free [TomTom API key](https://developer.tomtom.com) with
the Geocoding and Routing APIs enabled.

## License

MIT — see [LICENSE](LICENSE).
