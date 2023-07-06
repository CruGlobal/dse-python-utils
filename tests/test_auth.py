import base64
import json
import os
from unittest.mock import Mock, patch
import pytest
from google.oauth2.service_account import Credentials
from cru_dse_utils import (
    get_credentials_google,
    get_authorized_session_google,
    get_credentials_general,
)


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
        credentials = get_credentials_google("SECRET_NAME")
    assert credentials is None


@pytest.fixture
def mock_get_credentials_google():
    with patch("cru_dse_utils.auth.get_credentials_google") as mock_get_credentials:
        yield mock_get_credentials


def test_get_authorized_session_google_with_credentials(mock_get_credentials_google):
    credentials_mock = "mock_credentials"
    mock_get_credentials_google.return_value = credentials_mock
    session = get_authorized_session_google("secret_name")
    assert session is not None
    assert session.credentials == credentials_mock


def test_get_authorized_session_google_without_credentials(mock_get_credentials_google):
    mock_get_credentials_google.return_value = None
    session = get_authorized_session_google("secret_name")
    assert session is None


@pytest.fixture
def mock_os_getenv(monkeypatch):
    def mock_getenv(secret_name):
        if secret_name == "EXISTING_SECRET":
            return "VGVzdFNlY3JldA=="  # Base64 encoded value of "TestSecret"
        else:
            return None

    monkeypatch.setattr(os, "getenv", mock_getenv)


def test_get_credentials_general_with_existing_secret(mock_os_getenv):
    secret_name = "EXISTING_SECRET"
    result = get_credentials_general(secret_name)
    assert result == "TestSecret"


def test_get_credentials_general_with_non_existing_secret(mock_os_getenv):
    secret_name = "NON_EXISTING_SECRET"
    result = get_credentials_general(secret_name)
    assert result is None


def test_get_credentials_general_with_invalid_secret_name():
    secret_name = "INVALID_SECRET_NAME"
    result = get_credentials_general(secret_name)
    assert result is None
