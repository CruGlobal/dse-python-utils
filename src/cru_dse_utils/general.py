import requests
from typing import List, Dict, Any, Optional, Union
import time
import logging


def get_request(
    url: str,
    headers: Dict[str, str],
    params: Dict[Any, Any],
    max_retries: int = 5,
) -> Union[requests.Response, None]:
    """
    Sends an HTTP GET request to the specified URL with the specified headers.

    This function sends an HTTP GET request to the specified URL with the
    specified headers. If the response is not a valid JSON object, the
    function will retry the request up to `max_retries` times. If the response
    is a 429 error, the function will retry the request with an increasing
    delay between retries.

    Args:
        url (str): The URL to send the request to.
        headers (Dict[str, str]): A dictionary of headers to include in the
        GET request.
        params (Dict[Any, Any]): A dictionary of parameters to include in the
        GET request.
        logger (logging.Logger): The logger object to use for logging.
        max_retries (int): The maximum number of times to retry the request
        if the response is not a valid JSON object. Defaults to 5.

    Returns:
        requests.Response or None: The response object if the request is
        successful and returns valid JSON, or None if the request fails after
        the maximum number of retries.

    Raises:
        requests.exceptions.HTTPError: If the GET request encounters an HTTP
        error (other than 429).
        requests.exceptions.Timeout: If the GET request times out.
        requests.exceptions.ConnectionError: If there is a connection error
        during the GET request.
        requests.exceptions.RequestException: If there is a general request
        error.
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
                logger.warning(
                    f"Invalid JSON response: {str(e)}. Retry in 5 minutes..."
                )
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
                                f"Invalid JSON response: {str(e)}. Retry in 5 minutes..."
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
            logger.warning(f"Request timed out: {str(e)}. Retry in 1 minutes...")
            retries += 1
            time.sleep(60)
        except requests.exceptions.ConnectionError as e:
            logger.warning(
                f"Get request connection error: {str(e)}. Retry in 1 minutes..."
            )
            retries += 1
            time.sleep(60)
        except requests.exceptions.RequestException as e:
            logger.warning(
                f"Get general request error: {str(e)}. Retry in 5 minutes..."
            )
            retries += 1
            time.sleep(300)
    logger.error(f"Get request failed after {max_retries + 1} attempts.")
    return None
