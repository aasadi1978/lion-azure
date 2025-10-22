from flask import Blueprint, jsonify, request
from flask.json import loads as json_loads
from lion.runtimes.extract_runtimes import extract_data
from lion.runtimes.runtime_mileage_fetcher import UI_RUNTIMES_MILEAGES
from lion.runtimes.update_user_runtimes import update_user_defined_runtimes_mileages
from ..runtimes.dump_emaps_data import generate_eMAPS_lanes
from ..runtimes.import_ddt import update_default_distancetime

runtimes_bp = Blueprint('runtimes', __name__)

@runtimes_bp.route('/update-runtimes', methods=['POST'])
def update_runtimes():

    requested_data = request.form['requested_data']
    requested_data = json_loads(requested_data)
    overwrite_existing_lanes = requested_data['dct_params'].get('overwrite_existing_lanes', False)

    try:
        status = update_default_distancetime(overwrite_existing_lanes=overwrite_existing_lanes)
    except Exception as e:
        return jsonify({'code': 400, 'error': 'Running update_default_distancetime failed. ' + str(e)})
    
    if status != 'OK':
        return jsonify({'code': 400, 'error': 'Running update_default_distancetime failed. ' + str(status)})
    
    UI_RUNTIMES_MILEAGES.reset()
    return jsonify({'code': 200})

@runtimes_bp.route('/dump-emaps-data', methods=['POST'])
def dump_emaps_data():

    requested_data = request.form['requested_data']
    requested_data = json_loads(requested_data)
    dct_params = requested_data['dct_params']

    dc_status = generate_eMAPS_lanes(**dct_params)

    if 'error' in dc_status:
        return jsonify({'code': 400, 'error': dc_status['error']})
    
    return jsonify({'code': 200})

@runtimes_bp.route('/update-user-runtimes', methods=['POST'])
def update_user_runtimes():

    requested_data = request.form['requested_data']
    requested_data = json_loads(requested_data)
    dct_params = requested_data['dct_params']

    dc_status = update_user_defined_runtimes_mileages(**dct_params)

    if 'error' in dc_status:
        return jsonify({'code': 400, 'error': dc_status['error']})
    
    UI_RUNTIMES_MILEAGES.reset()
    return jsonify({'code': 200, 'message': dc_status['message']})


@runtimes_bp.route('/extract-runtimes-data', methods=['POST'])
def extract_runtimes_data():

    requested_data = request.form['requested_data']
    requested_data = json_loads(requested_data)
    dct_params = requested_data['dct_params']

    dc_status = extract_data(**dct_params)

    if 'error' in dc_status:
        return jsonify({'code': 400, 'error': dc_status['error']})
        
    return jsonify({'code': 200, 'message': dc_status['message']})
