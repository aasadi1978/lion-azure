from pprint import pprint
from pandas import DataFrame
from lion.logger.prettyprnt import print_dict_top


def display_in_console(obj, n_records=0, pause=False):

    if isinstance(obj, DataFrame):

        pprint(obj.head(20))
        print('#' * 100)
        return

    elif isinstance(obj, dict):

        if not n_records:
            n_records = len(obj)

        print_dict_top(dct=obj, n_records=n_records, pause=pause)
        return

    else:
        print(obj)

    if pause:
        input('Press ENTER to proceed')
