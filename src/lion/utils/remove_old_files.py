from lion.utils.clean_can_be_executed import clean_can_be_executed
from lion.utils.file_age_in_days import file_age_in_days
from lion.utils.remove_element import remove_element


from collections import defaultdict
from os import listdir, path as os_path
from shutil import rmtree


def remove_old_files(mydir='', days=7, patern='', exclude=[]):

    files_removed = False
    if clean_can_be_executed(mydir=mydir, days=days):

        try:

            __dct_ts = defaultdict()
            __files = [os_path.basename(f) for f in listdir(mydir)]

            if patern != '':
                __files = [f for f in __files if patern.lower()
                           in f.lower()]

            if exclude:
                for f in exclude:
                    __files = remove_element(
                        mylist=__files, elem=f)

            for filename in __files:
                __dct_ts[filename] = file_age_in_days(
                    os_path.join(mydir, filename))

            for filename in __files:
                if __dct_ts[filename] > days:
                    rmtree(os_path.join(mydir, filename))
                    files_removed = True

        except Exception:
            pass

    return files_removed