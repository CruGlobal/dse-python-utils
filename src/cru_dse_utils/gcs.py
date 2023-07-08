from typing import List, Dict, Any, Optional, Union
import logging
import io
from google.cloud import storage
from cru_dse_utils import get_google_credentials
import pandas as pd


def upload_to_gcs(
    file_path: str, bucket_name: str, blob_name: str, secret_name: str
) -> None:
    """
    Uploads the specified file to a Google Cloud Storage bucket.

    This function uploads a file to the specified Google Cloud Storage bucket
    with the specified name. The function logs a message indicating whether
    the upload succeeded or failed.

    Args:
        file_path: str: The path to the file to be uploaded.
        bucket_name (str): The name of the Google Cloud Storage bucket to
        upload the file to.
        blob_name (str): The name of the file to create in the bucket.
        secret_name (str): The name of the environment variable to retrieve
        the Google Cloud credentials.

    Returns:
        None
    """
    logger = logging.getLogger("primary_logger")
    credentials = get_google_credentials(secret_name)
    if credentials is None:
        logger.error(f"Failed to get Google Cloud credentials with {secret_name}")
        return None
    client = storage.Client(credentials=credentials)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    try:
        blob.upload_from_filename(file_path)
        logger.info(
            f"Uploaded file to Google Cloud Storage: gs://{bucket_name}/{blob_name}"
        )
    except Exception as e:
        logger.exception(f"Upload to Google Cloud Storage error: {str(e)}")


def download_from_gcs_as_dataframe(
    bucket_name, blob_name, secret_name: str
) -> Union[pd.DataFrame, None]:
    """
    Downloads a file from a Google Cloud Storage bucket.

    This function downloads a file from the specified Google Cloud Storage
    bucket with the specified name. The function logs a message indicating
    whether the download succeeded or failed.

    Args:
        bucket_name (str): The name of the Google Cloud Storage bucket to
        download the file from.
        blob_name (str): The name of the file to download from the bucket.
        secret_name (str): The name of the environment variable to retrieve
        the Google Cloud credentials.

    Returns:
        pd.DataFrame: The contents of the file as a pandas DataFrame.
        None: If the download failed.
    """
    logger = logging.getLogger("primary_logger")
    credentials = get_google_credentials(secret_name)
    if credentials is None:
        logger.error(f"Failed to get Google Cloud credentials with {secret_name}")
        return None
    client = storage.Client(credentials=credentials)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    try:
        contents = blob.download_as_string()
        df = pd.read_csv(io.BytesIO(contents))
        logger.info(f"Downloaded data from gs://{bucket_name}/{blob_name}")
        return df
    except Exception as e:
        logger.exception(f"Download from Google Cloud Storage error: {str(e)}")


def upload_dataframe_to_gcs(
    bucket_name: str, blob_name: str, df: pd.DataFrame, secret_name: str
) -> None:
    """
    Uploads a pandas DataFrame to a Google Cloud Storage bucket.

    This function uploads a pandas DataFrame to the specified Google Cloud
    Storage bucket. The function logs a message indicating whether the upload
    succeeded or failed.

    Args:
        bucket_name (str): The name of the Google Cloud Storage bucket to
        upload the file to.
        blob_name (str): The name of the file to create in the bucket.
        df (pd.DataFrame): The pandas DataFrame to upload.
        secret_name (str): The name of the environment variable to retrieve
        the Google Cloud credentials.

    Returns:
        None
    """
    logger = logging.getLogger("primary_logger")
    credentials = get_google_credentials(secret_name)
    if credentials is None:
        logger.error(f"Failed to get Google Cloud credentials with {secret_name}")
        return None
    client = storage.Client(credentials=credentials)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    try:
        blob.upload_from_string(df.to_csv(index=False), "text/csv")
        logger.info(f"Uploaded data to gs://{bucket_name}/{blob_name}")
    except Exception as e:
        logger.exception(f"Upload to Google Cloud Storage error: {str(e)}")
