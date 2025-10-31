from os import remove
from pandas import read_excel
from lion.config.paths import LION_USER_UPLOADS
from lion.logger.exception_logger import log_exception
from lion.orm.vehicle_type import VehicleType


def update_vehicle_types():
    """
    In order to update vehicle types, add/remove or modify, one has to
    apply relevent changes on 'vehicles.xlsx' file in LION_FILES_PATHdirectory in LION-Shared SharePoint.
    Once changes applied and saved, the corresponding button in LION can be clicked to apply the changes
    """

    _filepath = LION_USER_UPLOADS / 'vehicles.xlsx'

    if not _filepath.exists():
        return

    try:
        _df_vhcle_types = read_excel(
            _filepath, sheet_name='vehicles')

        print(f"Reading {_filepath} to update vehicle types ...")
        print(_df_vhcle_types.head())
        return {'code': 200, 'message': f'Vehicles updated successfully! {_df_vhcle_types.shape[0]} records found.'}

        if 'vehicle_name' not in _df_vhcle_types.columns or 'ShortName' not in _df_vhcle_types.columns:
            return {'code': 400, 'message': "The 'vehicles.xlsx' file is missing required columns: 'vehicle_name' and 'ShortName'."}

        _df_vhcle_types.set_index(['vehicle_name'], inplace=True)
        _dct = _df_vhcle_types.to_dict(orient='index')

        for vname, dct in _dct.items():
            VehicleType.update(vehicle_name=vname,
                               vehicle_short_name=dct.get('ShortName', vname))
        
        remove(_filepath)

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
