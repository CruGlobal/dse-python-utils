from typing import List, Dict, Any, Optional, Union
import logging
import json
from google.cloud import bigquery
from cru_dse_utils import get_authorized_session_google


def get_schema_bigquery(
    project_id: str, dataset_id: str, table_id: str, secret_name: str
) -> Optional[List[Dict]]:
    """
    Fetches and returns the schema details of the specified table in Google BigQuery.

    This function fetches the schema details by building the required URL using project_id,
    dataset_id, and table_id. The function checks for a successful session authorization and
    successful response status for a GET request. It also logs the progress and possible errors
    during the operation.

    Args:
        project_id (str): The Google BigQuery Project ID.
        dataset_id (str): The Google BigQuery Dataset ID.
        table_id (str): The Google BigQuery Table ID.

    Returns:
        List[Dict] or None: A list of dictionaries in json format containing the schema details
        if the operation is successful, None otherwise.

    Raises:
        HTTPError: If the GET request to the constructed URL returns a status code that indicates an error.
        AuthorizationError: If a session authorization fails in `get_authorized_session_google()`.
    """
    logger = logging.getLogger("primary_logger")
    session = get_authorized_session_google(secret_name)
    url = f"https://bigquery.googleapis.com/bigquery/v2/projects/{project_id}/datasets/{dataset_id}/tables/{table_id}"
    if session:
        # breakpoint()
        response = session.get(url)
        if response.status_code == 200:
            data = response.json()
            schema_json = data["schema"]["fields"]
            logger.info("Retrieved schemas from BigQuery.")
            # with open(f"{table_id}_schema.json", "w") as f:
            #     json.dump(schema_json, f)
            return schema_json
        else:
            logger.error(
                f"Get schema from BigQuery error with status code {response.status_code}, response: {response.text}"
            )
            return None
    else:
        logger.error("Get schema from BigQuery error with authorization error")
        return None
