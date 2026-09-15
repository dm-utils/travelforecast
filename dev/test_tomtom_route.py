"""One-off script to validate the TomTom geocode + routing call shape
before wiring it into the HA coordinator. Not part of the integration
itself. Reads TOMTOM_API_KEY from ../.env (gitignored).

Note: trafficDelayInSeconds stays 0 for a future departAt — TomTom only
reports it as a live/incident field. travelTimeInSeconds itself already
reflects the time-of-day-adjusted (historical traffic) duration, so the
coordinator should forecast on that value, not trafficDelayInSeconds.

Usage:
    pip install -r dev/requirements.txt
    python dev/test_tomtom_route.py
"""

from __future__ import annotations

import json
import ssl
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import certifi

ORIGIN_ADDRESS = "Rotterdamse Rijweg 121"
DESTINATION_ADDRESS = "Kustelberger Strasse 7, Medebach"

# TomTom's cert chain isn't fully trusted by Python's default SSL store on
# this machine (curl/Windows handle it fine via a different trust store);
# use the well-maintained Mozilla bundle from certifi instead.
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def load_api_key() -> str:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("TOMTOM_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError(f"TOMTOM_API_KEY not found in {env_path}")


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, context=SSL_CONTEXT) as resp:
        print(f"  HTTP {resp.status} | {url.split('?')[0]}")
        for header in ("X-RateLimit-Limit", "X-RateLimit-Remaining"):
            if resp.headers.get(header):
                print(f"  {header}: {resp.headers.get(header)}")
        return json.loads(resp.read().decode("utf-8"))


def geocode(address: str, api_key: str) -> tuple[float, float]:
    quoted = urllib.parse.quote(address)
    url = f"https://api.tomtom.com/search/2/geocode/{quoted}.json?key={api_key}&limit=1"
    data = get_json(url)
    results = data.get("results") or []
    if not results:
        raise RuntimeError(f"No geocode result for: {address}")
    pos = results[0]["position"]
    print(f"  -> {results[0].get('address', {}).get('freeformAddress')} ({pos['lat']}, {pos['lon']})")
    return pos["lat"], pos["lon"]


def calculate_route(origin: tuple[float, float], destination: tuple[float, float], depart_at: str, api_key: str) -> dict:
    origin_str = f"{origin[0]},{origin[1]}"
    dest_str = f"{destination[0]},{destination[1]}"
    url = (
        f"https://api.tomtom.com/routing/1/calculateRoute/{origin_str}:{dest_str}/json"
        f"?key={api_key}&traffic=true&departAt={depart_at}"
    )
    return get_json(url)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    api_key = load_api_key()

    print(f"Geocoding origin: {ORIGIN_ADDRESS}")
    origin = geocode(ORIGIN_ADDRESS, api_key)

    print(f"Geocoding destination: {DESTINATION_ADDRESS}")
    destination = geocode(DESTINATION_ADDRESS, api_key)

    depart_at = (datetime.now() + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0).isoformat()
    print(f"\nCalculating route, departAt={depart_at}")
    route = calculate_route(origin, destination, depart_at, api_key)

    summary = route["routes"][0]["summary"]
    print("\n--- Route summary ---")
    print(f"  Distance:            {summary['lengthInMeters'] / 1000:.1f} km")
    print(f"  Travel time:         {summary['travelTimeInSeconds'] / 60:.1f} min")
    print(f"  Traffic delay:       {summary.get('trafficDelayInSeconds', 0) / 60:.1f} min")
    print(f"  Arrival:             {summary.get('arrivalTime')}")


if __name__ == "__main__":
    main()
