import logging
import re


def clean_file_name(filename):

    try:
        invalid_chars = r'[<>:"/\\|?*]'

        cleaned_filename = re.sub(invalid_chars, '_', filename)

        cleaned_filename = cleaned_filename.rstrip(' .')

        reserved_names = {
            "CON", "PRN", "AUX", "NUL",
            "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
            "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
        }
        if cleaned_filename.upper() in reserved_names:
            cleaned_filename += '_'

        return str(cleaned_filename).strip()

    except Exception:
        logging.error("Error cleaning filename")
        return filename