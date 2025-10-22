from lion.logger.exception_logger import log_exception
from pandas import read_excel
from lion.config.paths import LION_FILES_PATH, LION_HOME_PATH
from os.path import join
from lion.utils.is_file_updated import is_file_updated
from lion.orm.traffic_type import TrafficType
from lion.logger.status_logger import log_message


def update_traffic_types(force_update=False):
    """
    In order to update traffic types, add/remove or modify, one has to
    apply relevent changes on 'traffic_types.xlsx' file in LION_FILES_PATHdirectory in LION-Shared SharePoint.
    Once changes applied and saved, the corresponding button in LION can be clicked to apply the changes
    """

    _filepath = LION_HOME_PATH / 'traffic_types.xlsx'
    f_dir = LION_HOME_PATH

    if not _filepath.exists():
        f_dir = LION_FILES_PATH
        _filepath = LION_FILES_PATH / 'traffic_types.xlsx'

    
    if force_update or is_file_updated(
        filename='traffic_types.xlsx', Path=f_dir):

        try:

            _df_traffic_types = read_excel(_filepath, sheet_name='traffic_types')

            _df_traffic_types.set_index(['traffic_type'], inplace=True)
            _dct = _df_traffic_types.color.to_dict()

            for tpe, col in _dct.items():
                TrafficType.update(traffic_type=tpe, traffic_type_color=col)
            
            log_message(message='Traffic types updated successfully!', module_name='update_traffic_types')

        except Exception:
            _err = log_exception(
                popup=True, remarks='Traffic types could not be updated!')

            if 'permission denied' in _err.lower():
                return {'code': 400, 'message': f"The file {_filepath} is opened by another user or application. Please close the file and try again!"}
            else:
                return {'code': 400, 'message': _err}

        return {'code': 200, 'message': 'Traffic types updated successfully!'}



if __name__ == '__main__':
    from lion.create_flask_app.create_app import LION_FLASK_APP
    with LION_FLASK_APP.app_context():
        update_traffic_types(force_update=True)
