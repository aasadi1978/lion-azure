
from flask import Blueprint, jsonify
from lion.utils.run_detached import DETACHEDRUNS
from lion.optimization import run_optimization_from_delta
from lion.optimization.cache_params import cache_optimization_params
from lion.optimization import run_optimization
from lion.optimization.load_resources_data import import_resources_to_db
import lion.optimization.validate_optimization_db
from lion.optimization.orm.opt_movements import OptimizationMovements
from lion.utils.flask_request_manager import retrieve_form_data
from lion.optimization.optimization_logger import OPT_LOGGER

import lion.utils.validate_uploaded_file as validate_uploaded_file
from lion.optimization.optimization_logger import OPT_LOGGER
from lion.optimization.read_user_movements.clean_up_changeovers import purge_invalid_changeover_ids
from lion.optimization.read_user_movements.to_opt_movements import save_movements_on_opt_movements
from lion.optimization.read_user_movements.validate_and_import_user_movements import validate_user_movements_file

optim_bp = Blueprint('optimization', __name__)

@optim_bp.route('/run-optimization', methods=['POST'])
def run_optimization_module():
    return jsonify(run_optimization.run())

@optim_bp.route('/run-optimization-detached', methods=['POST'])
def run_optimization_detached():
    try:
        run_id = DETACHEDRUNS.run_immediate(
            run_optimization.run,
            process_title="optimization-run",
            bind='lion_optimization_db',
            **retrieve_form_data()
        )

        return jsonify({
            'code': 200,
            'message': f'Optimization run started in background. run_id={run_id}.',
        })
    except Exception as e:
        return jsonify({'code': 400, 'message': f'Failed to start optimization: {str(e)}'})

@optim_bp.route('/run-optimize-delta-movements', methods=['POST'])
def run_optimize_delta_movements():
    """
    We use this endpoint when the intention is to optimize movements directly
    coming from DELTA
    """
    return jsonify(run_optimization_from_delta.import_delta_info_and_build())


@optim_bp.route('/cache-opt-params', methods=['POST'])
def cache_opt_params():
    return jsonify(cache_optimization_params(**retrieve_form_data()))

@optim_bp.route('/fresh-start', methods=['POST'])
def fresh_start():
    status = lion.optimization.validate_optimization_db.fresh_start_optimization_db()
    return jsonify({'code': 200 if status else 400, 
                    "message": "Optimization database initialized." if status else "Failed to initialize optimization database!"})

@optim_bp.route('/upload-external-file', methods=['POST'])
def upload_external_file():

    OPT_LOGGER.OPT_GLOBAL_ERROR = ''

    if lion.optimization.validate_optimization_db.validate_optimization_database():

        df_data_file_storage = validate_uploaded_file.receive_file_upload(allowed_extensions={'xlsx', 'xlsm'})

        if isinstance(df_data_file_storage, str):
            return jsonify({'code': 400, 'message': df_data_file_storage})

        df_data = validate_user_movements_file(mxlsFile=df_data_file_storage)
        if isinstance(df_data, str):

            df_data = import_resources_to_db(file_path=df_data_file_storage)
            import_failed = isinstance(df_data, str)
            return jsonify({'code': 400 if import_failed else 200, 
                            'message': 'No valid resources file found in the file!' if import_failed else \
                                f'File {df_data_file_storage.filename} has been successfully imported.'})

        purge_invalid_changeover_ids()
        save_movements_on_opt_movements(df_movs=df_data.copy())

        if OPT_LOGGER.OPT_GLOBAL_ERROR:
            return jsonify({'code': 400, "message": OPT_LOGGER.OPT_GLOBAL_ERROR})

        n_imported_movs = OptimizationMovements.query.count()

        if n_imported_movs:
            return jsonify({
                'code': 200,
                'message': f'{n_imported_movs} have been successfully imported.'
            })

        return jsonify({'code': 400, 'message': 'No movements have been imported!'})
    
    return jsonify({'code': 400, 'message': 'Optimization database is not valid!'})
