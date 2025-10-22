from typing import Union
import logging
from pathlib import Path
from werkzeug.datastructures import FileStorage
from lion.bootstrap.constants import WEEKDAYS_NO_SAT
from lion.orm.vehicle_type import VehicleType
from pandas import DataFrame, read_excel
from lion.xl.read_xlsm import read_xlsm
import lion.optimization.read_user_movements.movements_headers as headers


def validate_user_movements_file(mxlsFile: Union[Path, str, FileStorage] = '') -> DataFrame | str:
    """
    Read the movements.xlsm file and run an intitial clean up process to delete
    the records with no key data such as location, time or running days
    """
    
    try:

        if isinstance(mxlsFile, FileStorage):

            if str(mxlsFile.filename).lower().endswith('.xlsm'):
                df_movs = read_xlsm(filepath=mxlsFile, sheet_name='Movements')
            elif str(mxlsFile.filename).lower().endswith('.xlsx'):
                df_movs = read_excel(mxlsFile, sheet_name='Movements')
            else:
                return 'Invalid file format or missing sheetname Movements!'

        elif str(mxlsFile).lower().endswith('.xlsm'):
            df_movs = read_xlsm(filepath=mxlsFile, sheet_name='Movements')
        elif str(mxlsFile).lower().endswith('.xlsx'):
            df_movs = read_excel(mxlsFile, sheet_name='Movements')
        else:
            return 'Invalid file format or missing sheetname Movements!'

        validate_result = validate_minimum_required_fields(df_movs)
        if validate_result != 'OK':
            raise Exception(validate_result)
        
        df_movs = validate_required_fields(df_movs)
        if df_movs.empty:
            raise Exception('The movements file is empty or invalid!')

        df_movs.fillna(value='', inplace=True)

        df_movs = remove_invalid_movements(df_movs)
        if df_movs.empty:
            raise Exception('No valid movements found in the file!')

        df_movs = clean_up_and_transform(df_movs)
        if df_movs.empty:
            raise Exception('No valid loc_string found in the file!')
        
    except Exception as e:
        return f'Reading movements file failed! {str(e)}'

    return df_movs[headers.COLUMNS].copy() if not df_movs.empty else 'No valid movements found in the file!'

def remove_invalid_movements(df_movs):

    try:

        df_movs['FlagRowsToKeep'] = df_movs.apply(
            lambda x: str(x['From']).strip() != '' and str(x['To']).strip() != '' and len(str(x['DepTime']).strip()) >= 4, axis=1)

        df_movs['FlagRowsToKeep'] = df_movs.apply(
                        lambda x: x['FlagRowsToKeep'] if x['FlagRowsToKeep'] else sum([
                        int(x[c] in ['X', 'x', 1, '1']) for c in WEEKDAYS_NO_SAT]) > 0, axis=1)

        df_movs = df_movs[df_movs.FlagRowsToKeep].copy()

        df_movs.drop(columns=['FlagRowsToKeep'], inplace=True, axis=1)

        return df_movs
    
    except Exception as e:
        logging.error(f"Error during removal of invalid movements: {str(e)}")
        return DataFrame()

def validate_minimum_required_fields(df_movs):
    
    try:
       
        missing_fields = [field for field in headers.REQUIRED_FIELDS if field not in df_movs.columns]
        if missing_fields:
             return f'Invalid file. Missing required fields: {", ".join(missing_fields)}'
        
        return 'OK'
    except Exception as e:
        return f'Error validating minimum required fields: {str(e)}'

def validate_required_fields(df_movs):
    """
    Validates the presence of required fields in the DataFrame.
    """
    try:
        if df_movs.empty:
            raise Exception('The movements file is empty!')

        for field in headers.COLUMNS:
            if field not in df_movs.columns:
                df_movs[field] = headers.DEFAULT_VALUES.get(field, '')

        return df_movs
    
    except Exception as e:
        logging.error(f"Error during validation of required fields: {str(e)}")

    return DataFrame()

def clean_up_and_transform(df_movs: DataFrame):
 
    try:

        dct_vehicle_code = VehicleType.dict_vehicle_code()

        df_movs['From'] = df_movs.From.apply(lambda x: 'APR2' if x == '2-Apr' else (
                        'MAY2' if x == '2-May' else x))

        df_movs['To'] = df_movs.To.apply(lambda x: 'APR2' if x == '2-Apr' else (
                        'MAY2' if x == '2-May' else x))

        df_movs['VehicleType'] = df_movs.VehicleType.apply(
            lambda x: dct_vehicle_code.get(str(x).strip(), 1))
        
        df_movs['TrafficType'] = df_movs.TrafficType.apply(
                        lambda x: x if len(str(x).strip()) > 1 else 'Express')

        df_movs['DepDay'] = df_movs.DepDay.apply(
                        lambda x: 0 if len(str(x)) == 0 else x)

        if 'InScope' in df_movs.columns:
            
            df_movs['InScope'] = df_movs.InScope.apply(
                lambda x: 1 if x in {1, '1', 'x', 'X', 'yes', 'Yes', True, 'True'} else 0)
            
            df_movs_ins_scope = df_movs[df_movs.InScope == 1].copy()
            if not df_movs_ins_scope.empty:
                df_movs = df_movs_ins_scope.copy()

            del df_movs_ins_scope

        df_movs['DepTime'] = df_movs.DepTime.apply(
                        lambda x: f"000000{str(x).strip().replace(':', '')}"[-4:]) 

        # df_movs['DepTime'] = df_movs.DepTime.apply(
        #                 lambda x: x if isinstance(x, str) else (
        #                     x.strftime('%H%M') if isinstance(x, datetime_time) else ''))

        empty_deptime = [x for x in df_movs.DepTime.tolist() if x == '']

        if empty_deptime:
            raise ValueError("Some departure times could not be recognized. Correct format: text(cell, 'hhmm')")

        df_movs = df_movs.loc[:, headers.COLUMNS].copy()
        df_movs['DepDay'] = df_movs.DepDay.apply(
                        lambda x: int(x) if len(str(x)) > 0 else 0)

        df_movs['tu'] = df_movs.tu.apply(
                        lambda x: '' if len(str(x).strip()) == 0 else x)

        df_movs['loc_string'] = df_movs.apply(lambda x: x['loc_string'] if len(
                        x['loc_string']) > 0 else (
                            '.'.join([x['From'], x['To'], x['DepTime']]) if len(str(x['tu']).strip()) == 0 else '.'.join(
                                [x['From'], x['To'], x['tu'], x['DepTime']])), axis=1)

        df_movs.sort_values(by=['loc_string'], inplace=True)
        df_movs.reset_index(inplace=True)

        df_movs['str_id'] = df_movs.apply(lambda x: '|'.join([str(x[c]) for c in [
                        'From', 'To', 'DepDay', 'DepTime', 'VehicleType', 'TrafficType']]), axis=1)

        # Normalize weekday columns to binary indicators (1 if present, 0 otherwise)
        valid_true_values = {1, '1', 'x', 'X', True}
        for day in WEEKDAYS_NO_SAT:
            df_movs[day] = df_movs[day].apply(lambda x: 1 if x in valid_true_values else 0)

        return df_movs

    except Exception as e:
        logging.error(f"Error during cleanup and transformation: {str(e)}")

        return DataFrame()