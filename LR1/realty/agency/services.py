import json
import logging
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


logger = logging.getLogger("realty")


class ExternalAPIError(Exception):
    pass


def fetch_json(url: str, headers: dict | None = None):
    request_headers = {"User-Agent": "realty/1.0"}
    if headers:
        request_headers.update(headers)
    request = Request(url, headers=request_headers)
    try:
        with urlopen(request, timeout=5) as response:
            payload = response.read().decode("utf-8")
    except (HTTPError, URLError, TimeoutError) as exc:
        logger.warning("External API request failed for %s: %s", url, exc)
        raise ExternalAPIError(str(exc)) from exc
    return json.loads(payload)


def fetch_exchange_rates():
    rates = {}
    for code in ("USD", "EUR"):
        payload = fetch_json(f"https://api.nbrb.by/exrates/rates/{code}?parammode=2")
        rates[code] = {
            "scale": payload.get("Cur_Scale", 1),
            "rate": Decimal(str(payload["Cur_OfficialRate"])),
        }
    logger.info("Loaded exchange rates from NBRB: %s", ", ".join(rates.keys()))
    return rates


def geocode_address(address: str):
    payload = fetch_json(
        "https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&q="
        f"{quote(address)}",
        headers={"Accept-Language": "ru"},
    )
    if not payload:
        logger.info("No geocoding results for %s", address)
        return None
    first_item = payload[0]
    return {
        "lat": float(first_item["lat"]),
        "lon": float(first_item["lon"]),
        "display_name": first_item["display_name"],
    }


def fetch_weather(latitude: float, longitude: float):
    payload = fetch_json(
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}&longitude={longitude}"
        "&current=temperature_2m,wind_speed_10m&timezone=auto"
    )
    current = payload.get("current", {})
    logger.info("Loaded weather for lat=%s lon=%s", latitude, longitude)
    return {
        "time": current.get("time"),
        "temperature": current.get("temperature_2m"),
        "wind_speed": current.get("wind_speed_10m"),
    }
