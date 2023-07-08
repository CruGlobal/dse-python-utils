from unittest.mock import Mock, MagicMock, patch
import pytest
from google.cloud import bigquery
import pandas as pd
from cru_dse_utils import (
    get_schema_from_bigquery,
    upload_dataframe_to_bigquery,
    download_from_bigquery_as_dataframe,
    query_bigquery_as_dataframe,
)


# Test upload_dataframe_to_bigquery for a successful request where everything works as expected.
@patch("cru_dse_utils.bigquery.get_google_authorized_session")
def test_get_schema_from_bigquery_success(mock_get_session):
    response = MagicMock()
    mock_response = {"schema": {"fields": [{"name": "field1", "type": "STRING"}]}}
    response.status_code = 200
    response.json.return_value = mock_response

    session = MagicMock()
    session.get.return_value = response
    mock_get_session.return_value = session

    project_id, dataset_id, table_id, secrete_name = (
        "test_project",
        "test_dataset",
        "test_table",
        "test_secrete",
    )

    result = get_schema_from_bigquery(project_id, dataset_id, table_id, secrete_name)

    print(f"Mocked session: {mock_get_session()}")
    print(f"Result: {result}")

    # Ensure the session get method was called with the right argument
    url = f"https://bigquery.googleapis.com/bigquery/v2/projects/{project_id}/datasets/{dataset_id}/tables/{table_id}"
    session.get.assert_called_once_with(url)

    assert result == mock_response["schema"]["fields"]


# Test upload_dataframe_to_bigquery for server error.
@patch("cru_dse_utils.bigquery.get_google_authorized_session")
def test_get_schema_from_bigquery_server_error(mock_get_session):
    error_code = 500
    mock_get_session.return_value = MagicMock(
        get=MagicMock(return_value=MagicMock(status_code=error_code))
    )
    project_id, dataset_id, table_id, secrete_name = (
        "test_project",
        "test_dataset",
        "test_table",
        "test_secrete",
    )

    result = get_schema_from_bigquery(project_id, dataset_id, table_id, secrete_name)

    assert result is None


# Test upload_dataframe_to_bigquery for auth error.
@patch("cru_dse_utils.bigquery.get_google_authorized_session")
def test_get_schema_from_bigquery_auth_error(mock_get_session):
    mock_get_session.return_value = None
    project_id, dataset_id, table_id, secrete_name = (
        "test_project",
        "test_dataset",
        "test_table",
        "test_secrete",
    )

    result = get_schema_from_bigquery(project_id, dataset_id, table_id, secrete_name)

    assert result is None


# Test upload_dataframe_to_bigquery for a successful request where everything works as expected.
@patch("cru_dse_utils.bigquery.bigquery.Client")
@patch("cru_dse_utils.bigquery.get_google_credentials")
def test_upload_dataframe_to_bigquery(
    mock_get_google_credentials, mock_bigquery_client
):
    # create some mock objects for the tests
    mock_credentials = Mock()
    mock_df = Mock(spec=pd.DataFrame)
    mock_job = Mock()
    mock_client = Mock()
    mock_load_job_config = Mock()

    # setup the return values for the mock objects
    mock_get_google_credentials.return_value = mock_credentials
    mock_bigquery_client.return_value = mock_client
    mock_client.load_table_from_dataframe.return_value = mock_job
    mock_load_job_config.return_value = mock_load_job_config

    # run the function with the mock objects
    upload_dataframe_to_bigquery(
        "project_id",
        "dataset_id",
        "table_id",
        "secret_name",
        mock_df,
        {},
    )

    # check that the mock objects were used as expected
    mock_get_google_credentials.assert_called_once_with("secret_name")
    mock_bigquery_client.assert_called_once_with(credentials=mock_credentials)
    mock_client.load_table_from_dataframe.assert_called_once()
    mock_job.result.assert_called_once()


# Test upload_dataframe_to_bigquery the override of the job config was used.
@patch("cru_dse_utils.bigquery.bigquery.Client")
@patch("cru_dse_utils.bigquery.get_google_credentials")
def test_upload_dataframe_to_bigquery_with_config_override(
    mock_get_google_credentials, mock_bigquery_client
):
    # create some mock objects for the tests
    mock_credentials = Mock()
    mock_df = Mock(spec=pd.DataFrame)
    mock_job = Mock()
    mock_client = Mock()
    mock_load_job_config = Mock(spec=bigquery.LoadJobConfig)

    # setup the return values for the mock objects
    mock_get_google_credentials.return_value = mock_credentials
    mock_bigquery_client.return_value = mock_client
    mock_client.load_table_from_dataframe.return_value = mock_job

    # run the function with the mock objects and a mock LoadJobConfig
    upload_dataframe_to_bigquery(
        "project_id",
        "dataset_id",
        "table_id",
        "secret_name",
        mock_df,
        {},
        job_config_override=mock_load_job_config,
    )

    # check that the mock LoadJobConfig was used
    mock_client.load_table_from_dataframe.assert_called_once_with(
        mock_df, "project_id.dataset_id.table_id", job_config=mock_load_job_config
    )


# Test upload_dataframe_to_bigquery for an unsuccessful attempt to get the credentials.
@patch("cru_dse_utils.bigquery.get_google_credentials")
@patch("cru_dse_utils.bigquery.logging.getLogger")
def test_upload_dataframe_to_bigquery_no_credentials(
    mock_getLogger, mock_get_google_credentials
):
    # setup the return values for the mock objects
    mock_get_google_credentials.return_value = None
    mock_logger = Mock()
    mock_df = Mock(spec=pd.DataFrame)
    mock_getLogger.return_value = mock_logger

    # run the function with the mock objects
    try:
        upload_dataframe_to_bigquery(
            "project_id",
            "dataset_id",
            "table_id",
            "secret_name",
            mock_df,
            {},
        )
    except ValueError as e:
        # check that the appropriate error was thrown
        assert str(e) == "Invalid Google Cloud credentials"
    else:
        pytest.fail("Expected ValueError was not raised")

    # check that the appropriate error was logged
    mock_getLogger.assert_called_once_with("primary_logger")
    mock_logger.error.assert_called_once_with(
        "Upload to BigQuery error with authorization error"
    )


# Test download_from_bigquery_as_dataframe for a successful request where everything works as expected.
@patch("cru_dse_utils.bigquery.bigquery.Client")
@patch("cru_dse_utils.bigquery.get_google_credentials")
def test_download_from_bigquery_as_dataframe(
    mock_get_google_credentials, mock_bigquery_client
):
    # create some mock objects for the tests
    mock_credentials = Mock()
    mock_df = Mock(spec=pd.DataFrame)
    mock_list_rows_result = MagicMock()
    mock_client = Mock()

    # setup the return values for the mock objects
    mock_get_google_credentials.return_value = mock_credentials
    mock_bigquery_client.return_value = mock_client
    mock_client.list_rows.return_value = mock_list_rows_result
    mock_list_rows_result.to_dataframe.return_value = mock_df

    # run the function with the mock objects
    result = download_from_bigquery_as_dataframe(
        "project_id",
        "dataset_id",
        "table_id",
        "secret_name",
    )

    # check that the mock objects were used as expected
    mock_get_google_credentials.assert_called_once_with("secret_name")
    mock_bigquery_client.assert_called_once_with(credentials=mock_credentials)
    mock_client.list_rows.assert_called_once()
    mock_list_rows_result.to_dataframe.assert_called_once()
    assert isinstance(result, pd.DataFrame)


# Test download_from_bigquery_as_dataframe for an unsuccessful attempt to get the credentials.
@patch("cru_dse_utils.bigquery.get_google_credentials")
@patch("cru_dse_utils.bigquery.logging.getLogger")
def test_download_from_bigquery_as_dataframe_no_credentials(
    mock_getLogger, mock_get_google_credentials
):
    # setup the return values for the mock objects
    mock_get_google_credentials.return_value = None
    mock_logger = Mock()
    mock_getLogger.return_value = mock_logger

    # run the function with the mock objects

    result = download_from_bigquery_as_dataframe(
        "project_id",
        "dataset_id",
        "table_id",
        "secret_name",
    )

    assert result is None


# Test query_bigquery_as_dataframe for a successful request where everything works as expected.
@patch("cru_dse_utils.bigquery.get_google_credentials")
@patch("cru_dse_utils.bigquery.bigquery.Client")
@patch("cru_dse_utils.bigquery.logging")
def test_query_bigquery_as_dataframe(mock_logging, mock_client, mock_get_credentials):
    # Arrange
    query = "SELECT * FROM `bigquery-public-data.samples.gsod`"
    secrete_name = "MY_SECRET"
    mock_get_credentials.return_value = "fake_credentials"
    mock_client_instance = mock_client.return_value
    mock_query_job = MagicMock()
    mock_client_instance.query.return_value = mock_query_job
    mock_results = MagicMock()
    mock_query_job.result.return_value = mock_results
    mock_results.to_dataframe.return_value = pd.DataFrame()

    # Act
    result = query_bigquery_as_dataframe(query, secrete_name)

    # Assert
    mock_get_credentials.assert_called_once_with(secrete_name)
    mock_client.assert_called_once_with(credentials="fake_credentials")
    mock_client_instance.query.assert_called_once_with(query)
    mock_query_job.result.assert_called_once()
    mock_results.to_dataframe.assert_called_once()
    assert isinstance(result, pd.DataFrame)


# Test query_bigquery_as_dataframe for an unsuccessful request where the credentials are invalid.
@patch("cru_dse_utils.bigquery.get_google_credentials")
@patch("cru_dse_utils.bigquery.bigquery.Client")
@patch("cru_dse_utils.bigquery.logging")
def test_query_bigquery_as_dataframe_no_credentials(
    mock_logging, mock_client, mock_get_credentials
):
    # Arrange
    query = "SELECT * FROM `bigquery-public-data.samples.gsod`"
    secrete_name = "MY_SECRET"
    mock_get_credentials.return_value = None

    # Act
    result = query_bigquery_as_dataframe(query, secrete_name)

    # Assert
    mock_get_credentials.assert_called_once_with(secrete_name)
    mock_logging.getLogger.return_value.error.assert_called_once_with(
        "Query BigQuery error with authorization error"
    )
    assert result is None


# Test query_bigquery_as_dataframe for an unsuccessful request where the query fails.
@patch("cru_dse_utils.bigquery.get_google_credentials")
@patch("cru_dse_utils.bigquery.bigquery.Client")
@patch("cru_dse_utils.bigquery.logging")
def test_query_bigquery_as_dataframe_query_error(
    mock_logging, mock_client, mock_get_credentials
):
    # Arrange
    query = "SELECT * FROM `bigquery-public-data.samples.gsod`"
    secrete_name = "MY_SECRET"
    mock_get_credentials.return_value = "fake_credentials"
    mock_client_instance = mock_client.return_value
    mock_client_instance.query.side_effect = Exception("Query failed")

    # Act
    result = query_bigquery_as_dataframe(query, secrete_name)

    # Assert
    mock_get_credentials.assert_called_once_with(secrete_name)
    mock_client.assert_called_once_with(credentials="fake_credentials")
    mock_client_instance.query.assert_called_once_with(query)
    mock_logging.getLogger.return_value.exception.assert_called_once()
    assert result is None
