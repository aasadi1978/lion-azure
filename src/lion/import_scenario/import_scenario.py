import logging
from shutil import copyfile
from lion.bootstrap.constants import LION_SCHEDULE_DATABASE_NAME, LION_TEMP_SCENARIO_DATABASE_NAME
from lion.config.paths import LION_DEFAULT_SQLDB_PATH, LION_SHARED_SCHEDULE_PATH, LION_SQLDB_PATH, PR_LION_LOCAL_SCHEDULE_DB
from lion.logger.log_entry import LogEntry
from lion.orm.changeover import Changeover
from lion.orm.drivers_info import DriversInfo
from lion.orm.scn_info import ScnInfo
from lion.orm.temp_scn_info import TempScnInfo
from lion.ui.ui_params import UI_PARAMS
from lion.import_scenario.copy_scn_data import copy_schedule_data
import lion.utils.reset_global_instances as reset_globals
from lion.create_flask_app.create_app import LION_FLASK_APP
from lion.shift_data.shift_data import UI_SHIFT_DATA
from lion.logger.exception_logger import log_exception, return_exception_code
from lion.utils.sort_dir_tm import sort_dir_tm
from os import path as os_path

def import_schedule(**dct_params):

    pwd_required = False

    pr_temp_dest_path = LION_SQLDB_PATH / LION_TEMP_SCENARIO_DATABASE_NAME
    try:

        scn_name = dct_params.get('scn_name', '')

        if scn_name == '':
            lst_scnarios = sort_dir_tm(
                dir=LION_SHARED_SCHEDULE_PATH, endswith='.db')
            
            if lst_scnarios:

                lst_scnarios = [
                    x for x in lst_scnarios if not os_path.basename(x.lower()).startswith('encrypted-')]

                if lst_scnarios:
                    scn_name = lst_scnarios[0]

        if scn_name == '':
            raise ValueError('No scenario has been selected!')

        selected_schedule_file_path = LION_SHARED_SCHEDULE_PATH / os_path.basename(scn_name)

        if not selected_schedule_file_path.is_file() or not selected_schedule_file_path.exists():
            return {'error': 'Source database not found!', 'code': 400}

        pr_temp_dest_path = LION_SQLDB_PATH / LION_TEMP_SCENARIO_DATABASE_NAME
        database_copied_successfully = True
        try:
            copyfile(selected_schedule_file_path, pr_temp_dest_path)
            database_copied_successfully = database_copied_successfully and pr_temp_dest_path.is_file()
        except Exception:
            database_copied_successfully = False
            log_exception(popup=False, remarks=f'Copying scenario database {selected_schedule_file_path} failed!')

        if database_copied_successfully:

            logging.debug(f'The scenario {TempScnInfo.scn_name()} has been copied as {LION_TEMP_SCENARIO_DATABASE_NAME} ...')

            # Make sure the schedule database based on the latest settings is available.
            copyfile(LION_DEFAULT_SQLDB_PATH / LION_SCHEDULE_DATABASE_NAME , PR_LION_LOCAL_SCHEDULE_DB)

            if PR_LION_LOCAL_SCHEDULE_DB.exists() and copy_schedule_data():

                UI_SHIFT_DATA.reset()
        
                pwd_required = ScnInfo.get_param(
                    param='password', if_null=None) is not None

                if pwd_required:

                    scn_user = ScnInfo.get_param(param='user', if_null=0)
                    if str(scn_user).isnumeric():
                        scn_user = int(scn_user)

                    if LION_FLASK_APP.config['LION_USER_ID'] == scn_user:
                        pwd_required = False

                Changeover.clear_cache()
                DriversInfo.clear_cache()
                UI_PARAMS.CHANGEOVERS_VALIDATED = False
                UI_PARAMS.DCT_CACHED_INFO = {}
                reset_globals.reset_all()
                LogEntry.clear_log()
        
        else:
            logging.debug('Failed to copy scenario database! selected scn name.')
            return {'error': 'Copying scenario database failed!', 'code': 400}

    except Exception:
        return return_exception_code(popup=False, remarks=f"Copying local_schedule.db failed!")

    return {'message': 'Schedule imported successfully! Please reboot LION to see the data! ',
            'code': 200, 'pwd_required': pwd_required}