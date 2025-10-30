from os import listdir
from pathlib import Path
import threading
from lion.config.paths import LION_LOGS_PATH, LION_LOG_FILE_PATH
from lion.logger.exception_logger import log_exception
from lion.utils.storage_manager import STORAGE_MANAGER


def upload_logs_to_blob(src_path: Path, container_name: str, *blob_parts: str):
    """
    Upload all log files from the local_log_dir to the specified blob storage under the blob_prefix.
    """
    try:

        if src_path is None:
            src_path = LION_LOGS_PATH

        errmsg = ''

        list_logs = listdir(src_path)
        for log_file in list_logs:
            try:
                args = [*blob_parts, log_file]
                STORAGE_MANAGER.upload_file(local_path=src_path / log_file, container_name=container_name, *args)
            except Exception as e:
                errmsg = f"{errmsg}{log_exception(remarks=f"Failed to upload log file {log_file} to Blob Storage: {str(e)}")}. "

        STORAGE_MANAGER.upload_file(local_path=LION_LOG_FILE_PATH, *blob_parts, blob_name=LION_LOG_FILE_PATH.name)

        if errmsg:
            raise Exception(errmsg)

    except Exception:
        return {"message": log_exception(), 'code': 400}
    
    return {"status": "success", "message": "Logs uploaded to Blob Storage", 'code': 200}

def trigger_async_log_upload(src_path: Path, container_name: str, *blob_parts: str):

    t = threading.Thread(
        target=upload_logs_to_blob,
        args=(src_path, container_name, *blob_parts),
    )
    t.daemon = True
    t.start()