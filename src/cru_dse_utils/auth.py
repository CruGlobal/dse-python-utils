import os
import json
import base64
import logging
from typing import List, Dict, Any, Optional, Union
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import AuthorizedSession


def get_google_credentials(secret_name: str) -> Union[Credentials, None]:
    """
    Retrieves Google Cloud credentials for the specified secret from local
    or Amazon ECS environment variables.

    This function retrieves the base64 encoded secrete value from environment
    variables by calling the `os.getenv()` function with the provided
    secrete name. The function then retrieves the Google Cloud credentials
    by calling the `from_service_account_info()` function with the service
    account info from The decoded secrete value. The function returns the
    resulting `Credentials` object.

    Args:
        secret_name (str): The name of the environment variable containing
        the secret value.

    Returns:
        A `Credentials` object or None: Retrived Google Cloud credentials.
        or None if failed to retrive credentials.
    """
    logger = logging.getLogger("primary_logger")
    try:
        secret_value_encoded = os.getenv(secret_name)
        if secret_value_encoded is None:
            logger.error(f"Failed to get Google Cloud credentials with {secret_name}")
            return None
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
    except Exception as e:
        logger.exception(f"Get Google Cloud credentials error with {str(e)}")
        return None


def get_google_authorized_session(secret_name: str) -> Union[AuthorizedSession, None]:
    """
    Convert Google Cloud credentials to AuthorizedSession for the specified
    secret from local or Amazon ECS environment variables.

    This function calls the get_google_credentials() with the provided
    secrete name. The function then converts the resulting `Credentials`
    object to an `AuthorizedSession` object. The function returns the
    resulting `AuthorizedSession` object.

    Args:
        secret_name (str): The name of the environment variable containing
        the secret value.

    Returns:
        A `AuthorizedSession` object or None: Retrived Google Cloud
        AuthorizedSession or None if failed to retrive credentials.
    """
    logger = logging.getLogger("primary_logger")
    credentials = get_google_credentials(secret_name)
    if credentials is None:
        return None
    try:
        session = AuthorizedSession(credentials)
        return session
    except Exception as e:
        logger.exception(f"Get Google Cloud AuthorizedSession error with {str(e)}")
        return None


def get_general_credentials(secret_name: str) -> Union[str, None]:
    """
    Retrieves a secret value from the environment variables.

    This function retrieves a secret value from the environment variables
    by calling the `os.getenv()` function with the appropriate environment
    variable name. The function then returns the resulting secret value as
    a string.

    Args:
        secret_name (str): The name of the environment variable containing
        the secret value.

    Returns:
        str or None: The secret value as a string or None if failed to
        retrieve secret value.
    """
    logger = logging.getLogger("primary_logger")
    secret_value_encoded = os.getenv(secret_name)
    if secret_value_encoded is None:
        logger.error(f"Failed to get secret value with {secret_name}")
        return None
    secret_value = base64.b64decode(secret_value_encoded).decode("utf-8")
    return secret_value
