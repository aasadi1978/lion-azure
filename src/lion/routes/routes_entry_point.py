from collections import defaultdict
from datetime import datetime
from json import loads as json_loads
from os import getenv, makedirs, path as os_path
from lion.config.paths import LION_DRIVER_REPORT_DIST_PATH, LION_HOME_PATH, LION_LOG_FILE_PATH
from lion.orm.scn_info import ScnInfo
from lion.reporting.consolidate_driver_reprots import generate_consolidated_driver_report
from lion.ui.pushpins import PUSHPIN_DATA
from lion.ui.driver_ui import DRIVERS_UI
from lion.ui.ui_params import UI_PARAMS
from lion.utils.kill_file import kill_file
from lion.logger.exception_logger import log_exception
from lion.orm.location import Location
from lion.create_flask_app.create_app import LION_FLASK_APP
from flask import Blueprint, redirect, render_template, request, url_for

from lion.orm.drivers_info import DriversInfo
from lion.utils.get_week_num import get_week_num
from lion.config.js_modification_trigger import LATEST_JS_MODIFICATION_TIME

from lion.utils.popup_notifier import show_error, show_popup


top_blueprint = Blueprint('lion', __name__)

@top_blueprint.route('/')
def index():
    # ui is the blueprint name for the routes_ui.py file
    return redirect(url_for('ui.loading_schedule'))

@top_blueprint.route('/display-schedule-docs', methods=['GET'])
def disp_schedule_docs():

    message = ''
    try:
        message = ScnInfo.docs()
    except Exception:
        message = log_exception(popup=False)

    if not message:
        message = 'No documentation is available!'

    options = {'vsn': LATEST_JS_MODIFICATION_TIME, 'message': message}
    return render_template('documentation.html', options=options)


@top_blueprint.route('/view_report_wait/<shiftname>', methods=['GET', 'POST'])
def view_report_wait(shiftname):
    params = {'redirect_url': f'/view_report/{shiftname}',
              'message': 'Extracting driver plan'}
    return render_template('wait.html', params=params)


@top_blueprint.route('/lion_message/<message>', methods=['GET', 'POST'])
def lion_message(message='This is a test!'):
    return render_template('message.html', message={'info': message, 'error': '', 'title': 'Info'})

@top_blueprint.route('/lion_error/<error>', methods=['GET', 'POST'])
def lion_error(error='This is a test!'):
    return render_template('message.html', message={'info': '', 'error': error, 'title': 'ERROR'})

@top_blueprint.route('/view_report/<shiftname>', methods=['GET', 'POST'])
def view_report(shiftname):

    _err_msg = ''
    t0 = datetime.now()

    try:

        drivers = []
        full_weekPlan = shiftname == 'FullPlan'

        if not full_weekPlan:

            if shiftname == 'rightclicked':

                shiftname = DriversInfo.get_shift_name(shift_id=UI_PARAMS.RIGHT_CLICK_ID)
                drivers = [UI_PARAMS.RIGHT_CLICK_ID]

            if not drivers:
                drivers = [] if shiftname == 'LION Driver Plan' else [int(x) for x in shiftname.split(
                    ';')]

        __df_driver_week = DRIVERS_UI.preview_driver_report(
            drivers=drivers, full_weekPlan=full_weekPlan)

        if __df_driver_week.empty:
            raise Exception(f'No driver plan was found for {shiftname}!')

        report_cols = [
            'start_point',
            'end_point',
            'tu_dest',
            'start_time',
            'end_time',
            'driving_time',
            'dist_miles',
            'traffic_type',
            'break_info'
        ]

        html_driver_plan = ''
        if not full_weekPlan:

            titles = list(set(
                __df_driver_week.title.tolist()))

            _n_drivers = len(set(__df_driver_week.driver.tolist()))

            report_data = []
            for ttle in titles:

                __df_driver = __df_driver_week[
                    __df_driver_week.title == ttle].copy()

                if not __df_driver.empty:
                    remarks = __df_driver['remarks'].iloc[0]
                    report_title = ttle  # __df_driver['title'].iloc[0]
                    vehiclename = __df_driver['vehicle'].iloc[0]
                    last_update = __df_driver['last_update'].iloc[0]

                    report_data.append({'table': __df_driver.loc[:, report_cols].copy().to_html(classes='data', index=False),
                                        'driver': shiftname,
                                        'remarks': remarks,
                                        'vehiclename': vehiclename,
                                        'report_title': report_title,
                                        'user_name': LION_FLASK_APP.config['LION_USER_FULL_NAME'],
                                        'last_update': last_update})

            if report_data:

                html_driver_plan = render_template('driver_report.html',
                                                   report_data=report_data,
                                                   top_report_title=f'{shiftname} ({_n_drivers})')

                with open(os_path.join(LION_HOME_PATH, 'driver_plan.html'), 'w') as _html_file:
                    _html_file.writelines(html_driver_plan)

                return html_driver_plan

        else:

            _loc_report_dir = os_path.join(
                LION_DRIVER_REPORT_DIST_PATH, r'Driver plan %s' % (get_week_num()))

            _driver_locs = set(__df_driver_week.driver_loc.tolist())

            for dloc in _driver_locs:

                pr_rep_path = os_path.join(_loc_report_dir, dloc)
                makedirs(pr_rep_path, exist_ok=True)

                __df_driver_loc = __df_driver_week[
                    __df_driver_week.driver_loc == dloc].copy()

                titles = list(set((
                    __df_driver_loc.title.tolist())))

                _n_drivers = len(set(__df_driver_loc.driver.tolist()))

                report_data = []
                for ttle in titles:

                    __df_driver = __df_driver_loc[
                        __df_driver_loc.title == ttle].copy()

                    if not __df_driver.empty:
                        remarks = __df_driver['remarks'].iloc[0]
                        loc_name = __df_driver['driver_loc_name'].iloc[0]
                        report_title = ttle  # __df_driver['title'].iloc[0]
                        vehiclename = __df_driver['vehicle'].iloc[0]
                        last_update = __df_driver['last_update'].iloc[0]

                        report_data.append({'table': __df_driver.loc[:, report_cols].copy().to_html(classes='data', index=False),
                                            'driver': shiftname,
                                            'remarks': remarks,
                                            'vehiclename': vehiclename,
                                            'report_title': report_title,
                                            'user_name': LION_FLASK_APP.config['LION_USER_FULL_NAME'],
                                            'last_update': last_update})

                if report_data:

                    html_driver_plan = render_template('driver_report.html',
                                                       report_data=report_data,
                                                       top_report_title=f'{loc_name} driver plan')

                    report_htm_file = os_path.join(
                        pr_rep_path, f'{dloc}_driver_report.html')

                    kill_file(report_htm_file)
                    with open(report_htm_file, 'w') as _html_file:
                        _html_file.writelines(html_driver_plan)

            generate_consolidated_driver_report()

    except Exception:

        html_driver_plan = ''
        _err_msg = log_exception(
            popup=True, remarks=f'Extracting driver report failed!')

    if html_driver_plan == '':
        _err_msg = f'{_err_msg}. No report was created!'
        return render_template('message.html', message={
            'error': _err_msg,
            'info': ''})

    minutes = int((datetime.now() - t0).total_seconds()/60)
    return render_template('message.html', message={
        'error': '',
        'info': f'Driver plan was successfully exported in {minutes} minutes!'})


# @top_blueprint.route('/display-locations-on-map', methods=['GET'])
# def disp_locs():

#     __dct_ftprnt = Location.to_dict()
#     __dct_ftprnt = {k: v for k, v in __dct_ftprnt.items()
#                     if int(v['active']) != 0}
    
#     _all_locs = [f"{x} - {v['location_name']}" for x, v in __dct_ftprnt.items() 
#                  if v['loc_type'].lower() != 'customer']

#     _dct_loc_conts = defaultdict(set)
#     for loc_code, v in __dct_ftprnt.items():
#         _dct_loc_conts[v['loc_type']].update([loc_code])

#     dct_loc_type_cnt = {
#         typ: len(_dct_loc_conts[typ]) for typ in set(_dct_loc_conts)}

#     str_info = ''
#     for k, v in dct_loc_type_cnt.items():
#         str_info = f"{str_info}{k}: {v} | "

#     str_info = f"{str_info}Total: {len(__dct_ftprnt)}"

#     options = {'vsn': LATEST_JS_MODIFICATION_TIME, 'dict_footprint': __dct_ftprnt, 'all_locs': _all_locs,
#                'str_info': str_info, 'dct_pushpins': PUSHPIN_DATA.get(), 
#                'LION_BING_API_KEY': getenv('LION_BING_API_KEY')}

#     return render_template('disp-locations.html', options=options)


@top_blueprint.route('/status_page', methods=['GET'])
def status_page():
    with open(LION_LOG_FILE_PATH, 'r') as f:
        log_content = f.readlines()

    return render_template('status_page.html', 
                           options={'vsn': LATEST_JS_MODIFICATION_TIME, 
                                    'status': log_content})


@top_blueprint.route('/disp_popup', methods=['POST'])
def disp_popup():

    try:
        requested_data = request.form['requested_data']
        requested_data = json_loads(requested_data)
        msg = requested_data['message']
        type = requested_data['type']
        title = requested_data['title']

        if type == 'error':
            try:
                show_error(message=msg)
            except Exception:
                log_exception(popup=False)
        else:
            try:
                show_popup(message=msg, mytitle=title)
            except Exception:
                log_exception(popup=False)

        return {}

    except Exception:
        show_error(f'Post method disp_popup failed! {log_exception(False)}')
        return {}


