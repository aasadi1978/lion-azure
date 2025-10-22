from lion.logger.exception_logger import log_exception
from lion.utils.getmtime import getmtime
from pathlib import Path as pathlib_Path
from os import path as os_path


def get_file_ts(filename, Path=None):

    try:
        if Path is None:
            if pathlib_Path(filename).exists():
                return getmtime(pathlib_Path(filename))
            else:
                return None

        filename = os_path.basename(filename)
        filepth = pathlib_Path(pathlib_Path(Path) / filename)

        if not filepth.exists():
            raise FileNotFoundError(f"File {filepth} does not exist.")

        return getmtime(filepth)

    except Exception:
        log_exception(popup=False, message=f"Failed to get file timestamp for {filename} in {Path}!")
        return None