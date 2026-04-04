import mimetypes
import os
from pathlib import Path

from azure.storage.blob import BlobServiceClient, ContentSettings
from dotenv import load_dotenv

load_dotenv()


def get_blob_service_client() -> BlobServiceClient:
    account_name = os.environ["AZURE_STORAGE_ACCOUNT_NAME"]
    account_key = os.environ["AZURE_STORAGE_ACCOUNT_KEY"]

    account_url = f"https://{account_name}.blob.core.windows.net"
    return BlobServiceClient(account_url=account_url, credential=account_key)


def upload_file_to_blob(file_path: Path) -> dict:
    container_name = os.environ["AZURE_STORAGE_CONTAINER_NAME"]

    blob_service_client = get_blob_service_client()
    blob_name = file_path.name

    blob_client = blob_service_client.get_blob_client(
        container=container_name,
        blob=blob_name,
    )

    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"

    with file_path.open("rb") as data:
        blob_client.upload_blob(
            data,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type),
        )

    return {
        "blob_name": blob_name,
        "container_name": container_name,
    }


def download_blob_bytes(blob_name: str) -> tuple[bytes, str]:
    container_name = os.environ["AZURE_STORAGE_CONTAINER_NAME"]

    blob_service_client = get_blob_service_client()
    blob_client = blob_service_client.get_blob_client(
        container=container_name,
        blob=blob_name,
    )

    download_stream = blob_client.download_blob()
    blob_data = download_stream.readall()

    content_type = (
        download_stream.properties.content_settings.content_type
        or "application/octet-stream"
    )

    return blob_data, content_type