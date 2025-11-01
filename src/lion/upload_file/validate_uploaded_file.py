import json
from typing import Union
from flask import request
import logging
from werkzeug.datastructures import FileStorage
from lion.config.paths import LION_USER_UPLOADS
from lion.utils.storage_manager import STORAGE_MANAGER

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

        if STORAGE_MANAGER.upload_file(
            uploaded_file,
            *['uploads', filename]):

            logging.info(f"File {filename} uploaded to Azure Blob Storage.")

    except Exception as e:
        logging.error(f"File upload to storage failed: {str(e)}")
        return 'File upload failed.'

    if allowed_extensions and not filename.lower().endswith(tuple(allowed_extensions)):
        return 'Invalid file type. Allowed file extensions are: ' + ', '.join(allowed_extensions)

    # Special handling for suppliers.csv
    if filename.lower() in ['suppliers.csv', 'traffic_types.xlsx', 'vehicles.xlsx']:
        try:
            LION_USER_UPLOADS.mkdir(parents=True, exist_ok=True)

            local_path = LION_USER_UPLOADS / filename
            uploaded_file.save(local_path)

            logging.info(f"'{filename}' saved locally at {local_path}")

        except Exception as e:
            logging.error(f"Failed to save '{filename}' locally: {str(e)}")
            return f'Failed to save {filename} locally.'
        
        if local_path.exists():

            if filename.lower() == 'traffic_types.xlsx':
                from lion.traffic_types.update_traffic_types import update_traffic_types
                update_traffic_types()

            elif filename.lower() == 'vehicles.xlsx':
                from lion.vehicle_types.update_vehicle_types import update_vehicle_types
                update_vehicle_types()

            elif filename.lower() == 'suppliers.csv':
                from lion.orm.drivers_info import DriversInfo
                DriversInfo.update_suppliers()

        else:
            return f'Local file {filename} does not exist after saving.'

    return uploaded_file