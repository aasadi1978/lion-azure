import logging
from lion.logger.log_entry import LogEntry


def write_log_entry(message=''):
    try:
        LogEntry.log_entry(message=message)
    except Exception as e:
        logging.error(f"Error writing log entry: {e}")
