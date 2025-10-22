import logging
from pathlib import Path
from typing import Union
from werkzeug.datastructures import FileStorage

from lion.orm.resources import Resources
from pandas import DataFrame, read_excel
from lion.utils.dfgroupby import groupby as df_groupby

def import_resources_to_db(file_path: Union[Path, str, FileStorage]) -> DataFrame | str:
    """
    Reads an Excel file and returns the specified sheet as a pandas DataFrame.
    
    Args:
        file_path (Union[Path, str, FileStorage]): The path to the Excel file or a FileStorage object.
        sheet_name (str): The name of the sheet to read from the Excel file.
    
    Returns:
        pd.DataFrame: The DataFrame containing the data from the specified sheet.
    Raises:
        ValueError: If the file does not exist or cannot be read.
    """

    try:
        df_user_resources = read_excel(file_path, sheet_name='ResourcesPerLoc')

        df_user_resources['Total'] = df_user_resources.apply(
            lambda x: x['Employed'] + x['Subco'], axis=1)

        df_user_resources = df_groupby(df=df_user_resources,
                                            agg_cols_dict={
                                                'Total': 'max'},
                                            groupby_cols=['loc_code', 'Employed', 'Subco']).copy()

        cols = df_user_resources.columns.tolist()
        df_user_resources.rename(
            columns=({c: c.lower() for c in cols}), inplace=True)

        if Resources.bulk_import_resources(df_resources=df_user_resources):
            return df_user_resources if not df_user_resources.empty else 'No data found in ResourcesPerLoc sheet.'

        del cols
    
    except Exception as e:
        logging.error(f"Failed to read Excel file: {str(e)}")
        return f"Failed to read Excel file: {str(e)}"

    return df_user_resources if not df_user_resources.empty else 'No data found in ResourcesPerLoc sheet.'
