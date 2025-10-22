from shutil import rmtree
from pathlib import Path
from lion.logger import exception_logger


def empty_dir(folder: Path | str = '') -> bool:
    """
    Empties the specified directory by deleting it and recreating it.
    Args:
        folder (str): The path to the directory to empty. Defaults to an empty string, which refers to the current directory.
    Returns:
        bool: True if the directory exists and is a directory after the operation, False otherwise.
    Notes:
        - If the directory does not exist, it will be created.
        - Any exceptions during deletion or creation are silently ignored.
    """

    path_to_empty = Path(str(folder))

    if path_to_empty.exists() and path_to_empty.is_dir():
        try:
            rmtree(path_to_empty)
        except Exception:
            pass

    try:
        path_to_empty.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    status = path_to_empty.exists() and path_to_empty.is_dir() and not path_to_empty.iterdir()

    if not status:
        exception_logger.log_exception(
            f"Validating emptying {path_to_empty} directory failed!\n" + \
            f"Folder exists: {path_to_empty.exists() }. \n" + \
            f"Folder is a directory: {path_to_empty.is_dir() }. \n" + \
            f"Folder is empty: {not path_to_empty.iterdir() }. \n" + \
            "Please check permissions or if the path is correct."
        )

    return status