from unittest.mock import Mock, MagicMock, patch
import pytest
import pandas as pd
from cru_dse_utils import (
    upload_to_gcs,
    download_from_gcs_as_dataframe,
    upload_dataframe_to_gcs,
)


# Fixture to set up variables for testing.
@pytest.fixture
def setup_variables():
    file_path = "/path/to/file"
    bucket_name = "my-bucket"
    blob_name = "my-blob"
    secret_name = "MY_SECRET"
    return file_path, bucket_name, blob_name, secret_name


# Test upload_to_gcs for a successful request where everything works as expected.
@patch("cru_dse_utils.gcs.get_google_credentials")
@patch("cru_dse_utils.gcs.storage.Client")
@patch("cru_dse_utils.gcs.logging")
def test_upload_to_gcs(
    mock_logging, mock_client, mock_get_credentials, setup_variables
):
    # Arrange
    file_path, bucket_name, blob_name, secret_name = setup_variables
    mock_get_credentials.return_value = "fake_credentials"
    mock_client_instance = mock_client.return_value
    mock_bucket = MagicMock()
    mock_client_instance.bucket.return_value = mock_bucket
    mock_blob = MagicMock()
    mock_bucket.blob.return_value = mock_blob

    # Act
    upload_to_gcs(file_path, bucket_name, blob_name, secret_name)

    # Assert
    mock_get_credentials.assert_called_once_with(secret_name)
    mock_client.assert_called_once_with(credentials="fake_credentials")
    mock_client_instance.bucket.assert_called_once_with(bucket_name)
    mock_bucket.blob.assert_called_once_with(blob_name)
    mock_blob.upload_from_filename.assert_called_once_with(file_path)


# Test upload_to_gcs for an unsuccessful attempt to retrieve the Google Cloud credentials.
@patch("cru_dse_utils.gcs.get_google_credentials")
@patch("cru_dse_utils.gcs.storage.Client")
@patch("cru_dse_utils.gcs.logging")
def test_upload_to_gcs_no_credentials(
    mock_logging, mock_client, mock_get_credentials, setup_variables
):
    # Arrange
    file_path, bucket_name, blob_name, secret_name = setup_variables
    mock_get_credentials.return_value = None

    # Act
    result = upload_to_gcs(file_path, bucket_name, blob_name, secret_name)

    # Assert
    mock_get_credentials.assert_called_once_with(secret_name)
    mock_logging.getLogger.return_value.error.assert_called_once_with(
        f"Failed to get Google Cloud credentials with {secret_name}"
    )
    assert result is None


# Test upload_to_gcs for an unsuccessful attempt to upload the file to Google Cloud Storage.
@patch("cru_dse_utils.gcs.get_google_credentials")
@patch("cru_dse_utils.gcs.storage.Client")
@patch("cru_dse_utils.gcs.logging")
def test_upload_to_gcs_upload_error(
    mock_logging, mock_client, mock_get_credentials, setup_variables
):
    # Arrange
    file_path, bucket_name, blob_name, secret_name = setup_variables
    mock_get_credentials.return_value = "fake_credentials"
    mock_client_instance = mock_client.return_value
    mock_bucket = MagicMock()
    mock_client_instance.bucket.return_value = mock_bucket
    mock_blob = MagicMock()
    mock_blob.upload_from_filename.side_effect = Exception("Upload failed")
    mock_bucket.blob.return_value = mock_blob

    # Act
    result = upload_to_gcs(file_path, bucket_name, blob_name, secret_name)

    # Assert
    mock_get_credentials.assert_called_once_with(secret_name)
    mock_client.assert_called_once_with(credentials="fake_credentials")
    mock_client_instance.bucket.assert_called_once_with(bucket_name)
    mock_bucket.blob.assert_called_once_with(blob_name)
    mock_blob.upload_from_filename.assert_called_once_with(file_path)
    mock_logging.getLogger.return_value.exception.assert_called_once()
    assert result is None


# Test download_from_gcs_as_dataframe for a successful request where everything works as expected.
@patch("cru_dse_utils.gcs.get_google_credentials")
@patch("cru_dse_utils.gcs.storage.Client")
@patch("cru_dse_utils.gcs.logging")
@patch("cru_dse_utils.gcs.pd.read_csv")
@patch("cru_dse_utils.gcs.io.BytesIO")
def test_download_from_gcs_as_dataframe(
    mock_bytes_io,
    mock_read_csv,
    mock_logging,
    mock_client,
    mock_get_credentials,
    setup_variables,
):
    # Arrange
    file_path, bucket_name, blob_name, secret_name = setup_variables
    mock_get_credentials.return_value = "fake_credentials"
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_client_instance = mock_client.return_value
    mock_client_instance.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob
    mock_content = MagicMock()
    mock_blob.download_as_string.return_value = mock_content
    mock_bytes_io.return_value = mock_content
    mock_dataframe = pd.DataFrame()
    mock_read_csv.return_value = mock_dataframe

    # Act
    returned_df = download_from_gcs_as_dataframe(bucket_name, blob_name, secret_name)

    # Assert
    mock_get_credentials.assert_called_once_with(secret_name)
    mock_client.assert_called_once_with(credentials="fake_credentials")
    mock_client_instance.bucket.assert_called_once_with(bucket_name)
    mock_bucket.blob.assert_called_once_with(blob_name)
    mock_blob.download_as_string.assert_called_once()
    mock_bytes_io.assert_called_once_with(mock_content)
    mock_read_csv.assert_called_once_with(mock_content)
    assert isinstance(returned_df, pd.DataFrame)


# Test download_from_gcs_as_dataframe for an unsuccessful attempt to retrieve credentials.
@patch("cru_dse_utils.gcs.get_google_credentials")
@patch("cru_dse_utils.gcs.storage.Client")
@patch("cru_dse_utils.gcs.logging")
def test_download_from_gcs_as_dataframe_no_credentials(
    mock_logging, mock_client, mock_get_credentials, setup_variables
):
    # Arrange
    file_path, bucket_name, blob_name, secret_name = setup_variables
    mock_get_credentials.return_value = None

    # Act
    result = download_from_gcs_as_dataframe(bucket_name, blob_name, secret_name)

    # Assert
    mock_get_credentials.assert_called_once_with(secret_name)
    mock_logging.getLogger.return_value.error.assert_called_once_with(
        f"Failed to get Google Cloud credentials with {secret_name}"
    )
    assert result is None


# Test download_from_gcs_as_dataframe for an unsuccessful attempt to download.
@patch("cru_dse_utils.gcs.get_google_credentials")
@patch("cru_dse_utils.gcs.storage.Client")
@patch("cru_dse_utils.gcs.logging")
def test_download_from_gcs_as_dataframe_download_error(
    mock_logging, mock_client, mock_get_credentials, setup_variables
):
    # Arrange
    file_path, bucket_name, blob_name, secret_name = setup_variables
    mock_get_credentials.return_value = "fake_credentials"
    mock_client_instance = mock_client.return_value
    mock_bucket = MagicMock()
    mock_client_instance.bucket.return_value = mock_bucket
    mock_blob = MagicMock()
    mock_blob.download_as_string.side_effect = Exception("Download failed")
    mock_bucket.blob.return_value = mock_blob

    # Act
    result = download_from_gcs_as_dataframe(bucket_name, blob_name, secret_name)

    # Assert
    mock_get_credentials.assert_called_once_with(secret_name)
    mock_client.assert_called_once_with(credentials="fake_credentials")
    mock_client_instance.bucket.assert_called_once_with(bucket_name)
    mock_bucket.blob.assert_called_once_with(blob_name)
    mock_logging.getLogger.return_value.exception.assert_called_once()
    assert result is None


# Test upload_dataframe_to_gcs for a successful request where everything works as expected.
@patch("cru_dse_utils.gcs.get_google_credentials")
@patch("cru_dse_utils.gcs.storage.Client")
@patch("cru_dse_utils.gcs.logging.getLogger")
def test_upload_dataframe_to_gcs_success(
    mock_get_logger, mock_client, mock_get_credentials, setup_variables
):
    # Arrange
    file_path, bucket_name, blob_name, secret_name = setup_variables
    df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    mock_get_credentials.return_value = "fake_credentials"
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_client_instance = mock_client.return_value
    mock_client_instance.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    # Act
    upload_dataframe_to_gcs(bucket_name, blob_name, df, secret_name)

    # Assert
    mock_get_credentials.assert_called_once_with(secret_name)
    mock_client.assert_called_once_with(credentials="fake_credentials")
    mock_client_instance.bucket.assert_called_once_with(bucket_name)
    mock_bucket.blob.assert_called_once_with(blob_name)
    mock_blob.upload_from_string.assert_called_once_with(
        df.to_csv(index=False), "text/csv"
    )
    mock_logger.info.assert_called_once_with(
        f"Uploaded data to gs://{bucket_name}/{blob_name}"
    )


# Test upload_dataframe_to_gcs for an unsuccessful attempt.
@patch("cru_dse_utils.gcs.get_google_credentials")
@patch("cru_dse_utils.gcs.storage.Client")
@patch("cru_dse_utils.gcs.logging.getLogger")
def test_upload_dataframe_to_gcs_fail(
    mock_get_logger, mock_client, mock_get_credentials, setup_variables
):
    # Arrange
    file_path, bucket_name, blob_name, secret_name = setup_variables
    df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    mock_get_credentials.return_value = "fake_credentials"
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_blob.upload_from_string.side_effect = Exception("fake exception")
    mock_client_instance = mock_client.return_value
    mock_client_instance.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    # Act
    upload_dataframe_to_gcs(bucket_name, blob_name, df, secret_name)

    # Assert
    mock_get_credentials.assert_called_once_with(secret_name)
    mock_client.assert_called_once_with(credentials="fake_credentials")
    mock_client_instance.bucket.assert_called_once_with(bucket_name)
    mock_bucket.blob.assert_called_once_with(blob_name)
    mock_blob.upload_from_string.assert_called_once_with(
        df.to_csv(index=False), "text/csv"
    )
    mock_logger.exception.assert_called_once_with(
        "Upload to Google Cloud Storage error: fake exception"
    )
