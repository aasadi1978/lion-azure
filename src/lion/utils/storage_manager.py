import logging
from os import getenv
from pathlib import Path
from typing import Optional
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError
from functools import lru_cache

from lion.bootstrap.constants import LION_STRG_CONTAINER_LOGS, LION_STRG_CONTAINER_UPLOADS
from lion.config.paths import LION_PROJECT_HOME, PREFIX_MAP
from lion.logger.exception_logger import log_exception
from lion.utils.session_manager import SESSION_MANAGER

class LionStorageManager:

    def __init__(self, local_root: Optional[Path] = None):

        self.local_root = local_root or LION_PROJECT_HOME
        self._group_name = SESSION_MANAGER.get('group_name')

        conn_str = getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.in_azure = conn_str is not None

        if self.in_azure:
            self.blob_service = BlobServiceClient.from_connection_string(conn_str)
    
    def create_container(self, container_name):
        try:
            self.blob_service.create_container(container_name)
        except Exception:
            pass  # Container already exists

    def get_container_client(self, container_name: str):
        if not self.in_azure:
            raise RuntimeError("Azure connection string not set. Running in local mode.")

        self._group_name = self._group_name or SESSION_MANAGER.get('group_name')
        container_client = self.blob_service.get_container_client(container_name)

        # Ensure container exists (idempotent)
        try:
            container_client.get_container_properties()
        except ResourceNotFoundError:
            self.create_container(container_name)
            log_exception()
        except Exception:
            self.create_container(container_name)
            log_exception()

        return container_client

    def upload_file(
            self, 
            local_path: str | Path, 
            container_name: str, 
            *blob_parts: str,
            blob_name: Optional[str] = None):
        """
        Uploads file to the storage container
        """

        try:
            if not blob_name and not blob_parts:
                raise ValueError("Provide either 'blob_name' or path parts via '*blob_parts'")

            prefix = str(PREFIX_MAP.get(Path(local_path), f"{self._group_name}")).replace(' ', '')
            blob_name = blob_name or f"{prefix}/" + "/".join(blob_parts)

            if self.in_azure:
                container_name = container_name or LION_STRG_CONTAINER_LOGS
                container_client = self.get_container_client(container_name)
                with open(local_path, "rb") as f:
                    container_client.upload_blob(blob_name, f, overwrite=True)
                logging.info(f"Uploaded {local_path} → Azure blob {container_name}/{blob_name}")
            else:
                dest_path = self.local_root / container_name / Path(*blob_parts)
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                Path(local_path).replace(dest_path)
                logging.info(f"Copied {local_path} → Local {dest_path}")
        
        except Exception:
            log_exception('Uploading failed!')

    def download_file(
        self,
        container_name: str,
        *blob_parts: str,
        local_path: str | Path,
        blob_name: Optional[str] = None,
    ):
        """
        Downloads a blob from Azure Storage or a local container.

        You can specify either:
        • blob_parts → pieces of the blob path, e.g. ("group", "logs", "file.log")
        • blob_name  → full blob path string (overrides blob_parts)

        Example:
            download_file("logs", "group1", "file.log", local_path="output.log")
            download_file("logs", local_path="output.log", blob_name="group1/file.log")
        """

        try:
            if not blob_name and not blob_parts:
                raise ValueError("Provide either 'blob_name' or path parts via '*blob_parts'")

            prefix = f"{self._group_name}/"
            blob_name = blob_name or f"{prefix}" + "/".join(blob_parts)

            if self.in_azure:
                container_name = container_name or LION_STRG_CONTAINER_UPLOADS
                container_client = self.get_container_client(container_name)

                with open(local_path, "wb") as f:
                    data = container_client.download_blob(blob_name).readall()
                    f.write(data)

                logging.info(f"Downloaded Azure blob {container_name}/{blob_name} → {local_path}")
            else:
                src_path = self.local_root / container_name / Path(*blob_parts)
                Path(src_path).replace(local_path)
                logging.info(f"Copied Local {src_path} → {local_path}")

        except Exception:
            log_exception('Downloading failed!')


    def list_files(self, container_name: str, prefix: str = ""):

        prefix = f"{self._group_name}/" + prefix
        if self.in_azure:
            container_client = self.get_container_client(container_name)
            return [b.name for b in container_client.list_blobs(name_starts_with=prefix)]
        else:
            local_dir = self.local_root / container_name / prefix
            return [str(p.relative_to(self.local_root / container_name)) for p in local_dir.rglob("*") if p.is_file()]


@lru_cache(maxsize=1)
def get_storage_manager(local_root: Optional[Path] = None) -> LionStorageManager:
    return LionStorageManager(local_root=local_root)

STORAGE_MANAGER = get_storage_manager()