from flask import Blueprint, jsonify
from lion.bootstrap.constants import LION_STRG_CONTAINER_DRIVER_REPORT, LION_STRG_CONTAINER_LOGS, LION_STRG_CONTAINER_OPTIMIZATION
from lion.config.paths import LION_LOCAL_DRIVER_REPORT_PATH, LION_LOGS_PATH, LION_OPTIMIZATION_PATH
from lion.logger.exception_logger import log_exception
from lion.logger.trigger_async_log_upload import trigger_async_log_upload
from lion.utils.flask_request_manager import retrieve_form_data

bp_copy_logs = Blueprint('logger_upload_logs', __name__)

@bp_copy_logs.route("/push-logs", methods=["POST", "GET"])
def push_logs():
    trigger_async_log_upload(src_path=LION_LOGS_PATH, container_name=LION_STRG_CONTAINER_LOGS)
    return jsonify({"status": "started", "message": "Uploading logs in background"})


@bp_copy_logs.route("/push-optimization-logs", methods=["POST", "GET"])
def push_optimization_logs():
    trigger_async_log_upload(src_path=LION_OPTIMIZATION_PATH, container_name=LION_STRG_CONTAINER_OPTIMIZATION)
    return jsonify({"status": "started", "message": "Uploading logs in background"})

@bp_copy_logs.route("/push-driver-reports", methods=["POST", "GET"])
def push_driver_reports():

    try:
        dct_params = retrieve_form_data()

        if loc_code := dct_params.get('loc_code', ''):
            src_path = LION_LOCAL_DRIVER_REPORT_PATH / loc_code
            args = [f"{loc_code}/"]
        else:
            src_path = LION_LOCAL_DRIVER_REPORT_PATH
            args = []

        trigger_async_log_upload(src_path=src_path, container_name=LION_STRG_CONTAINER_DRIVER_REPORT, *args)

    except Exception:
        return jsonify({"status": "error", "message": log_exception()})

    return jsonify({"status": "started", "message": "Uploading logs in background"})
