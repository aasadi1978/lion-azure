from lion.logger.exception_logger import log_exception


from os import path as os_path
from pickle import dump as pickle_dump
from shutil import rmtree


def dump_obj(obj, str_DestFileName, path=None):

    try:
        if path is None:
            raise ValueError('Please specify a path!')

        if path == '':

            with open(str_DestFileName, 'wb') as f:
                pickle_dump(obj, f)
            return 1

    except Exception:
        log_exception(popup=False,
                       remarks=f'Dumping {str_DestFileName} was not successful!')
        return 0

    if not os_path.exists(path):
        rmtree(path)

    try:
        with open(os_path.join(path, str_DestFileName), 'wb') as f:
            pickle_dump(obj, f)
        return 1

    except Exception as err:
        log_exception(popup=False,
                       remarks=f'Dumping {str_DestFileName} was not successful!')

        return 0