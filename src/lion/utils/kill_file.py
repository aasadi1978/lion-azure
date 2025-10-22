from os import path as os_path, remove
from shutil import rmtree


def kill_file(path=""):
    try:
        remove(path)
    except Exception:
        pass

    if os_path.exists(path):
        rmtree(path)

    return int(not os_path.exists(path))