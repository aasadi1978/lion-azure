from flask import Blueprint, jsonify, request
from flask.json import loads as json_loads
from lion.movement.insert_new_movements import insert_movements

movements_bp = Blueprint('movements', __name__)

@movements_bp.route('/insert-movements', methods=['POST'])
def insertmovements():

    task = 'creating movement'
    requested_data = request.form['requested_data']
    requested_data = json_loads(requested_data)
    dct_params = requested_data['dct_params']

    try:
        dct_chart_data = insert_movements(**dct_params)
    except Exception as e:
        return jsonify({'code': 400, 'error': f'{task} failed. ' + str(e)})
    
    if dct_chart_data.get('error', ''):
        return jsonify({'code': 400, 'error': f'{task} failed. ' + str(dct_chart_data['error'])})
    
    return jsonify(dct_chart_data)