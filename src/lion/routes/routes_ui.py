import logging
from os import environ
from json import loads as json_loads
from lion.delta_suite.import_delta_into_lion_main import import_delta_data
from flask import Blueprint, jsonify, render_template, request
from lion.orm.changeover import Changeover
from lion.logger.log_entry import LogEntry
from lion.orm.scenarios import Scenarios
from lion.orm.shift_movement_entry import ShiftMovementEntry
from lion.orm.drivers_info import DriversInfo
from lion.orm.user import User
from lion.reporting.publish_driver_plan import gen_driver_report
from lion.upload_file import validate_uploaded_file
from lion.utils.session_manager import SESSION_MANAGER
from lion.ui import changeover_chart
from lion.ui.basket import basket_chart
from lion.ui.basket.basket_shifts import get_basket_shift_ids
from lion.ui.dump_locations_info import dump_locs_data
from lion.ui.save_ui_params import refresh_schedule_filters
from lion.orm.shift_index import ShiftIndex
from lion.shift_data.save_schedule import save_final_version_of_schedule
from lion.shift_data.shift_data import UI_SHIFT_DATA
from lion.utils.flask_request_manager import retrieve_form_data
from lion.orm.location import Location
from lion.orm.user_params import UserParams
from lion.shift_data.refreshshift import refresh_shift
from lion.traffic_types.traffic_type_colors import refresh_traffic_type_colors
from lion.ui.validate_shift_data import load_shift_data_if_needed
from lion.ui.ui_params import UI_PARAMS
from lion.ui.chart import get_chart_data
from lion.ui.filter_tours import apply_filters
from lion.ui.driver_ui import DRIVERS_UI
from lion.ui.options import refresh_options
from lion.logger.exception_logger import log_exception, return_exception_code
from lion.upload_file.validate_uploaded_file import receive_file_upload
from lion.utils.warnnings_off import flaskWarningsOff
from lion.create_flask_app.create_app import FLASK_APP_INSTANCE, LION_FLASK_APP
import lion.reporting.extract_dep_arrivals as extract_dep_arrivals
import lion.utils.reset_global_instances as reset_globals

ui_bp = Blueprint('ui', __name__)

# @ui_bp.before_request
# def block_requests():
#     """
#     Before running any route in the ui_bp blueprint, first call this function. If it returns or raises an error (like abort(503)), 
#     stop the request there.
#     """
#     if UI_PARAMS.REQUEST_BLOCKER:
#         abort(503, description="A background operation is running. Try again shortly.")

@ui_bp.route('/loading_schedule/')
def loading_schedule():
    params = {'redirect_url': '/schedule',
              'message': 'Loading schedule'}

    return render_template('wait.html', params=params)

@ui_bp.route('/schedule/')
def schedule():
    flaskWarningsOff()

    # This is triggered when window.location.href = '/loading_schedule/' is called
    try:

        # Location.update_loc_names()
        refresh_traffic_type_colors()
        
        DRIVERS_UI.set_barwidth()
        DRIVERS_UI.clear_cache()

        status = load_shift_data_if_needed()

        if status.get('code', 200) == 200:
            status = apply_filters()

        status = refresh_options()

        if status.get('code', 200) == 200:
            return render_template('driver_schedule.html', options=UI_PARAMS.OPTIONS)

        return render_template('driver_schedule.html', options={})

    except Exception as e:
        return render_template('message.html', 
                               message={'title': 'ERROR',
                                        'error': f'Loading schedule failed!\n{log_exception(popup=False)}'})

@ui_bp.route('/cold-schedule-reload/', methods=['POST'])
def cold_schedule_reload():

    cold_start_error = ''
    try:
        # UI_PARAMS.REQUEST_BLOCKER = True
        # shutdown_db_engine()

        if not FLASK_APP_INSTANCE.is_app_valid():
            logging.info("Cold schedule reload: Creating new Flask app instance ...")
            FLASK_APP_INSTANCE.create(cold_start=True)

        Location.update_loc_names()
        refresh_traffic_type_colors()
        
        DRIVERS_UI.set_barwidth()
        DRIVERS_UI.clear_cache()

        status = load_shift_data_if_needed()

        if status and status.get('code', 400) == 400:
            cold_start_error = status.get('message', '')
        else:
            status = apply_filters()

            if status and status.get('code', 400) == 400:
                cold_start_error = status.get('message', '')
            else:
                status = refresh_options()
                if status and status.get('code', 400) == 400:
                    cold_start_error = status.get('message', '')

    except Exception as e:
        cold_start_error = f"Cold schedule reload failed: {str(e)}"
        logging.error(cold_start_error)


    if cold_start_error:
        return jsonify({'code': 400, 'error': cold_start_error, 'chart_data': {}})

    return jsonify({'chart_data': get_chart_data(), 'code': 200, 'message': 'Schedule reloaded successfully.'})

@ui_bp.route('/options', methods=['GET', 'POST'])
def get_options():
    try:
        return jsonify(UI_PARAMS.OPTIONS)
    except Exception:
        return jsonify({
            'code': 400,
            'message': f'Getting UI options failed!\n{log_exception(popup=False)}'
        }), 400


@ui_bp.route('/load-weekday-schedule', methods=['post'])
def load_weekday_schedule():
    try:

        day = retrieve_form_data().get('weekday', None)
        if not day:
            raise ValueError("No weekday selected!")

        UI_PARAMS.FILTERING_WKDAYS = []
        list_filtered_drivers = []
        dict_drivers_per_page = {}
        list_filtered_drivers = []
        UI_PARAMS.PAGE_NUM = 1

        if day != 'All':
            UI_PARAMS.FILTERING_WKDAYS = [day]
        else:
            list_filtered_drivers = UI_PARAMS.ALL_WEEK_DRIVERS_FILTERED

        if not list_filtered_drivers:
            """
            Combining with LIST_FILTERED_DRIVERS_ALL_WEEK helps user to apply day filter on already filtered data
            """
            list_filtered_drivers = DriversInfo.shift_ids_running_on_weekdays(weekdays=[day])
            if UI_PARAMS.ALL_WEEK_DRIVERS_FILTERED:
                list_filtered_drivers = [x for x in UI_PARAMS.ALL_WEEK_DRIVERS_FILTERED if x in list_filtered_drivers]

        if list_filtered_drivers:

            dict_drivers_per_page = ShiftIndex.get_page_shifts(
                dct_shift_ids=DriversInfo.to_sub_dict(
                    shift_ids=list_filtered_drivers), pagesize=UI_PARAMS.PAGE_SIZE)

        UI_PARAMS.DICT_DRIVERS_PER_PAGE = dict_drivers_per_page
        UI_PARAMS.LIST_FILTERED_SHIFT_IDS = list_filtered_drivers

        return jsonify({'code': 200, 'message': 'Weekdays selected',
                        'chart_data': get_chart_data()})

    except Exception:
        return jsonify({'code': 400, 'error': log_exception(popup=False)})

@ui_bp.route('/load-changeover-shifts', methods=['post'])
def load_changeover_shifts():
    try:
        changeovers = retrieve_form_data().get('changeovers', None)
        if not changeovers:
            raise ValueError("No changeovers selected!")

        chart = changeover_chart.chart(list_changeovers=changeovers)
        return jsonify({'code': 200, 'message': 'Weekdays selected', 'chart_data': chart})

    except Exception:
        return jsonify({'code': 400, 'error': log_exception(popup=False)})

@ui_bp.route('/load-basket', methods=['post'])
def loadbasket():
    try:
        shifts = get_basket_shift_ids()
        if shifts:

            refresh_options()
            dct_chart = basket_chart.chart()
            if dct_chart.get('code', 200) == 400:
                raise Exception(dct_chart['error'])

            return jsonify({'code': 200, 'message': f'{len(shifts)} shifts in basket', 'chart_data': dct_chart})

        else:
            return jsonify({'code': 201, 'message': 'No shifts in basket', 'chart_data': {}})
        
    except Exception:
        return jsonify({'code': 400, 'error': log_exception(popup=False)})

@ui_bp.route('/refresh-schedule-filter', methods=['post'])
def refresh_schedule_filter():
    try:
        refresh_schedule_filters(**retrieve_form_data())
    except Exception:
        return jsonify({'code': 400, 
                        'message': f'Refreshing schedule filter failed!\n{log_exception(popup=False)}'})

    return jsonify({'code': 200})

@ui_bp.route('/toggle-logging', methods=['post'])
def toggle_logging():
    try:
        dct_params = retrieve_form_data()
        log_enabled = dct_params.get('log_enabled', False)
        environ['LOGGING_ENABLED'] = str(log_enabled)
    except Exception:
        return jsonify({'code': 400, 
                        'message': f'Toggling logging failed!\n{log_exception(popup=False)}'})
    
    return jsonify({'code': 200, 
                    'message': f'Logging is now {"enabled" if environ.get("LOGGING_ENABLED", 'False') == 'True' else "disabled"}.'})

@ui_bp.route('/empty-basket', methods=['post'])
def empty_basket():
    try:
        UserParams.delete_param(param_to_del='basket_shifts')
        refresh_options(basket_drivers = [])
        return {'drivers': UI_PARAMS.OPTIONS['basket_drivers'], 'code': 200}
    except Exception:
        return jsonify(return_exception_code(popup=False))

@ui_bp.route('/drivers', methods=['POST'])
def drivers():

    try:
        requested_data = request.form['requested_data']
        requested_data = json_loads(requested_data)
        dct_params = requested_data['dct_params']

        return jsonify(DRIVERS_UI.execute_module(
            module_name=requested_data.get('str_func_name', ''), **dct_params))

    except Exception as e:
        return render_template('message.html', 
                               message={'title': 'ERROR',
                                        'error': f'Loading schedule failed!\n{log_exception(popup=False)}'})

@ui_bp.route('/import-delta-data', methods=['POST'])
def import_delta():

    dct_status = import_delta_data()
    if dct_status.get('code', 200) != 200:
        return jsonify(dct_status)

    UI_SHIFT_DATA.reset()
    ShiftIndex.clear_all()

    return jsonify(dct_status)

@ui_bp.route('/upload-delta-accdb', methods=['POST'])
def upload_accdb_delta():

    status = receive_file_upload(allowed_extensions={'.accdb', '.mdb'})
    if isinstance(status, str):
        return jsonify({'code': 400, 'message': status})

    UI_SHIFT_DATA.reset()
    ShiftIndex.clear_all()

    return jsonify({'code': 200, 'message': 'File uploaded successfully.'})


@ui_bp.route('/set-language', methods=['POST'])
def set_language():
    try:
        dct_params = retrieve_form_data()
        lang = dct_params.get('lang', LION_FLASK_APP.config['LION_REGION_LANGUAGE'])
        UserParams.update(lang = lang )
        LION_FLASK_APP.config['LION_REGION_LANGUAGE'] = dct_params.get('lang', LION_FLASK_APP.config['LION_REGION_LANGUAGE'])
    except Exception:
        return jsonify({'code': 400, 
                        'message': f'Setting language failed!\n{log_exception(popup=False)}. Current lang: {LION_FLASK_APP.config['LION_REGION_LANGUAGE']}'})

    return jsonify({'code': 200, 'message': 'Language set successfully to ' + LION_FLASK_APP.config['LION_REGION_LANGUAGE']})

@ui_bp.route('/get-chart-data', methods=['POST'])
def get_chart():

    try:
        status = get_chart_data(**retrieve_form_data())

        if status.get('code', 200) == 400:
            return jsonify({})

        return jsonify(status)

    except Exception as e:
        return render_template('message.html', 
                               message={'title': 'ERROR',
                                        'error': f'Loading schedule failed!\n{log_exception(popup=False)}'})


@ui_bp.route('/upload-external-file', methods=['POST'])
def upload_external_file():

    try:
        output = validate_uploaded_file.receive_file_upload(allowed_extensions={'xlsx', 'xlsm'})
        if isinstance(output, str):
            return jsonify({'code': 400, 'message': output})

    except Exception:
        return jsonify({'code': 400, 'message': f'Upload failed: {log_exception(popup=False)}'})

    return jsonify({'code': 200, 'message': f'{output.filename} has been successfully uploaded.'})


@ui_bp.route('/load-selected-schedule', methods=['post'])
def import_selected_schedule():

    # UI_PARAMS.REQUEST_BLOCKER = True

    try:
        dct_params = retrieve_form_data()
        scn_id = Scenarios.get_scn_id(scn_name=dct_params.get('scn_name', ''))

        scn_id_copy, scnname, group_name = DriversInfo.duplicate_scn(scn_id=scn_id)
        if isinstance(scn_id_copy, int) and scn_id_copy > 0:

            SESSION_MANAGER.set_user_context(
                current_scn_id=scn_id_copy, 
                scn_name=scnname,
                group_name=group_name)
            
            User.set_scn_id(scn_id=scn_id_copy)

            if ShiftMovementEntry.duplicate_scn(from_scn_id=scn_id, to_scn_id=scn_id_copy) and \
               Changeover.duplicate_scn(from_scn_id=scn_id, to_scn_id=scn_id_copy):

                Scenarios.duplicate_scn_settings(from_scn_id=scn_id, to_scn_id=scn_id_copy)

                Changeover.clear_cache()
                DriversInfo.clear_cache()
                UI_PARAMS.CHANGEOVERS_VALIDATED = False
                UI_PARAMS.DCT_CACHED_INFO = {}
                reset_globals.reset_all()
                LogEntry.clear_log()

                return jsonify({'code': 200, 'message': 'Scenario duplicated successfully.'})

        else:
            raise ValueError(f'Duplicating scenario failed! {scn_id_copy}.')

    except Exception:
        return return_exception_code(popup=False)

    # finally:
    #     UI_PARAMS.REQUEST_BLOCKER = False

@ui_bp.route('/save-final-vsn-schedule', methods=['post'])
def export_local_schedule_data():
    
    try:
        status = save_final_version_of_schedule(**retrieve_form_data())
        if status.get('code', 200) == 400:
            raise Exception(status['error'])

        return jsonify(status)
        
    except Exception as e:
        return jsonify({'message':  f'Exporting schedule failed!\n{log_exception(popup=False)}'})


@ui_bp.route('/refresh-shift', methods=['post'])
def refreshshift():
    try:
        return jsonify(refresh_shift(**retrieve_form_data()))
    except Exception as e:
        return jsonify({'code': 400, 'message': f'Error refreshing shift: {log_exception(popup=False)}'})

@ui_bp.route('/please_wait/<message>')
def please_wait(message):
    return render_template('please_wait.html', message=message)

@ui_bp.route('/reboot-lion', methods=['GET'])
def rebootlion():
    return {'message': 'The service is deprecated and will be removed in future versions.', 'code': 400}


@ui_bp.route('/extract-locations', methods=['POST'])
def extract_locations():
    try:
        return jsonify(dump_locs_data())
    except Exception:
        return jsonify({'code': 400, 
                'message': f'Extracting locations failed! {log_exception(popup=False)}'})

@ui_bp.route('/check-scn-password/', methods=['POST'])
def check_scn_password():
    try:
        requested_data = request.form['requested_data']
        requested_data = json_loads(requested_data)
        pwd = requested_data['pwd']

        status = Scenarios.check_password(password=pwd)

    except Exception:
        return {'code': 400, 'message': log_exception(popup=False), 'status': False}

    return {'code': 200, 'message': '', 'status': status}

@ui_bp.route('/extract-dep-arrivals/', methods=['POST'])
def extract_dep_arrivals_data():
    return extract_dep_arrivals.extract_data()

@ui_bp.route('/gen-driver-report', methods=['POST'])
def generate_driver_report():

    try:
        dct_params = retrieve_form_data()
        status = gen_driver_report(dct_params=dct_params)
        return jsonify({
            'code': 200, 
            'message': status,
        })
    except Exception:
        return jsonify({'code': 400, 'message': log_exception(popup=False)})
