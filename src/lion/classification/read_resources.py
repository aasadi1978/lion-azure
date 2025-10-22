from lion.utils.is_file_updated import is_file_updated
from lion.logger.exception_logger import log_exception
from pandas import read_excel
from os import path as os_path
from lion.utils.dfgroupby import groupby as df_groupby
from lion.utils.load_obj import load_obj
from lion.config.paths import LION_OPTIMIZATION_PATH
from lion.orm.pickle_dumps import PickleDumps


def load_data(force_reload=False):

    try:

        if force_reload or is_file_updated(
                filename='Resources.xlsx', Path=LION_OPTIMIZATION_PATH):

            _pr_user_resource_file = os_path.join(
                LION_OPTIMIZATION_PATH, 'Resources.xlsx')

            if not os_path.exists(_pr_user_resource_file):
                raise ValueError(f'Missing file: {_pr_user_resource_file}')

            __df_user_resources = read_excel(
                _pr_user_resource_file, sheet_name='ResourcesPerLoc')

            __df_user_resources['Total'] = __df_user_resources.apply(
                lambda x: x['Employed'] + x['Subco'], axis=1)

            __df_user_resources = df_groupby(df=__df_user_resources,
                                             agg_cols_dict={
                                                 'Total': 'max'},
                                             groupby_cols=['loc_code', 'Employed', 'Subco']).copy()

            PickleDumps.update(filename='df_user_resources',
                               obj=__df_user_resources)

        else:
            __df_user_resources = PickleDumps.get_content(
                filename='df_user_resources', if_null=None)

            if __df_user_resources is None:
                load_data(force_reload=True)

    except Exception as e:
        log_exception(popup=True, remarks=f'Error reading resources: {e}')

        return None

    return __df_user_resources
