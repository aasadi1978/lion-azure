from os import path as os_path
from datetime import datetime, timedelta

from flask import logging
from lion.config.paths import (LION_SHARED_ASSETS_PATH, LION_CONSOLIDATED_REPORT_PATH, LION_DIAGNOSTICS_PATH, 
                          LION_LOCAL_DRIVER_REPORT_PATH, LION_SHARED_SCHEDULE_PATH)
from lion.utils.remove_old_files import remove_old_files
from lion.config.paths import LION_DRIVER_REPORT_DIST_PATH


dct_days = {
    LION_SHARED_SCHEDULE_PATH:  5 * 365,
    LION_DRIVER_REPORT_DIST_PATH: 90,
    LION_DIAGNOSTICS_PATH: 90,
    LION_LOCAL_DRIVER_REPORT_PATH: 90
}


def update_log_file(msg):

    msg = f"{datetime.now().strftime('%Y%m%d %H:%M')} - clean_up_folders:\n{msg}"
    try:
        logging.error(msg)
    except Exception:
        return


def clean_up_folders():

    try:

        files_removed = False
        for mydir, days in dct_days.items():
            files_removed = files_removed or remove_old_files(
                mydir=mydir, days=days)

        files_removed = files_removed or remove_old_files(
            mydir=LION_CONSOLIDATED_REPORT_PATH, exclude=[
                'consolidated_driver_plan.xlsx', 'df_driver_report.csv'], days=90)

    except Exception as err:
        update_log_file(str(err))
        return

    if files_removed:
        with open(os_path.join(LION_SHARED_ASSETS_PATH, 'clean_up_folders.txt'), 'w') as f:
            f.write(datetime.now().strftime('%Y-%m-%d'))


if __name__ == '__main__':

    tday = datetime.now()
    try:
        with open(os_path.join(LION_SHARED_ASSETS_PATH, 'clean_up_folders.txt'), 'r') as f:
            dt = datetime.strptime(f.readline(), '%Y-%m-%d')

        if dt < tday - timedelta(days=30):
            clean_up_folders()

    except Exception:
        pass
