import os
import json
import base64
from typing import List, Dict, Any, Optional, Union
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import AuthorizedSession


def get_credentials_google(secret_name: str) -> Union[Credentials, None]:
    """
    Retrieves Google Cloud credentials for the specified secret from local or Amazon ECS environment variables.

    This function retrieves the base64 encoded secrete value from environment variables
    by calling the `os.getenv()` function with the provided secrete name. The function then retrieves
    the Google Cloud credentials by calling the `from_service_account_info()`
    function with the service account info from The decoded secrete value.
    The function returns the resulting `Credentials` object.

    Args:
        secret_name (str): The name of the environment variable containing the secret value.

    Returns:
        A `Credentials` object or None: Retrived Google Cloud credentials.  2
        or None if failed to retrive credentials.
    """
    try:
        secret_value_encoded = os.getenv(secret_name)
        if secret_value_encoded is not None:
            credentials_dict = json.loads(
                base64.b64decode(secret_value_encoded).decode("utf-8")
            )
            scopes = [
                "https://www.googleapis.com/auth/cloud-platform",
                "https://www.googleapis.com/auth/drive",
                "https://www.googleapis.com/auth/bigquery",
            ]
            credentials = Credentials.from_service_account_info(
                credentials_dict, scopes=scopes
            )
            return credentials
        else:
            return None
    except Exception:
        return None


def get_authorized_session_google(secret_name: str) -> Union[AuthorizedSession, None]:
    """
    Convert Google Cloud credentials to AuthorizedSession for the specified secret from local or
    Amazon ECS environment variables.

    This function calls the get_credentials_google() with the provided secrete name. The function
    then converts the resulting `Credentials` object to an `AuthorizedSession` object.
    The function returns the resulting `AuthorizedSession` object.

    Args:
        secret_name (str): The name of the environment variable containing the secret value.

    Returns:
        A `AuthorizedSession` object or None: Retrived Google Cloud AuthorizedSession or None
        if failed to retrive credentials.
    """
    credentials = get_credentials_google(secret_name)
    if credentials is not None:
        session = AuthorizedSession(credentials)
        return session
    else:
        return None


def get_credentials_general(secret_name: str) -> Union[str, None]:
    """
    Retrieves a secret value from the environment variables.

    This function retrieves a secret value from the environment variables by calling the `os.getenv()` function with the
    appropriate environment variable name. The function then returns the resulting secret value as a string.

    Args:
        secret_name (str): The name of the environment variable containing the secret value.

    Returns:
        str or None: The secret value as a string or None if failed to retrieve secret value.
    """
    secret_value_encoded = os.getenv(secret_name)
    if secret_value_encoded is not None:
        secret_value = base64.b64decode(secret_value_encoded).decode("utf-8")
        return secret_value
    else:
        return None
