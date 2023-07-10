import logging
import requests
from requests.models import Response
from unittest.mock import Mock, patch
from cru_dse_utils import get_request


# Test get_request for a successful request where everything works as expected.
def test_get_request():
    mock_response = Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {"key": "value"}

    logger = logging.getLogger("test")
    url = "https://test.com"
    headers = {"Header": "test"}
    params = {"Param": "test"}

    with patch("requests.get", return_value=mock_response) as mock_get:
        result = get_request(url, headers, params)

    assert result == mock_response
    mock_get.assert_called_once_with(url, headers=headers, params=params, timeout=60)


# Test get_request for timeout error.
def test_get_request_timeout_error():
    logger = logging.getLogger("test")
    url = "https://test.com"
    headers = {"Header": "test"}
    params = {"Param": "test"}

    with patch("requests.get", side_effect=requests.exceptions.Timeout()), patch(
        "time.sleep"
    ):
        assert get_request(url, headers, params) is None


# Test get_request for connection error.
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
        assert get_request(url, headers, params) is None
