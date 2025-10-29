from pandas import DataFrame
from os import makedirs, path as os_path
from lion.config.paths import LION_ARCGIS_PATH
from lion.utils.dfgroupby import groupby as df_grpby
from lion.orm.orm_runtimes_mileages import RuntimesMileages
from lion.utils.session_manager import SESSION_MANAGER
from lion.xl.write_excel import write_excel as xlwriter
from lion.utils.popup_notifier import show_error
from lion.logger.exception_logger import log_exception

def get_lanes_xlsx_file(df_lanes=DataFrame(
        columns=['Origin', 'Destination', 'VehicleType']), scenario='Default', overwrite_existing_lanes=False):

    try:
        if df_lanes.empty:
            raise Exception('No lanes were provided!')

        df_lanes = df_grpby(df_lanes, groupby_cols=[
                            'Origin', 'Destination', 'VehicleType'])

        if not overwrite_existing_lanes:

            _existing_lanes = RuntimesMileages.get_existing_records()

            df_lanes['Lanes'] = scenario + '|' + df_lanes['Origin'] + '|' + \
                df_lanes['Destination'] + '|' + \
                df_lanes['VehicleType'].astype(str)

            df_lanes['not_existing'] = ~df_lanes['Lanes'].isin(_existing_lanes)
            df_lanes = df_lanes[df_lanes.not_existing].copy()
            _existing_lanes = RuntimesMileages.get_existing_records()
            del _existing_lanes

        df_lanes = df_grpby(df_lanes, groupby_cols=[
                            'Origin', 'Destination'])

        pr_egis_data_path = os_path.join(
            *[LION_ARCGIS_PATH, 'user', SESSION_MANAGER.get('user_name')])

        makedirs(pr_egis_data_path, exist_ok=True)

        xlwriter(df=df_lanes.copy(),
                 sheetname='Lanes',  xlpath=os_path.join(pr_egis_data_path, 'Lanes.xlsx'),
                 echo=True)

    except Exception:
        show_error(
            f"Generating DDT input data failed! {log_exception(False)}")
        return
