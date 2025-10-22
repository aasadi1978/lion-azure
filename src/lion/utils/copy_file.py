from lion.logger.exception_logger import log_exception


from os import makedirs, path as os_path
from shutil import copyfile


def copy_file(file_full_path, dest_folder=None, new_name=''):

    try:
        makedirs(dest_folder, exist_ok=True)
        fname = new_name if new_name != '' else os_path.basename(
            file_full_path)
        dst = os_path.join(dest_folder, fname)

        copyfile(file_full_path, dst)

    except Exception:
        log_exception(popup=False)
        return False

    return True