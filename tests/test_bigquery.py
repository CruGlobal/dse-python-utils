from unittest.mock import Mock, MagicMock, patch
from cru_dse_utils import get_schema_bigquery


@patch("cru_dse_utils.bigquery.get_authorized_session_google")
def test_get_schema_bigquery_success(mock_get_session):
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

    result = get_schema_bigquery(project_id, dataset_id, table_id, secrete_name)

    print(f"Mocked session: {mock_get_session()}")
    print(f"Result: {result}")

    # Ensure the session get method was called with the right argument
    url = f"https://bigquery.googleapis.com/bigquery/v2/projects/{project_id}/datasets/{dataset_id}/tables/{table_id}"
    session.get.assert_called_once_with(url)

    assert result == mock_response["schema"]["fields"]


@patch("cru_dse_utils.bigquery.get_authorized_session_google")
def test_get_schema_bigquery_server_error(mock_get_session):
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

    result = get_schema_bigquery(project_id, dataset_id, table_id, secrete_name)

    assert result is None


@patch("cru_dse_utils.bigquery.get_authorized_session_google")
def test_get_schema_bigquery_auth_error(mock_get_session):
    mock_get_session.return_value = None
    project_id, dataset_id, table_id, secrete_name = (
        "test_project",
        "test_dataset",
        "test_table",
        "test_secrete",
    )

    result = get_schema_bigquery(project_id, dataset_id, table_id, secrete_name)

    assert result is None
