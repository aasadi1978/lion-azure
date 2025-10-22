from typing import Union
from flask import request
import logging
from werkzeug.datastructures import FileStorage

def receive_file_upload(allowed_extensions={'xlsx', 'xlsm'}) -> Union[FileStorage, str]:
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

    except Exception as e:
        logging.error(f"File upload failed: {str(e)}")
        return 'File upload failed.'

    if not uploaded_file.filename.lower().endswith(tuple(allowed_extensions)):
        return 'Invalid file type. Allowed file extensions are: ' + ', '.join(allowed_extensions)

    return uploaded_file