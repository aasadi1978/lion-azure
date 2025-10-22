
import inspect
import logging
from os import getenv
from lion.logger.logging_levels import LOGGING_SEVERITY_LEVELS
from lion.utils.split_string import split_string
from lion.utils.print2console import display_in_console

def log_message(message,
               module_name='',
               **kwargs):

    log_enabled = getenv('LOGGING_ENABLED', 'False') == 'True'
    if not log_enabled:
        return

    module_name = kwargs.get('module_name', module_name)
    if len(message) > 250:
        message_lines = split_string(txt=message, max_length=250)
        message = "\n".join(message_lines)

    if module_name == '':

        try:
            # Get the current frame from the caller
            frame = inspect.currentframe()
            # Step back to the caller's frame
            caller_frame = frame.f_back
            # Get code information about the frame
            code = caller_frame.f_code

            # Get the module name
            module_name = inspect.getmodule(caller_frame).__name__

            # Get function or method name
            function_name = code.co_name

            # Format the information
            module_name = f"{module_name}.py/{function_name}()"

        except Exception:
            module_name = ''

    # message = f"{str(datetime.now())[:19]} - {module_name}: {message}\n"
    message = f"{module_name}: {message}"

    try:
        display_in_console(message)
        LOGGING_SEVERITY_LEVELS.get('info', logging.INFO)(message)

    except Exception as err:
        logging.error(f"{message}. {str(err)}")
