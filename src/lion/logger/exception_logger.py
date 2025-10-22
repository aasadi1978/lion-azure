import logging
from linecache import checkcache, getline
from os import path as os_path
from sys import exc_info

from lion.logger.logging_levels import LOGGING_SEVERITY_LEVELS

def log_exception(message=None, **kwargs):

    remarks = kwargs.get('remarks', 'ERROR:')
    level = str(kwargs.get('level', 'error')).lower()

    if message is not None:
        remarks = f'{remarks} {message}'

    try:
        exc_type, exc_obj, tb = exc_info()

        if tb is None:
            return 'sys.exc_info() returned None, no traceback available'
        
        f = tb.tb_frame
        lineno = tb.tb_lineno
        filename = f.f_code.co_filename
        checkcache(filename)
        line = getline(filename, lineno, f.f_globals)

        # str_now = dt_datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f'{remarks}: ({os_path.basename(filename)}, LINE {lineno} "{line.strip()}")(|): {exc_obj}'

        handle_logging(level, message)

        if kwargs.get('popup', False):
            show_exception_popup(message)

        return message.split('(|):')[1]

    except Exception as err:
        logging.error(f'Error in log_exception: {str(err)}')
        return str(err)

def handle_logging(*logs):
    try:
        level, message = logs
        message = str(message).strip()
        if len(message) == 0:
            return
        
        LOGGING_SEVERITY_LEVELS.get(level, logging.error)(f'{message}')
    except Exception as err:
        logging.error(f'Error in handle_logging: {str(err)}')

def show_exception_popup(message=None, **kwargs):
    from lion.utils.popup_notifier import show_error
    """A simple wrapper around log_exception to show a popup"""
    
    show_error(message if message else log_exception(**kwargs))

def return_exception_code(message=None, **kwargs):
    """The same as log_exception but returns {'code': 400, 'error': message}"""
    msg = log_exception(message=message, **kwargs)
    return {'code': 400, 'error':msg, 'message': msg}
