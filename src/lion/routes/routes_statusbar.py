from time import sleep
from json import dumps as jsons_dumps
from flask import Blueprint, Response, stream_with_context
from lion.status_n_progress_bar.status_bar_manager import STATUS_CONTROLLER
from lion.logger.exception_logger import log_exception

statusbar_bp = Blueprint('statusbar', __name__)

@statusbar_bp.route("/event-stream-listener")
def stream_statusbar():

    try:
        def stream_status_updates():
            try:
                while STATUS_CONTROLLER.POPUP_MESSAGE or STATUS_CONTROLLER.STATUS_VALUE > 0.0 or STATUS_CONTROLLER.PROGRESS_INFO:

                    data = {}

                    data["popup_message"] = str(STATUS_CONTROLLER.POPUP_MESSAGE)
                    data["progress_percentage"] = str(STATUS_CONTROLLER.PROGRESS_PERCENTAGE_STR)
                    data["progress_info"] = str(STATUS_CONTROLLER.PROGRESS_INFO)

                    STATUS_CONTROLLER.POPUP_MESSAGE = ''

                    if data:
                        yield f"data: {jsons_dumps(data)}\n\n"

                    sleep(0.1)

            except Exception:
                log_exception(False)

        return Response(stream_with_context(stream_status_updates()), mimetype="text/event-stream")

    except Exception:
        log_exception(False)
        return {}
    
