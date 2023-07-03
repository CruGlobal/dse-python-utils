import requests
from typing import List, Dict, Any, Optional, Union
import time
import os
import json
import logging
import base64
from dotenv import load_dotenv

# from pythonjsonlogger import jsonlogger
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import AuthorizedSession


def get_request(
    url: str,
    headers: Dict[str, str],
    params: Dict[Any, Any],
    logger: logging.Logger,
    max_retries: int = 5,
) -> Union[requests.Response, None]:
    """
    Sends an HTTP GET request to the specified URL with the specified headers.

    This function sends an HTTP GET request to the specified URL with the specified headers. If the response is not a
    valid JSON object, the function will retry the request up to `max_retries` times. If the response is a 429 error,
    the function will retry the request with an increasing delay between retries.

    Args:
        url (str): The URL to send the request to.
        headers (Dict[str, str]): A dictionary of headers to include in the GET request.
        params (Dict[Any, Any]): A dictionary of parameters to include in the GET request.
        logger (logging.Logger): The logger object to use for logging.
        max_retries (int): The maximum number of times to retry the request if the response is not a valid JSON object.
        Defaults to 5.

    Returns:
        requests.Response or None: The response object if the request is successful and returns valid JSON,
        or None if the request fails after the maximum number of retries.

    Raises:
        requests.exceptions.HTTPError: If the GET request encounters an HTTP error (other than 429).
        requests.exceptions.Timeout: If the GET request times out.
        requests.exceptions.ConnectionError: If there is a connection error during the GET request.
        requests.exceptions.RequestException: If there is a general request error.
    """
    logger = logging.getLogger("primary_logger")
    retries = 0
    while retries <= max_retries:
        try:
            r = requests.get(url, headers=headers, params=params, timeout=60)
            r.raise_for_status()
            try:
                _ = r.json()
                return r
            except ValueError as e:
                # In case of invalid JSON response, retry the request
                retries += 1
                logger.warning(f"Invalid JSON response: {e}. Retry in 5 minutes...")
                time.sleep(300)
        except requests.exceptions.HTTPError as err:
            if err.response.status_code == 429:  # Handle 429 error
                logger.warning("API rate limit exceeded. Retry in 1 second...")
                delay = 1  # Initial delay is 1 second
                while True:
                    time.sleep(delay)  # Wait for the delay period
                    try:
                        r = requests.get(
                            url, headers=headers, params=params, timeout=60
                        )  # Retry the same URL
                        r.raise_for_status()
                        try:
                            _ = r.json()
                            return r
                        except ValueError as e:
                            retries += 1
                            logger.warning(
                                f"Invalid JSON response: {e}. Retry in 5 minutes..."
                            )
                            time.sleep(300)
                    except requests.exceptions.HTTPError as err:
                        if err.response.status_code == 429:  # Handle 429 error
                            logger.warning(
                                f"API rate limit exceeded. Retry in {delay*2} seconds..."
                            )
                            delay *= 2  # Double the delay period
                            continue  # Retry the same URL
                        else:
                            raise
                    break  # Break out of the retry loop if the request is successful
            else:
                raise
        except requests.exceptions.Timeout as e:
            logger.warning(f"Request timed out: {e}. Retry in 1 minutes...")
            retries += 1
            time.sleep(60)
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Get request connection error: {e}. Retry in 1 minutes...")
            retries += 1
            time.sleep(60)
        except requests.exceptions.RequestException as e:
            logger.warning(f"Get general request error: {e}. Retry in 5 minutes...")
            retries += 1
            time.sleep(300)
    logger.error(f"Get request failed after {max_retries + 1} attempts.")
    return None


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
        A `Credentials` object or None: Retrived Google Cloud credentials.
        or None if failed to retrive credentials.

    Raises:
        ValueError: If the secret name is not recognized.
    """
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
