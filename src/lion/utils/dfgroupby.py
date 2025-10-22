from pandas import DataFrame
from lion.logger.exception_logger import log_exception


def groupby(df, groupby_cols=[],
            agg_cols_dict={},
            rename_cols_dict={}):

    try:
        if groupby_cols == []:
            if agg_cols_dict == {}:
                groupby_cols = df.columns.tolist()
            else:
                groupby_cols = [x for x in df.columns.tolist()
                                if x not in agg_cols_dict.keys()]

        if agg_cols_dict != {}:

            for ky in agg_cols_dict.keys():

                if agg_cols_dict[ky] == 'count':
                    pass
                else:
                    try:
                        df[ky] = df[ky].astype(float)
                    except Exception:
                        log_exception(popup=False)
                        return DataFrame()

            df_grouped = df.groupby(groupby_cols).agg(agg_cols_dict)
            df_grouped = df_grouped.reset_index()

            if rename_cols_dict != {}:

                for ky in rename_cols_dict.keys():
                    df_grouped.rename(columns=({ky: rename_cols_dict[ky]}),
                                      inplace=True)

            return (df_grouped)

        return DataFrame(list(df.groupby(groupby_cols).groups),
                         columns=groupby_cols)

    except Exception:
        log_exception(popup=False)
        return DataFrame()

def df_groupby(df, groupby_cols=[],
            agg_cols_dict={},
            rename_cols_dict={}):
    
    return groupby(df, groupby_cols, agg_cols_dict, rename_cols_dict)
