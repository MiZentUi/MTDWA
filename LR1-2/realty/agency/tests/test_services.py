import json
from urllib.error import URLError
from unittest.mock import patch

from agency.services import ExternalAPIError, fetch_exchange_rates, fetch_json, geocode_address

from .base import BaseDataMixin


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class ServiceTests(BaseDataMixin):
    @patch("agency.services.urlopen")
    def test_fetch_exchange_rates_parses_payload(self, mocked_urlopen):
        mocked_urlopen.side_effect = [
            FakeResponse({"Cur_OfficialRate": 3.2, "Cur_Scale": 1}),
            FakeResponse({"Cur_OfficialRate": 3.45, "Cur_Scale": 1}),
        ]
        rates = fetch_exchange_rates()
        self.assertIn("USD", rates)
        self.assertIn("EUR", rates)

    @patch("agency.services.fetch_json", return_value=[])
    def test_geocode_address_returns_none_when_no_data(self, mocked_fetch):
        result = geocode_address("Минск, улица 1")
        self.assertIsNone(result)
        mocked_fetch.assert_called_once()

    @patch("agency.services.urlopen", side_effect=URLError("boom"))
    def test_fetch_json_raises_custom_error(self, mocked_urlopen):
        with self.assertRaises(ExternalAPIError):
            fetch_json("https://example.com")
        mocked_urlopen.assert_called_once()
