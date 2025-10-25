
import logging
from os import getenv
from pathlib import Path
from typing import Optional
from azure.storage.blob import BlobServiceClient

from lion.config.paths import LION_PROJECT_HOME

class LionStorageManager:

    def __init__(
        self,
        local_root: Optional[Path] = None,
        container_name: str  = 'logs'
    ):
        self.local_root = local_root or LION_PROJECT_HOME

        conn_str = getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.in_azure = conn_str is not None

        if self.in_azure:
            self.blob_service = BlobServiceClient.from_connection_string(conn_str)
            self.container_client = self.blob_service.get_container_client(container_name)
            try:
                self.container_client.create_container()
            except Exception:
                pass  # container already exists

    def upload_file(self, local_path: str | Path, *blob_parts: str):

        """Uploads a local file to Azure Blob or copies locally."""
        if not blob_parts:
            raise ValueError("Please provide a blob path (folder/subfolder/filename)")
        blob_name = "/".join(blob_parts)

        if self.in_azure:
            with open(local_path, "rb") as f:
                self.container_client.upload_blob(blob_name, f, overwrite=True)
            logging.info(f"Uploaded {local_path} → Azure blob {blob_name}")
        else:
            dest_path = self.local_root.joinpath(*blob_parts)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            Path(local_path).replace(dest_path)
            logging.info(f"Copied {local_path} → Local {dest_path}")

    def download_file(self, *blob_parts: str, local_path: str | Path):
        """Downloads from Azure Blob or copies locally."""
        blob_name = "/".join(blob_parts)

        if self.in_azure:
            with open(local_path, "wb") as f:
                data = self.container_client.download_blob(blob_name).readall()
                f.write(data)
            logging.info(f"Downloaded Azure blob {blob_name} → {local_path}")
        else:
            src_path = self.local_root.joinpath(*blob_parts)
            Path(src_path).replace(local_path)
            logging.info(f"Copied Local {src_path} → {local_path}")

    def list_files(self, prefix: str = ""):
        """List files in Azure Blob or locally."""
        if self.in_azure:
            return [b.name for b in self.container_client.list_blobs(name_starts_with=prefix)]
        else:
            local_dir = self.local_root / prefix
            return [str(p.relative_to(self.local_root)) for p in local_dir.rglob("*") if p.is_file()]
