import base64
import json
import os
from unittest.mock import Mock, patch
import pytest
from google.oauth2.service_account import Credentials
from cru_dse_utils import (
    get_google_credentials,
    get_google_authorized_session,
    get_general_credentials,
)


# Test get_google_credentials for a successful request where everything works as expected.
def test_get_google_credentials():
    # Simulate a base64-encoded JSON object
    credentials_dict = {"type": "service_account"}
    encoded_credentials = base64.b64encode(json.dumps(credentials_dict).encode("utf-8"))

    with patch("os.getenv", return_value=encoded_credentials.decode("utf-8")), patch(
        "google.oauth2.service_account.Credentials.from_service_account_info",
        return_value=Mock(spec=Credentials),
    ) as mock_from_service_account_info:
        credentials = get_google_credentials("SECRET_NAME")

    assert credentials is not None
    mock_from_service_account_info.assert_called_once_with(
        credentials_dict,
        scopes=[
            "https://www.googleapis.com/auth/cloud-platform",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/bigquery",
        ],
    )


# Test get_google_credentials for a failed request where the secret is missing.
def test_get_google_credentials_missing_secret():
    # Test when the secret is missing
    with patch("os.getenv", return_value=None):
        credentials = get_google_credentials("SECRET_NAME")

    assert credentials is None


# Test get_google_credentials for a failed request where the secret is invalid.
def test_get_google_credentials_invalid_secret():
    # Test when the secret is not a valid base64-encoded JSON object
    with patch("os.getenv", return_value="invalid"):
        credentials = get_google_credentials("SECRET_NAME")
    assert credentials is None


# Fixture to mock get_google_credentials
@pytest.fixture
def mock_get_google_credentials():
    with patch("cru_dse_utils.auth.get_google_credentials") as mock_get_credentials:
        yield mock_get_credentials


# Test get_google_authorized_session for a successful request where everything works as expected.
def test_get_google_authorized_session_with_credentials(mock_get_google_credentials):
    credentials_mock = "mock_credentials"
    mock_get_google_credentials.return_value = credentials_mock
    session = get_google_authorized_session("secret_name")
    assert session is not None
    assert session.credentials == credentials_mock


# Test get_google_authorized_session for a failed request where the credentials are missing.
def test_get_google_authorized_session_without_credentials(mock_get_google_credentials):
    mock_get_google_credentials.return_value = None
    session = get_google_authorized_session("secret_name")
    assert session is None


# Fixture to mock get_google_general_credentials
@pytest.fixture
def mock_os_getenv(monkeypatch):
    def mock_getenv(secret_name):
        if secret_name == "EXISTING_SECRET":
            return "VGVzdFNlY3JldA=="  # Base64 encoded value of "TestSecret"
        else:
            return None

    monkeypatch.setattr(os, "getenv", mock_getenv)


# Test get_general_credentials with a working secret.
def test_get_general_credentials_with_existing_secret(mock_os_getenv):
    secret_name = "EXISTING_SECRET"
    result = get_general_credentials(secret_name)
    assert result == "TestSecret"


# Test get_general_credentials with a non-existing secret.
def test_get_general_credentials_with_non_existing_secret(mock_os_getenv):
    secret_name = "NON_EXISTING_SECRET"
    result = get_general_credentials(secret_name)
    assert result is None


# Test get_general_credentials with an invalid secret.
def test_get_general_credentials_with_invalid_secret_name():
    secret_name = "INVALID_SECRET_NAME"
    result = get_general_credentials(secret_name)
    assert result is None
