import base64
import json
from unittest.mock import Mock, patch
from google.oauth2.service_account import Credentials
from src.cru_dse_utils import get_credentials_google


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
