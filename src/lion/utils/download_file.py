from pathlib import Path
import pandas as pd
from lion.config.paths import TEMP_APP_DATA_FOLDER
from lion.logger.exception_logger import log_exception
from lion.utils.storage_manager import STORAGE_MANAGER


def download_file(filename: str) -> Path:
    """
    Downloads a file from Azure Blob Storage to a local path.
    """
    try:
        dest_file_path = TEMP_APP_DATA_FOLDER / filename
        if STORAGE_MANAGER.download_file(container_name="uploads", blob_name=filename, local_path=dest_file_path):

            # Load into a DataFrame
            if dest_file_path.exists():
                df = pd.read_csv(dest_file_path)

                return dest_file_path
        return None
    except Exception as e:
        log_exception(f"File download failed: {str(e)}")
