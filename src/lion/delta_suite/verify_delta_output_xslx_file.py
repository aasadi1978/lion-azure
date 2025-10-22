from pathlib import Path
from lion.config.libraries import OS_PATH
from lion.delta_suite.delta_logger import DELTA_LOGGER
from pandas import read_excel


def validate_and_load_delta_excel(xlFilePath: Path):
    """
    Validates and loads movement data from an Excel file.
    This function reads all sheets from the specified Excel file, checks for the presence of required columns
    ('fromlocation', 'tolocation', 'vehicletype', 'deptime'), and processes the data if valid. The column names
    are normalized (stripped, lowercased, spaces and underscores removed) before validation. If the required columns
    are present and contain at least one non-empty row, the columns are renamed to a standardized format and the
    data is passed to DELTA_LOGGER for further processing.
    Args:
        xlFilePath (str): Path to the Excel file to be validated and loaded.
    Returns:
        bool: True if the file was successfully validated and loaded; False otherwise.
    Exceptions:
        Any exceptions encountered during processing are logged using DELTA_LOGGER.
    """
    try:

        xlFilePath = Path(xlFilePath).resolve()
        sheet_names = read_excel(xlFilePath, sheet_name=None).keys()

        for sheet in sheet_names:

            df_movements_data = read_excel(xlFilePath, sheet_name=sheet, header=0)

            REQUIRED_COLUMNS = {'fromlocation', 'tolocation', 'vehicletype', 'deptime'}
            df_movements_data = df_movements_data.rename(columns=lambda x: x.strip().lower().replace(' ', '').replace('_', ''))

            dct_header_mapping = {'fromlocation': 'FromLocation',
                                  'tolocation': 'ToLocation',
                                  'vehicletype': 'VehicleType',
                                  'deptime': 'DepTime'}

            if REQUIRED_COLUMNS.issubset(df_movements_data.columns):

                df_movements_data = df_movements_data[list(REQUIRED_COLUMNS)].copy()
                df_movements_data.rename(columns=dct_header_mapping, inplace=True)
                df_movements_data = df_movements_data[
                    df_movements_data.DepTime.notnull()].copy()

                if not df_movements_data.empty:
                    DELTA_LOGGER.update_df_movements(df_movements_data.copy())
                    return True
                
    except Exception:
        DELTA_LOGGER.log_exception(message=f"Error processing {OS_PATH.basename(xlFilePath)}.")
    
    return False