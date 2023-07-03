import logging
import requests
from requests.models import Response
from unittest.mock import Mock, patch
from src.cru_dse_utils.general import get_request


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

    with patch("requests.get", return_value=mock_response):
        assert get_request(url, headers, params, logger) is None