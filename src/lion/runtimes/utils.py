from pandas import concat, isna, isnull

def get_number_of_drivers(dur):

    try:
        if dur <= 540:
            return 1
        else:
            return 2
    except TypeError:
        return 0

    except Exception:
        return dur


def get_break_time(dur, is_double_man=False):

    try:

        if is_double_man:
            return 0

        if not dur:
            return 0

        if dur <= 270:
            return 0

        elif dur <= 540:
            return 60

        return 15

    except TypeError:
        return None

    except Exception:
        return None



def is_null_or_zero(x):

    if isnull(x) or isna(x) or str(x).lower() == 'nan' or str(x).lower() == 'null' or str(x).lower() == 'n/a' or str(
            x).strip() == '' or (x is None):
        return True

    if not x:
        return True

    return False
