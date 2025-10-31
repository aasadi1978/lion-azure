from pathlib import Path
from typing import Union
from flask import request
import logging
from werkzeug.datastructures import FileStorage
from lion.config.paths import LION_USER_UPLOADS
from lion.utils.storage_manager import STORAGE_MANAGER

def receive_file_upload(allowed_extensions={'xlsx', 'xlsm', 'csv'}) -> Union[FileStorage, str]:
    """
    Endpoint to receive an Excel file upload from frontend, 
    It validate the file extension and returns the FileStorage object if valid.
    Otherwise, it returns None.
    """

    filename = ''
    try:
        if 'file' not in request.files:
            return None

        uploaded_file: FileStorage = request.files['file']
        if uploaded_file.filename == '':
            return 'Invalid filename.'

        if STORAGE_MANAGER.upload_file(
            uploaded_file,  
            *['uploads', uploaded_file.filename]):
            logging.info(f"File {uploaded_file.filename} uploaded to Azure Blob Storage.")

        filename = f"{uploaded_file.filename}"

    except Exception as e:
        logging.error(f"File upload failed: {str(e)}")
        return 'File upload failed.'

    if not uploaded_file.filename.lower().endswith(tuple(allowed_extensions)):
        return 'Invalid file type. Allowed file extensions are: ' + ', '.join(allowed_extensions)
    

    # Special handling for suppliers.csv
    if filename.lower() in ['suppliers.csv', 'traffic_types.xlsx', 'vehicles.xlsx']:
        try:
            local_dir = LION_USER_UPLOADS
            local_dir.mkdir(parents=True, exist_ok=True)

            local_path = local_dir / filename
            uploaded_file.save(local_path)

            logging.info(f"'{filename}' saved locally at {local_path}")
            
        except Exception as e:
            logging.error(f"Failed to save '{filename}' locally: {str(e)}")
            return f'Failed to save {filename} locally.'
        
        if filename.lower() == 'traffic_types.xlsx':
            from lion.traffic_types.update_traffic_types import update_traffic_types
            update_traffic_types()

        elif filename.lower() == 'vehicles.xlsx':
            from lion.vehicle_types.update_vehicle_types import update_vehicle_types
            update_vehicle_types()

        elif filename.lower() == 'suppliers.csv':
            from lion.orm.drivers_info import DriversInfo
            DriversInfo.update_suppliers()

    return uploaded_file