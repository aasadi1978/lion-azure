from lion.logger.exception_logger import log_exception


from json import dump as json_dump
from os import makedirs, path as os_path


def tojsonfile(dct, filename, Path=None):

    if dct == {}:
        log_exception(popup=False, remarks=('dict is empty!'))
        return

    try:
        if Path is None:
            raise ValueError('Please specify a path!')

        makedirs(Path, exist_ok=True)

        if filename.lower()[-5:] != '.json':
            filename = filename + '.json'

        with open(os_path.join(Path, filename), 'w') as fp:
            json_dump(dct, fp, indent=4)

    except Exception:
        log_exception(popup=True, remarks='Exporting as json failed!')