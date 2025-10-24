from os import listdir
from flask import jsonify
from lion.config.paths import LION_LOGS_PATH, LION_LOG_FILE_PATH
from lion.create_flask_app.create_app import LION_FLASK_APP
from lion.logger.exception_logger import log_exception
from lion.utils.storage_manager import LionStorageManager


@LION_FLASK_APP.route("/push-logs", methods=["POST", "GET"])
def push_logs():
    try:
        storage = LionStorageManager(container_name="logs")
        errmsg = ''

        list_logs = listdir(LION_LOGS_PATH)
        for log_file in list_logs:
            try:
                storage.upload_file(local_path=LION_LOGS_PATH / log_file, blob_name=log_file)
            except Exception as e:
                errmsg = f"{errmsg}{log_exception(remarks=f"Failed to upload log file {log_file} to Blob Storage: {str(e)}")}. "
        
        storage.upload_file(local_path=LION_LOG_FILE_PATH, blob_name=LION_LOG_FILE_PATH.name)

        if errmsg:
            raise Exception(errmsg)

    except Exception:
        return jsonify({"message": log_exception(), 'code': 400})
    
    return jsonify({"status": "success", "message": "Logs uploaded to Blob Storage", 'code': 200})
