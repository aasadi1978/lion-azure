from pprint import pprint
from random import sample


def ppt(obj, pause=True):

    pprint(obj)
    print('-'*100)

    if pause:
        __t = input('Press ENTER to continue ...')
        del __t


def print_top_dict(dct, n_records=1, pause=True):
    print_dict_top(dct=dct, n_records=n_records, pause=pause)


def print_dict_top(dct, n_records=1, pause=True):

    if len(dct) == 0:
        return {}

    kys = set(sample(list(dct.keys()), n_records))

    ppt(obj={x: v for x, v in dct.items() if x in kys}, pause=pause)

    print('-'*100)

    if pause:
        aa = input('Press ENTER to continue ...')
        del aa
