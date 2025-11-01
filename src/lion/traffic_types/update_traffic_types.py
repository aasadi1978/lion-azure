from os import remove
from lion.logger.exception_logger import log_exception
from pandas import read_csv, read_excel
from lion.config.paths import LION_USER_UPLOADS
from lion.orm.traffic_type import TrafficType
from lion.logger.status_logger import log_message


def update_traffic_types(*args, **kwargs):
    """
    In order to update traffic types, add/remove or modify, one has to
    apply relevent changes on 'traffic_types.xlsx' file in LION_FILES_PATHdirectory in LION-Shared SharePoint.
    Once changes applied and saved, the corresponding button in LION can be clicked to apply the changes
    """

    _filepath = LION_USER_UPLOADS / 'traffic_types.xlsx'
    _filepath = _filepath if _filepath.exists() else LION_USER_UPLOADS / 'traffic_types.csv'
    _filepath = _filepath.resolve()

    if not _filepath.exists():
        return

    try:

        if _filepath.suffix.lower() == '.csv':
            _df_traffic_types = read_csv(_filepath, sep=',', header=0)

        else:
            _df_traffic_types = read_excel(
                _filepath, sheet_name='traffic_types', engine='openpyxl')
        
        if 'traffic_type' not in _df_traffic_types.columns or 'color' not in _df_traffic_types.columns:
            return {'code': 400, 'message': "The 'traffic_types.xlsx' file is missing required columns: 'traffic_type' and 'color'."}

        _df_traffic_types.set_index(['traffic_type'], inplace=True)
        _dct = _df_traffic_types.color.to_dict()

        for tpe, col in _dct.items():
            TrafficType.update(traffic_type=tpe, traffic_type_color=col)
        
        log_message(message='Traffic types updated successfully!', module_name='update_traffic_types')
        remove(_filepath)

    except Exception:
        _err = log_exception(
            popup=True, remarks='Traffic types could not be updated!')

        if 'permission denied' in _err.lower():
            return {'code': 400, 'message': f"The file {_filepath} is opened by another user or application. Please close the file and try again!"}
        else:
            return {'code': 400, 'message': _err}

    return {'code': 200, 'message': 'Traffic types updated successfully!'}
