from pandas import read_excel
from lion.config.paths import LION_FILES_PATH, LION_PROJECT_HOME
from lion.logger.exception_logger import log_exception
from lion.orm.vehicle_type import VehicleType


def update_vehicle_types():
    """
    In order to update vehicle types, add/remove or modify, one has to
    apply relevent changes on 'vehicles.xlsx' file in LION_FILES_PATHdirectory in LION-Shared SharePoint.
    Once changes applied and saved, the corresponding button in LION can be clicked to apply the changes
    """

    _filepath = LION_PROJECT_HOME / 'vehicles.xlsx'

    if not _filepath.exists():
        _filepath = LION_FILES_PATH / 'vehicles.xlsx'

    try:
        _df_vhcle_types = read_excel(
            _filepath, sheet_name='vehicles')

        _df_vhcle_types.set_index(['vehicle_name'], inplace=True)
        _dct = _df_vhcle_types.to_dict(orient='index')

        for vname, dct in _dct.items():
            VehicleType.update(vehicle_name=vname,
                               vehicle_short_name=dct.get('ShortName', vname))

    except Exception:
        _err = log_exception(
            popup=False, remarks='Vehicle types could not be updated!')

        if 'permission denied' in _err.lower():
            return {'code': 400, 'message': f"The file {_filepath} is opened by another user or application. Please close the file and try again!"}
        else:
            return {'code': 400, 'message': _err}

    return {'code': 200, 'message': 'Vehicles updated successfully!'}


if __name__ == '__main__':
    from lion.create_flask_app.create_app import LION_FLASK_APP
    with LION_FLASK_APP.app_context():
        update_vehicle_types()
