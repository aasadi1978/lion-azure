import logging
from os import getenv
from pathlib import Path
import re
import shutil
from typing import Optional
from azure.storage.blob import BlobServiceClient, ContainerClient
from azure.core.exceptions import ResourceNotFoundError
from functools import lru_cache
from werkzeug.datastructures import FileStorage
from typing import Union

from lion.config.paths import LION_PROJECT_HOME, RECOMMENDED_BLOB_CONTAINER
from lion.logger.exception_logger import log_exception
from lion.utils.session_manager import SESSION_MANAGER

class LionStorageManager:

    def __init__(self, local_root: Optional[Path] = None):

        self.local_root = local_root or LION_PROJECT_HOME
        self._group_name = SESSION_MANAGER.get('group_name')
        self._user_id = SESSION_MANAGER.get('user_id')

        conn_str = getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.in_azure = conn_str is not None

        if self.in_azure:
            self.blob_service = BlobServiceClient.from_connection_string(conn_str)
        else:
            self.blob_service = None

    def _validate_storage_container_client(
            self, container_name: str = None) -> Union[None, ContainerClient]:
        """ Validates and adjusts the container name to meet Azure naming rules. 
         If the container name is not provided, it uses the group name from the session manager.
        """

        try:

            if not self.in_azure:
                return None
            
            container_name = container_name or self._group_name or SESSION_MANAGER.get('group_name')
            self._validated_root_container_name = re.sub(r'[^a-z0-9-]', '', container_name.lower())

            if len(self._validated_root_container_name) < 3:
                self._validated_root_container_name = (self._validated_root_container_name + 'container')[:3]
            elif len(self._validated_root_container_name) > 63:
                self._validated_root_container_name = self._validated_root_container_name[:63]

            self._configure_storage_container()
            return self.blob_service.get_container_client(self._validated_root_container_name)

        except Exception:
            log_exception("Could not validate container name!")
            return None

    def _configure_storage_container(self):
        try:
            # Check if container already exists
            container_client = self.blob_service.get_container_client(self._validated_root_container_name)
            container_client.get_container_properties()
            logging.debug(f"Container '{self._validated_root_container_name}' already exists.")
        except ResourceNotFoundError:
            # Create only if missing
            self.blob_service.create_container(self._validated_root_container_name)
            logging.info(f"Created container: {self._validated_root_container_name}")
        except Exception:
            log_exception(f"Could not verify or create container: {self._validated_root_container_name}")


    def upload_file(
            self, 
            local_path: Union[str, Path, FileStorage], 
            *blob_parts: str,
            blob_name: Optional[str] = None) -> bool:
        """
        Uploads file to the storage container
        """

        try:
            if not blob_name and not blob_parts:
                raise ValueError("Provide either 'blob_name' or path parts via '*blob_parts'")

            is_shared = False
            for pth, prfx in RECOMMENDED_BLOB_CONTAINER.items():
                if isinstance(local_path, (str, Path)) and str(local_path).lower().startswith(str(pth).lower()):
                    prefix = local_path.replace(str(pth), str(prfx)).strip("/").replace(' ', '')
                    blob_parts = (prefix, *blob_parts)
                    is_shared = True
                    break

            # Determine prefix for blob path
            if not is_shared:
                prefix = str(f"{self._user_id}").replace(' ', '')

            blob_path_parts = [prefix, *blob_parts]
            if blob_name:
                blob_path_parts.append(blob_name)

            blob_name = "/".join(part.strip("/") for part in blob_path_parts if part)

            if self.in_azure:

                container_client = self._validate_storage_container_client()

                if isinstance(local_path, FileStorage):
                    local_path.stream.seek(0)
                    container_client.upload_blob(blob_name, local_path.stream, overwrite=True)
                else:
                    with open(local_path, "rb") as f:
                        container_client.upload_blob(blob_name, f, overwrite=True)

                logging.info(f"Uploaded {local_path} → Azure blob {self._validated_root_container_name}/{blob_name}")
            else:

                dest_path = self.local_root / Path(*blob_parts)
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                if isinstance(local_path, FileStorage):
                    local_path.save(dest_path)
                else:
                    shutil.copy2(local_path, dest_path)

                logging.info(f"Copied {getattr(local_path, 'filename', local_path)} → Local {dest_path}")

            
            return True
        
        except Exception:
            log_exception(f'Uploading failed for {local_path}!')

        return False

    def download_file(
        self,
        *blob_parts: str,
        local_path: str | Path,
        blob_name: Optional[str] = None,
    ) -> bool:
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
                container_client = self._validate_storage_container_client()

                with open(local_path, "wb") as f:
                    data = container_client.download_blob(blob_name).readall()
                    f.write(data)

                logging.info(f"Downloaded Azure blob {self._validated_root_container_name}/{blob_name} → {local_path}")
            else:
                src_path = self.local_root / Path(*blob_parts)
                Path(src_path).replace(local_path)
                logging.info(f"Copied Local {src_path} → {local_path}")
            
            return True

        except Exception:
            log_exception('Downloading failed!')

        return False


    def list_files(self, prefix: str = ""):
        if self.in_azure:
            container_client = self._validate_storage_container_client()
            prefix = prefix.strip("/")
            return [b.name for b in container_client.list_blobs(name_starts_with=prefix)]
        else:
            local_dir = (self.local_root / prefix).resolve()
            return [str(p.relative_to(self.local_root)) for p in local_dir.rglob("*") if p.is_file()]



@lru_cache(maxsize=1)
def get_storage_manager(local_root: Optional[Path] = None) -> LionStorageManager:
    return LionStorageManager(local_root=local_root)

STORAGE_MANAGER = get_storage_manager()