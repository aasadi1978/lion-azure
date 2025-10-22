from pandas import DataFrame, concat as pd_concat
from lion.logger.exception_logger import log_exception


def concat(df_list=[], ignore_index=False, axis=0, log_err=False):

    if df_list:

        try:
            if ignore_index:
                return pd_concat(df_list, ignore_index=ignore_index, axis=axis)

            _df = pd_concat(df_list)

        except Exception:
            if log_err:
                log_exception(popup=False, remarks='direct concat failed!')

            _df = DataFrame()

        return _df