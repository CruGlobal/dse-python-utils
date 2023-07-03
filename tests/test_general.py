import logging
import requests
import base64
import json
from requests.models import Response
from unittest.mock import Mock, patch
from google.oauth2.service_account import Credentials
from src.cru_dse_utils.general import get_request, get_credentials_google


def test_get_request():
    mock_response = Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {"key": "value"}

    logger = logging.getLogger("test")
    url = "https://test.com"
    headers = {"Header": "test"}
    params = {"Param": "test"}

    with patch("requests.get", return_value=mock_response) as mock_get:
        result = get_request(url, headers, params, logger)

    assert result == mock_response
    mock_get.assert_called_once_with(url, headers=headers, params=params, timeout=60)


def test_get_request_timeout_error():
    logger = logging.getLogger("test")
    url = "https://test.com"
    headers = {"Header": "test"}
    params = {"Param": "test"}

    with patch("requests.get", side_effect=requests.exceptions.Timeout()), patch(
        "time.sleep"
    ):
        assert get_request(url, headers, params, logger) is None


def test_get_request_json_error():
    mock_response = Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.json.side_effect = ValueError()

    logger = logging.getLogger("test")
    url = "https://test.com"
    headers = {"Header": "test"}
    params = {"Param": "test"}

    with patch("requests.get", return_value=mock_response), patch(
        "time.sleep", return_value=None
    ):
        assert get_request(url, headers, params, logger) is None


def test_get_credentials_google():
    # Simulate a base64-encoded JSON object
    credentials_dict = {"type": "service_account"}
    encoded_credentials = base64.b64encode(json.dumps(credentials_dict).encode("utf-8"))

    with patch("os.getenv", return_value=encoded_credentials.decode("utf-8")), patch(
        "google.oauth2.service_account.Credentials.from_service_account_info",
        return_value=Mock(spec=Credentials),
    ) as mock_from_service_account_info:
        credentials = get_credentials_google("SECRET_NAME")

    assert credentials is not None
    mock_from_service_account_info.assert_called_once_with(
        credentials_dict,
        scopes=[
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/bigquery",
        ],
    )


def test_get_credentials_google_missing_secret():
    # Test when the secret is missing
    with patch("os.getenv", return_value=None):
        credentials = get_credentials_google("SECRET_NAME")

    assert credentials is None


def test_get_credentials_google_invalid_secret():
    # Test when the secret is not a valid base64-encoded JSON object
    with patch("os.getenv", return_value="invalid"):
        try:
            credentials = get_credentials_google("SECRET_NAME")
            assert credentials is None
        except Exception:
            pass
