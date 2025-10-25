
from datetime import datetime, timezone
from lion.logger.exception_logger import log_exception

def utcnow(format_str: str = '%Y-%m-%d %H:%M:%S', local: bool = False) -> str | datetime:
    time_now = datetime.now(timezone.utc) if not local else datetime.now()

    try:
        if not format_str:
            return time_now

        return time_now.strftime(format_str)
    except Exception:
        log_exception(remarks="Failed to get UTC now. Returning local now instead.", popup=False)
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')