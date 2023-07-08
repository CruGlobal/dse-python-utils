import pytest
from unittest.mock import patch, MagicMock
import requests
from cru_dse_utils import get_dbt_job_list, trigger_dbt_job, get_dbt_run_status, dbt_run


# Fixture to setup variables for get_dbt_job_list
@pytest.fixture
def setup_variables_get_dbt_job_list():
    secret_name = "MY_SECRET"
    account_id = "12345"
    return secret_name, account_id


# Test get_dbt_job for a successful request where everything works as expected.
@patch("cru_dse_utils.dbt.get_general_credentials")
@patch("cru_dse_utils.dbt.requests")
@patch("cru_dse_utils.dbt.logging")
def test_get_dbt_job_list(
    mock_logging, mock_requests, mock_get_credentials, setup_variables_get_dbt_job_list
):
    # Arrange
    secret_name, account_id = setup_variables_get_dbt_job_list
    mock_get_credentials.return_value = "fake_token"
    mock_response = MagicMock()
    mock_requests.get.return_value = mock_response

    # Act
    get_dbt_job_list(account_id, secret_name)

    # Assert
    mock_get_credentials.assert_called_once_with(secret_name)
    mock_requests.get.assert_called_once_with(
        f"https://cloud.getdbt.com/api/v2/accounts/{account_id}/jobs/",
        headers={
            "Authorization": f"Token fake_token",
            "Content-Type": "application/json",
        },
    )
    mock_response.raise_for_status.assert_called_once()


# Test get_dbt_job for an unsuccessful attempt to retrieve the dbt Cloud API token.
@patch("cru_dse_utils.dbt.get_general_credentials")
@patch("cru_dse_utils.dbt.requests")
@patch("cru_dse_utils.dbt.logging")
def test_get_dbt_job_list_no_credentials(
    mock_logging, mock_requests, mock_get_credentials, setup_variables_get_dbt_job_list
):
    # Arrange
    secret_name, account_id = setup_variables_get_dbt_job_list
    mock_get_credentials.return_value = None

    # Act
    result = get_dbt_job_list(account_id, secret_name)

    # Assert
    mock_get_credentials.assert_called_once_with(secret_name)
    mock_logging.getLogger.return_value.error.assert_called_once_with(
        f"Failed to get dbt token with {secret_name}"
    )
    assert result is None


# Test get_dbt_job for an exception thrown while trying to make the request
@patch("cru_dse_utils.dbt.get_general_credentials")
@patch("cru_dse_utils.dbt.requests")
@patch("cru_dse_utils.dbt.logging")
def test_get_dbt_job_list_request_error(
    mock_logging, mock_requests, mock_get_credentials, setup_variables_get_dbt_job_list
):
    # Arrange
    secret_name, account_id = setup_variables_get_dbt_job_list
    mock_get_credentials.return_value = "fake_token"
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        "Request failed"
    )
    mock_requests.get.return_value = mock_response

    # Act
    result = get_dbt_job_list(account_id, secret_name)

    # Assert
    mock_get_credentials.assert_called_once_with(secret_name)
    mock_requests.get.assert_called_once_with(
        f"https://cloud.getdbt.com/api/v2/accounts/{account_id}/jobs/",
        headers={
            "Authorization": f"Token fake_token",
            "Content-Type": "application/json",
        },
    )
    mock_response.raise_for_status.assert_called_once()
    mock_logging.getLogger.return_value.exception.assert_called_once()
    assert result is None


# fixture to set up variables for testing dbt_run related functions
@pytest.fixture
def setup_variables():
    account_id = "10206"
    job_id = "85521"
    secret_name = "MY_SECRET"
    token = "fake_token"
    run_id = "run123"
    return account_id, job_id, secret_name, token, run_id


# Test trigger_dbt_job for a successful request where everything works as expected.
@patch("cru_dse_utils.dbt.get_general_credentials")
@patch("cru_dse_utils.dbt.requests.post")
@patch("cru_dse_utils.dbt.logging")
def test_trigger_dbt_job(
    mock_logging, mock_post, mock_get_credentials, setup_variables
):
    # Arrange
    account_id, job_id, secret_name, token, run_id = setup_variables
    mock_get_credentials.return_value = token
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": {"id": run_id}}
    mock_post.return_value = mock_response

    # Act
    result = trigger_dbt_job(account_id, job_id, token)

    # Assert
    mock_post.assert_called_once()
    assert result == run_id


# Test get_dbt_run_status for a successful request where everything works as expected.
@patch("cru_dse_utils.dbt.requests.get")
@patch("cru_dse_utils.dbt.logging")
def test_get_dbt_run_status(mock_logging, mock_get, setup_variables):
    # Arrange
    account_id, job_id, secret_name, token, run_id = setup_variables
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": {"status": 10}}
    mock_get.return_value = mock_response

    # Act
    result = get_dbt_run_status(run_id, token)

    # Assert
    mock_get.assert_called_once()
    assert result == 10


# Test dbt_run for a successful request where everything works as expected.
@patch("cru_dse_utils.dbt.time.sleep")  # mock sleep to speed up tests
@patch("cru_dse_utils.dbt.get_dbt_run_status")
@patch("cru_dse_utils.dbt.trigger_dbt_job")
@patch("cru_dse_utils.dbt.get_general_credentials")
@patch("cru_dse_utils.dbt.logging")
def test_dbt_run(
    mock_logging,
    mock_get_credentials,
    mock_trigger_dbt_job,
    mock_get_dbt_run_status,
    mock_sleep,
    setup_variables,
):
    # Arrange
    account_id, job_id, secret_name, token, run_id = setup_variables
    mock_get_credentials.return_value = token
    mock_trigger_dbt_job.return_value = run_id
    mock_get_dbt_run_status.return_value = 10

    # Act
    dbt_run(account_id, job_id, secret_name)

    # Assert
    mock_get_credentials.assert_called_once_with(secret_name)
    mock_trigger_dbt_job.assert_called_once_with(account_id, job_id, token)
    mock_get_dbt_run_status.assert_called()
    mock_logging.getLogger.return_value.info.assert_called_with(
        f"dbt job run completed successfully."
    )
