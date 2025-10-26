from datetime import datetime, timedelta
import json
import logging
from pathlib import Path

from lion.config.paths import LION_DRIVER_REPORT_DIST_PATH, LION_LOCAL_DRIVER_REPORT_PATH
from lion.bootstrap.constants import WEEKDAYS_NO_SAT
from lion.reporting.consolidate_driver_reprots import generate_consolidated_driver_report
from lion.reporting.gen_driver_dep_arr_report import DepArrReport
from lion.reporting.generate_driver_report import DRIVER_REPORT
from lion.utils.empty_dir import empty_dir


def gen_driver_report(dct_params: dict, *args, **kwargs) -> str | None:

    try:

        return_status = dct_params.get('return_status', False)
        DRIVER_REPORT.initialize()
        DRIVER_REPORT.right_click_id = False

        _weekdays = dct_params.get('weekdays', [])
        _publish = str(dct_params.get('publish', False)).lower() in ('true', '1', 'yes')
        _no_pdf = str(dct_params.get('no_pdf', False)).lower() in ('true', '1', 'yes')

        with open('dct_params.json', 'w') as f:
            json.dump(dct_params, f)

        __status_msg = ''

        DRIVER_REPORT.page_export = False

        __days = []
        _t0 = datetime.now()

        _dump_dir = LION_DRIVER_REPORT_DIST_PATH if _publish else LION_LOCAL_DRIVER_REPORT_PATH

        _csv_reports_dir = ''
        if not _publish:
            _csv_reports_dir = _dump_dir
            empty_dir(path_to_empty=LION_LOCAL_DRIVER_REPORT_PATH)

        DRIVER_REPORT.dump_directory = str(_dump_dir)

        _dep_arr_report_obj = DepArrReport()
        _dep_arr_report_obj.configure_base_data()
        _dep_arr_report_obj.dump_directory = str(_dump_dir)

    except Exception as e:
        status = logging.error(f'Initializing driver report failed! {e}')
        if return_status:
            return status
        return

    try:

        __days.extend(WEEKDAYS_NO_SAT)

        if _weekdays:
            __days = [d for d in __days if d in _weekdays]

        DRIVER_REPORT.gen_report_base()

        if not __days:
            raise Exception('No weekdays selected for driver report generation!')

        for __wkday in __days:

            objStatus = DRIVER_REPORT.gen_report(
                wkday=__wkday, no_pdf=_no_pdf)

            if objStatus.status_msg != '':
                __status_msg = '%s. %s' % (
                    __status_msg, objStatus.status_msg)

            if not _no_pdf:
                __status = _dep_arr_report_obj.gen_dep_arr_report(
                    wkday=__wkday)

                if __status != '':
                    __status_msg = '%s. %s' % (
                        __status_msg, __status)

        generate_consolidated_driver_report(
            pr_cons_driver_rep_path=Path(_csv_reports_dir))


    except Exception:
        logging.error('Generating driver report failed!')

    __t1 = datetime.now()
    if __status_msg == '':

        __status_msg = f'Driver plan has successfully exported in {_dump_dir}.\n' + \
            'Runtime: %s' % (
                str(timedelta(seconds=int((__t1 - _t0).total_seconds()))))

        logging.info(__status_msg)

    else:
        __status_msg = '%s.\nRuntime: %s' % (__status_msg, str(
            timedelta(seconds=int((__t1 - _t0).total_seconds()))))

        logging.error(__status_msg)

    if return_status:
        return __status_msg