from typing import Union
from flask import request
import logging
from werkzeug.datastructures import FileStorage

from lion.utils.session_manager import SESSION_MANAGER
from lion.utils.storage_manager import STORAGE_MANAGER

def receive_file_upload(allowed_extensions={'xlsx', 'xlsm', 'csv'}) -> Union[FileStorage, str]:
    """
    Endpoint to receive an Excel file upload from frontend, 
    It validate the file extension and returns the FileStorage object if valid.
    Otherwise, it returns None.
    """
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

    except Exception as e:
        logging.error(f"File upload failed: {str(e)}")
        return 'File upload failed.'

    if not uploaded_file.filename.lower().endswith(tuple(allowed_extensions)):
        return 'Invalid file type. Allowed file extensions are: ' + ', '.join(allowed_extensions)

    return uploaded_file