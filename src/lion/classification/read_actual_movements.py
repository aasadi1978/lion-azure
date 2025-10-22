from lion.bootstrap.constants import LION_SCHEDULE_DATABASE_NAME
from lion.config.paths import LION_SQLDB_PATH
from lion.utils.is_file_updated import is_file_updated
from lion.logger.exception_logger import log_exception
from lion.orm.drivers_info import DriversInfo
from lion.orm.pickle_dumps import PickleDumps
from pandas import DataFrame, Series
from lion.orm.shift_movement_entry import ShiftMovementEntry
from lion.utils.load_obj import load_obj
from lion.config.paths import LION_OPTIMIZATION_PATH
from lion.utils.dfgroupby import groupby as df_groupby


def load_movs_data(force_reload=False):

    try:

        dct_drivers = DriversInfo.to_dict()

        if force_reload or is_file_updated(
                filename=LION_SCHEDULE_DATABASE_NAME, Path=LION_SQLDB_PATH):

            m_records = ShiftMovementEntry.query.filter(
                ShiftMovementEntry.is_loaded == True).all()

            list_records = []
            for movObj in m_records:

                origin, dest, depday, deptime, vehicle, traffic_type = movObj.str_id.split(
                    '|')

                if not movObj.shift_id:
                    continue

                _movement_id = movObj.movement_id
                driver_loc = dct_drivers[movObj.shift_id]['loc']

                list_records.append(
                    [_movement_id, origin, dest, int(deptime), int(vehicle), driver_loc])

            df_movs = DataFrame(list_records, columns=[
                                'movement_id', 'origin', 'dest', 'deptime', 'vehicle', 'actual_driver_loc'])

            PickleDumps.update(filename='df_movs_for_ml', obj=df_movs)

        else:
            df_movs = PickleDumps.get_content(
                filename='df_movs_for_ml', if_null=None)

            if df_movs is None:
                load_movs_data(force_reload=True)

    except Exception as e:
        log_exception(
            popup=True, remarks=f'Error load_movs_data: {e}')
        return None

    return df_movs


def load_df_movs_data():

    try:
        df_movs = load_obj(str_FileName='df_all_movements',
                           path=LION_OPTIMIZATION_PATH, if_null=None)

        df_movs[['origin', 'dest', 'depday', 'deptime', 'vehicle', 'traffic_type']
                ] = df_movs.str_id.apply(lambda x: Series(str(x).split('|')))

        df_movs.rename(
            columns={'driver_loc': 'actual_driver_loc'}, inplace=True)

        df_movs.drop(columns=['movement_id'], inplace=True)

        df_movs = df_groupby(df=df_movs, groupby_cols=[
            'origin', 'dest', 'deptime', 'vehicle', 'actual_driver_loc']).copy()

        df_movs.reset_index(inplace=True)
        df_movs['movement_id'] = 1e6 + df_movs['index'] + 1

        df_movs = df_movs[['movement_id', 'origin', 'dest',
                           'deptime', 'vehicle', 'actual_driver_loc']].copy()

        df_movs['movement_id'] = df_movs['movement_id'].astype(int)
        df_movs['vehicle'] = df_movs['vehicle'].astype(int)
        df_movs['deptime'] = df_movs['deptime'].astype(int)

    except Exception as e:
        log_exception(
            popup=True, remarks=f'Error load_movs_data: {e}')
        return None

    return df_movs


if __name__ == '__main__':
    load_df_movs_data()
