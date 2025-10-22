from pandas import isna, isnull


def is_null(x, return_val=None):

    if return_val is not None:
        return return_val

    return (isnull(x) or isna(x) or
            str(x).lower() == 'nan' or str(x).lower() == 'null' or str(x).lower() == 'n/a' or str(x).strip() == '' or (x is None))