from flask import request
import logging
from flask.json import loads
import lion.logger.exception_logger as EXCP_LOGGER

def retrieve_form_data(logger=EXCP_LOGGER) -> dict:

    try:
        requested_data = request.form['requested_data']
        requested_data = loads(requested_data)
        dct_params = requested_data.pop('dct_params', {})
        dct_params.update(requested_data)

        return dct_params

    except Exception as e:
        logger.log_exception(popup=False, remarks='retrieving request data failed!')
        logging.error(f"retrieving request data failed!: {str(e)}")
    
    return {}