import logging
from lion.config.paths import LION_JS_PATH
from os import path, walk

try:
    LATEST_JS_MODIFICATION_TIME = str(max(path.getmtime(path.join(root_path, f))
                    for root_path, dirs, files in walk(LION_JS_PATH)
                    for f in files))
except Exception as e:
    logging.error(f'Error obtaining latest JS modification time: {str(e)}\n')

    LATEST_JS_MODIFICATION_TIME = '0.0.0'