import json
from typing import Union
from flask import request
import logging
from werkzeug.datastructures import FileStorage
from lion.config.paths import LION_USER_UPLOADS
from lion.logger.trigger_async_log_upload import trigger_async_log_upload

def receive_file_upload() -> Union[FileStorage, str]:
    """
    Endpoint to receive an Excel file upload from frontend, 
    It validate the file extension and returns the FileStorage object if valid.
    Otherwise, it returns None.
    """

    filename = ''
    try:
        if 'file' not in request.files:
            return None
        
        uploaded_file: FileStorage | None = request.files['file']
        client_extensions = request.form.get('allowedExtensions')
        allowed_extensions = set()

        if client_extensions:
            try:
                allowed_extensions = set(json.loads(client_extensions))
            except Exception:
                logging.warning("Failed to parse allowedExtensions from request.")
                allowed_extensions = set()

        filename = f"{uploaded_file.filename}" if uploaded_file else ''

        if filename == '':
            return 'Invalid filename.'

        local_path = LION_USER_UPLOADS / filename
        uploaded_file.save(local_path)

    except Exception as e:
        logging.error(f"File upload to storage failed: {str(e)}")
        return 'File upload failed.'

    if allowed_extensions and not filename.lower().endswith(tuple(allowed_extensions)):
        return 'Invalid file type. Allowed file extensions are: ' + ', '.join(allowed_extensions)

    # Special handling for suppliers.csv
    if filename.lower() in ['suppliers.csv', 'traffic_types.xlsx', 'vehicles.xlsx',
                            'traffic_types.csv', 'vehicles.csv']:

        if filename.lower() in ['traffic_types.xlsx', 'traffic_types.csv']:
            from lion.traffic_types.update_traffic_types import update_traffic_types
            update_traffic_types()

        elif filename.lower() in ['vehicles.xlsx', 'vehicles.csv']:
            from lion.vehicle_types.update_vehicle_types import update_vehicle_types
            update_vehicle_types()

        elif filename.lower() == 'suppliers.csv':
            from lion.orm.drivers_info import DriversInfo
            DriversInfo.update_suppliers()

    if local_path.exists():
        trigger_async_log_upload(src_path=LION_USER_UPLOADS, *['uploads'])

    return uploaded_file