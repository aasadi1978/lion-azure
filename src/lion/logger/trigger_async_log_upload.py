from pathlib import Path
import threading
from lion.config.paths import LION_LOGS_PATH
from lion.logger.exception_logger import log_exception
from lion.utils.storage_manager import STORAGE_MANAGER


def upload_logs_to_blob(src_path: Path, *blob_parts: str):
    """
    Recursively upload all files under src_path to the specified blob storage container,
    preserving relative paths under the given blob_parts prefix.
    """
    try:
        if src_path is None:
            src_path = LION_LOGS_PATH

        errmsg = ''

        for file_path in src_path.rglob("*"):
            if file_path.is_file():
                try:
                    # Preserve folder structure relative to src_path
                    relative_parts = file_path.relative_to(src_path).parts
                    blob_path_parts = [*blob_parts, *relative_parts]
                    STORAGE_MANAGER.upload_file(file_path, *blob_path_parts)
                except Exception as e:
                    errmsg += f"{log_exception(remarks=f'Failed to upload {file_path} to Blob Storage: {str(e)}')}. "

        if errmsg:
            raise Exception(errmsg)

    except Exception:
        return {"message": log_exception(), 'code': 400}
    
    return {"status": "success", "message": "Logs uploaded to Blob Storage", 'code': 200}

def trigger_async_log_upload(src_path: str | Path, *blob_parts: str):

    t = threading.Thread(
        target=upload_logs_to_blob,
        args=(src_path, *blob_parts),
    )
    t.daemon = True
    t.start()