# Travel Forecast

Home Assistant custom integration that predicts driving travel time for a
given origin/destination **per hour, up to 48 hours ahead** — instead of only
the live "right now" travel time that `google_travel_time` and
`waze_travel_time` already provide.

Uses the [TomTom Routing API](https://developer.tomtom.com/routing-api)
(`departAt` + traffic-aware duration) to build an hourly forecast curve, plus
a `best_departure` sensor that surfaces the cheapest travel-time window in
that curve.

Status: early development, not yet installable. See
[DESIGN.md](DESIGN.md) for the implementation plan.

## License

MIT — see [LICENSE](LICENSE).
