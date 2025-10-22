from os import listdir, path as os_path


def sort_dir_tm(dir='', endswith='', pattern='', return_basename=False):
    """
    Sorts contents of a folder in descending order to push the latest files to
    the top of the list
    """
    __lsfiles = listdir(dir)

    if endswith != '':
        __lsfiles = [
            f for f in __lsfiles if f.lower().endswith(endswith.lower())]

    if pattern != '':
        __lsfiles = [os_path.basename(
            f) for f in __lsfiles if pattern.lower() in f.lower()]

    __lsfiles = [os_path.join(dir, f) for f in __lsfiles]

    __lsfiles = sorted(__lsfiles, key=os_path.getmtime, reverse=True)

    if return_basename:
        __lsfiles = [os_path.basename(f) for f in __lsfiles]

    return __lsfiles