from pandas import DataFrame
from lion.runtimes.clean_up_arcgis_output import get_clean_data
from lion.logger.exception_logger import log_exception
from datetime import datetime
import warnings
from lion.runtimes.orm_runtimes_mileages import RuntimesMileages

warnings.filterwarnings('ignore')

def update_default_distancetime(overwrite_existing_lanes=False):

    df_runtimes_emaps = get_clean_data()
    __errmsg = ''

    try:

        if df_runtimes_emaps.empty:
            raise ValueError('No runtimes data found!')

        df_runtimes_emaps['Scenario'] = 'Default'
        df_runtimes_emaps['VehicleType'] = df_runtimes_emaps.VehicleType.apply(
            lambda x: 1 if x.lower() == 'truck' else (4 if 'van' in x.lower() else 0))

        df_runtimes_emaps['Origin'] = df_runtimes_emaps.Origin.apply(lambda x: 'APR2' if x == '2-Apr' else (
            'MAY2' if x == '2-May' else x))

        df_runtimes_emaps['Destination'] = df_runtimes_emaps.Destination.apply(lambda x: 'APR2' if x == '2-Apr' else (
            'MAY2' if x == '2-May' else x))

        __cols = df_runtimes_emaps.columns.tolist()
        if 'BreakTime' not in __cols:
            df_runtimes_emaps['BreakTime'] = 0

        if 'RestTime' not in __cols:
            df_runtimes_emaps['RestTime'] = 0

        df_runtimes_emaps['last_update'] = datetime.now().strftime(
            '%Y-%m-%d %H:%M')
        df_runtimes_emaps['remarks'] = ''

        df_runtimes_emaps['DrivingTime'] = df_runtimes_emaps.DrivingTime.astype(
            int)

        df_runtimes_emaps['Distance'] = df_runtimes_emaps.Distance.astype(
            int)

        df_runtimes_emaps['TotalTime'] = df_runtimes_emaps.TotalTime.apply(
            lambda x: int(x))

    except Exception:
        df_runtimes_emaps = DataFrame()
        __errmsg = f'{__errmsg}. Importing runtimes data failed. {log_exception(False)}'

    if not df_runtimes_emaps.empty:

        try:
            RuntimesMileages.import_df(
                df_new_disttime=df_runtimes_emaps.copy(), overwite_existing_lanes=overwrite_existing_lanes)
        except Exception:
            __errmsg = f'{__errmsg}. Importing df_runtimes_emaps failed. {
                log_exception(False)}'

    del df_runtimes_emaps
    return 'OK' if __errmsg == '' else __errmsg


if __name__ == '__main__':
    from lion.create_flask_app.create_app import LION_FLASK_APP
    with LION_FLASK_APP.app_context():
        update_default_distancetime()

