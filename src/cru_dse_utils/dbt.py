import logging
import requests
import time
from typing import List, Dict, Any, Optional, Union
from cru_dse_utils import get_general_credentials


def get_dbt_job_list(account_id: str, secret_name: str) -> None:
    """
    Fetches a list of dbt jobs for a given account.

    This function retrieves the dbt jobs list from the dbt Cloud API for a
    given account. The function logs a message indicating whether the
    operation was successful or failed. This function is intended to be
    used for testing dbt connections and permissions.

    Args:
        account_id (str): The ID of the account in dbt Cloud.
        secret_name (str): The name of the environment variable used for
        dbt Cloud API token.

    Returns:
        None.
    """
    logger = logging.getLogger("primary_logger")
    token = get_general_credentials(secret_name)
    if token is None:
        logger.error(f"Failed to get dbt token with {secret_name}")
        return None
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
    }
    url = f"https://cloud.getdbt.com/api/v2/accounts/{account_id}/jobs/"
    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        logger.info(f"Got dbt job list.")
    except Exception as e:
        logger.exception(f"List dbt job error: {str(e)}")


def trigger_dbt_job(account_id: str, job_id: str, token: str) -> Union[str, None]:
    """
    Triggers a dbt job.

    This function triggers a dbt job by sending a POST request to the
    specified URL with the specified headers and JSON payload. The function
    logs a message indicating whether the dbt job started successfully or
    failed, and returns the id of the dbt job run.

    Args:
        account_id (str): The ID of the account in dbt Cloud.
        job_id (str): The ID of the dbt job to be triggered.
        token (str): The dbt Cloud API token.

    Returns:
        str: The run_id of the dbt job run.
        None: If the dbt job failed to start.
    """
    logger = logging.getLogger("primary_logger")
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
    }
    url = f"https://cloud.getdbt.com/api/v2/accounts/{account_id}/jobs/{job_id}/run/"
    json = {"cause": "Triggered by python script API request"}
    try:
        r = requests.post(url, headers=headers, json=json)
        r.raise_for_status()
        logger.info(f"dbt job started successfully.")
        run_id = r.json()["data"]["id"]
        return run_id
    except Exception as e:
        logger.exception(f"dbt job failed to start: {str(e)}")
        return None


def get_dbt_run_status(run_id: str, token: str) -> int:
    """
    Retrieves the status of a dbt job run.

    This function retrieves the status of a dbt job run by sending a GET
    request to the specified URL with the specified headers and the dbt
    job run_id. The function logs a message indicating whether the dbt job
    status check succeeded or failed, and returns the status of the dbt
    job run.

    Args:
        run_id (str): The id of the dbt job run.
        token (str): The dbt Cloud API token.

    Returns:
        int: The status of the dbt job run.

    """
    logger = logging.getLogger("primary_logger")
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
    }
    url = f"https://cloud.getdbt.com/api/v2/accounts/10206/runs/{run_id}/"
    try:
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        status = r.json()["data"]["status"]
    except Exception as e:
        logger.exception(f"dbt job status check failed: {e}")
        status = 0
    return status


def dbt_run(
    account_id: str, job_id: str, secret_name: str, max_retries: int = 3
) -> None:
    """
    Runs a dbt job and checks its status, with retry logic.

    This function runs a dbt job by calling the `trigger_dbt_job()` function
    and then checks the status of the job by calling `get_dbt_run_status()`
    function every 30 seconds until the job is completed successfully,
    failed, or cancelled. If the job fails, it will retry up to 'max_retries' times.
    The function logs messages indicating the status of the dbt job and its final outcome.

    Args:
        account_id (str): The ID of the account in dbt Cloud.
        job_id (str): The ID of the dbt job to be triggered.
        secret_name (str): The name of the environment variable used for dbt Cloud API token.
        max_retries (int): Maximum number of retries if the job fails. Default is 3.

    Returns:
        None
    """
    logger = logging.getLogger("primary_logger")
    logger.info(f"Starting dbt job...")
    token = get_general_credentials(secret_name)
    if token is None:
        logger.error(f"Failed to get dbt token with {secret_name}")
        return

    retries = 0
    while retries <= max_retries:
        run_id = trigger_dbt_job(account_id, job_id, token)
        if run_id is None:
            logger.error(
                f"dbt run failed to start. Retry {retries + 1} of {max_retries + 1}"
            )
            retries += 1
            continue

        while True:
            time.sleep(30)
            status = get_dbt_run_status(run_id, token)
            status_str = {
                0: "Status not available",
                1: "Queued",
                2: "Starting",
                3: "Running",
                10: "Success",
                20: "Failed",
                30: "Cancelled",
            }.get(status, "Unknown")

            logger.info(f"dbt job status: {status} - {status_str}")

            if status == 10:
                logger.info(f"dbt job run completed successfully.")
                return  # Exit the function on success
            elif status in (20, 30):  # Failed or Cancelled
                if retries < max_retries:
                    logger.warning(
                        f"dbt job {status_str}. Retrying... (Attempt {retries + 1} of {max_retries})"
                    )
                    retries += 1
                    break  # Break the inner loop to retry
                else:
                    logger.error(f"dbt job {status_str} after {max_retries} retries.")
                    return  # Exit the function after max retries

    logger.error(
        f"dbt job failed to complete successfully after {max_retries} retries."
    )
