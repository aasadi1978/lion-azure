from os import path as os_path
from pickle import load as pickle_load


def load_obj(str_FileName, path=None, if_null=None, silent=False):

    try:
        with open(str_FileName, 'rb') as f:
            return pickle_load(f)
    except Exception as err:
        if silent:
            return if_null

    try:

        if path is None:
            raise ValueError('Please specify a path!')

        if not os_path.exists(path):
            return if_null

        with open(os_path.join(path, str_FileName), 'rb') as f:
            return pickle_load(f)
    except Exception:
        if silent:
            return if_null

        return if_null