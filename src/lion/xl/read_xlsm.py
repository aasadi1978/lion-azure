from pandas import ExcelFile, DataFrame
import logging


def read_xlsm(filepath='', sheet_name='', logger=None) -> DataFrame:

    try:
        xl = ExcelFile(filepath)
        df = xl.parse(sheet_name)
    except Exception as e:
        logging.error(f"""Error reading xlsm file {filepath}, sheet {sheet_name}: {str(e)}""")
        return DataFrame()

    return df
