from typing import List, Dict, Any, Optional, Union
import logging
import pandas as pd
from google.cloud import bigquery
from google.cloud.bigquery import SchemaField
from cru_dse_utils import get_google_credentials, get_google_authorized_session


def get_schema_from_bigquery(
    project_id: str, dataset_id: str, table_id: str, secret_name: str
) -> Optional[List[Dict]]:
    """
    Fetches and returns the schema details of the specified table in Google
    BigQuery.

    This function fetches the schema details by building the required URL
    using project_id, dataset_id, and table_id. The function checks for a
    successful session authorization and successful response status for a
    GET request. It also logs the progress and possible errors during the
    operation.

    Args:
        project_id (str): The Google BigQuery Project ID.
        dataset_id (str): The Google BigQuery Dataset ID.
        table_id (str): The Google BigQuery Table ID.

    Returns:
        List[Dict] or None: A list of dictionaries in json format containing
        the schema details if the operation is successful, None otherwise.
    """
    logger = logging.getLogger("primary_logger")
    session = get_google_authorized_session(secret_name)
    if session is None:
        logger.error("Get schema from BigQuery error with authorization error")
        return None
    url = f"https://bigquery.googleapis.com/bigquery/v2/projects/{project_id}/datasets/{dataset_id}/tables/{table_id}"
    response = session.get(url)
    if response.status_code == 200:
        data = response.json()
        schema_json = data["schema"]["fields"]
        logger.info("Retrieved schemas from BigQuery.")
        return schema_json
    else:
        logger.error(
            f"Get schema from BigQuery error with status code {response.status_code}, response: {response.text}"
        )
        return None


def validate_upload_dataframe_to_bigquery_arguments(
    project_id: str,
    dataset_id: str,
    table_id: str,
    secret_name: str,
    df: pd.DataFrame,
):
    """
    Validate the arguments needed for upload_bigquery_dataframe().

    Args:
        project_id (str): The Google Cloud project ID.
        dataset_id (str): The BigQuery dataset ID.
        table_id (str): The BigQuery table ID.
        secret_name (str): The name of the environment variable
        used for Google Cloud authentication.
        df (pd.DataFrame): The pandas DataFrame containing the data to
        upload.

    Raises:
        AssertionError: If any of the arguments are None or if df is not
        a pandas DataFrame.
    """
    assert project_id, "project_id must not be None or empty"
    assert dataset_id, "dataset_id must not be None or empty"
    assert table_id, "table_id must not be None or empty"
    assert secret_name, "secret_name must not be None or empty"
    assert isinstance(df, pd.DataFrame), "df must be a pandas DataFrame"


def get_job_config(schema_json, write_disposition, job_config_override):
    """
    Get the BigQuery LoadJobConfig based on provided arguments.

    Args:
        schema_json (Dict[Any, Any]): A dictionary representing the schema
        of the BigQuery table.
        write_disposition (str): Write disposition for the load job. Default
        is "WRITE_TRUNCATE", other options are "WRITE_APPEND" and
        "WRITE_EMPTY".
        job_config_override (bigquery.LoadJobConfig): An optional
        LoadJobConfig instance. If provided, this config will be used and
        other parameters will be ignored.

    Returns:
        bigquery.LoadJobConfig: The load job configuration for uploading
        data to BigQuery.
    """
    if job_config_override:
        return job_config_override
    if schema_json:
        schema = [SchemaField.from_api_repr(field) for field in schema_json]
        return bigquery.LoadJobConfig(
            schema=schema,
            create_disposition="CREATE_IF_NEEDED",
            write_disposition=write_disposition,
        )
    return bigquery.LoadJobConfig(
        autodetect=True,
        create_disposition="CREATE_IF_NEEDED",
        write_disposition=write_disposition,
    )


def upload_dataframe_to_bigquery(
    project_id: str,
    dataset_id: str,
    table_id: str,
    secret_name: str,
    df: pd.DataFrame,
    schema_json: Optional[Dict[Any, Any]] = None,
    job_config_override: Optional[bigquery.LoadJobConfig] = None,
    write_disposition: Optional[str] = "WRITE_TRUNCATE",
) -> None:
    """
    Uploads data from a pandas DataFrame to a BigQuery table.

    This function validates the provided arguments, retrieves the Google Cloud
    credentials, prepares the load job configuration and then starts the
    upload process.

    Args:
        project_id (str): The Google Cloud project ID.
        dataset_id (str): The BigQuery dataset ID.
        table_id (str): The BigQuery table ID.
        secret_name (str): The name of the environment variable used for
        Google Cloud authentication.
        df (pd.DataFrame): The pandas DataFrame containing the data to upload.
        write_disposition (str, optional): Write disposition for the load job.
        Default is "WRITE_TRUNCATE". Other options are "WRITE_APPEND" and
        "WRITE_EMPTY".
        schema_json (Dict[Any, Any], optional): A dictionary representing the
        schema of the BigQuery table.
        job_config_override (bigquery.LoadJobConfig, optional): An optional
        LoadJobConfig instance. If provided, this config will be used and
        other parameters will be ignored.

    Raises:
        ValueError: If Google Cloud credentials are invalid or absent.
        Any exception raised during the upload process will be re-raised after
        being logged.
    """
    validate_upload_dataframe_to_bigquery_arguments(
        project_id, dataset_id, table_id, secret_name, df
    )

    logger = logging.getLogger("primary_logger")
    credentials = get_google_credentials(secret_name)
    if credentials is None:
        logger.error("Upload to BigQuery error with authorization error")
        raise ValueError("Invalid Google Cloud credentials")

    client = bigquery.Client(credentials=credentials)
    table_id_full = f"{project_id}.{dataset_id}.{table_id}"
    job_config = get_job_config(schema_json, write_disposition, job_config_override)

    logger.info(f"Starting to upload data to {table_id_full}")
    try:
        job = client.load_table_from_dataframe(df, table_id_full, job_config=job_config)
        job.result()
        logger.info(f"Uploaded data to {table_id_full}")
    except Exception as e:
        logger.exception(f"Upload to BigQuery error: {str(e)}")
        raise


def download_from_bigquery_as_dataframe(
    project_id: str, dataset_id: str, table_id: str, secret_name: str
) -> Union[pd.DataFrame, None]:
    """
    Download data from a BigQuery table to a pandas DataFrame.

    This function uploads a pandas DataFrame to the specified BigQuery table.
    The function logs a message indicating whether the upload succeeded or
    failed.

    Args:
        project_id (str): The Google Cloud project ID.
        dataset_id (str): The BigQuery dataset ID.
        table_id (str): The BigQuery table ID.
        secret_name (str): The name of the environment variable used for
        Google Cloud authentication.

    Returns:
        Union[pd.DataFrame, None]: The pandas DataFrame containing the data
        downloaded from BigQuery. If the authorization or download fails,
        None is returned.
    """
    logger = logging.getLogger("primary_logger")
    credentials = get_google_credentials(secret_name)
    if credentials is None:
        logger.error("Download from BigQuery error with authorization error")
        return None
    client = bigquery.Client(credentials=credentials)
    table_id_full = f"{project_id}.{dataset_id}.{table_id}"
    logger.info(f"Starting to download data from BigQuery table: {table_id_full}")
    try:
        df = client.list_rows(table_id_full).to_dataframe()
        logger.info(f"Downloaded data from BigQuery table: {table_id_full}")
        return df
    except Exception as e:
        logger.exception(f"Download from BigQuery error: {str(e)}")
        return None


def query_bigquery_as_dataframe(
    query: str, secrete_name: str
) -> Union[pd.DataFrame, None]:
    """
    Executes a SQL query on a BigQuery dataset and returns the results as
    a pandas DataFrame.

    This function executes a SQL query on a BigQuery dataset and returns
    the results as a pandas DataFrame. The function logs a message indicating
    the query that was executed, and logs a message indicating the number of
    rows that were returned by the query.

    Args:
        query (str): The SQL query to execute.
        secrete_name (str): The name of the environment variable used for
        Google Cloud authentication.

    Returns:
        Union[pd.DataFrame, None]: A pandas DataFrame containing the results
        of the query. If the authorization or query fails, None is returned.
    """
    logger = logging.getLogger("primary_logger")
    credentials = get_google_credentials(secrete_name)
    if credentials is None:
        logger.error("Query BigQuery error with authorization error")
        return None
    client = bigquery.Client(credentials=credentials)
    try:
        query_job = client.query(query)
        results = query_job.result()
        logger.info(f"Executed query.")
        return results.to_dataframe()
    except Exception as e:
        logger.exception(f"Query BigQuery error: {str(e)}")
        return None
