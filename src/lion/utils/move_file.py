from os import mkdir, path as os_path, remove
from shutil import copyfile


def move_file(file_full_path, dest_folder=None):

    try:
        mkdir(dest_folder)
    except Exception as err:
        del err

    fname = os_path.basename(file_full_path)
    dst = os_path.join(dest_folder, fname)
    copyfile(file_full_path, dst)

    if os_path.isfile(dst):
        remove(file_full_path)