from copy import deepcopy
from lion.logger.exception_logger import log_exception
from pandas import concat, read_csv, DataFrame
from lion.runtimes.utils import get_break_time, get_number_of_drivers, is_null_or_zero
from lion.utils.roundup_to_nearest_5 import roundup_to_nearest_5
from datetime import datetime
from lion.config.libraries import OS_PATH as os_path
from os import listdir
from lion.utils.popup_notifier import show_error

from lion.config.paths import LION_ARCGIS_PATH

def get_clean_data():

    try:

        csv_files = [x for x in listdir(
            LION_ARCGIS_PATH) if x.lower().endswith('.csv') and ('egis_runtimes' not in x.lower())]

        if not csv_files:
            show_error('No csv file was found in the output directory!')
            return DataFrame()

        df_data = DataFrame()
        for csv_file in csv_files:

            try:

                __df_emaps = read_csv(os_path.join(
                    LION_ARCGIS_PATH, csv_file), sep=',', header=0)
                
                required_columns = ['Name', 'Total_Kilometers', 'Total_TruckTravelTime', 'Total_TravelTime']
                if not all(col in __df_emaps.columns for col in required_columns):
                    continue

                __df_emaps['Total_TruckTravelTime'] = __df_emaps.Total_TruckTravelTime.apply(
                    lambda x: 0 if is_null_or_zero(x) else float(x))
                __df_emaps['Total_TravelTime'] = __df_emaps.Total_TravelTime.apply(
                    lambda x: 0 if is_null_or_zero(x) else float(x))

                __df_emaps['VehicleType'] = __df_emaps.apply(lambda x: 'Van' if float(x['Total_TravelTime']) > 0 else (
                    'Truck' if float(x['Total_TruckTravelTime']) > 0 else 'UnknownMode'), axis=1)

                __df_emaps = __df_emaps[__df_emaps.VehicleType.isin(
                    ['Van', 'Truck'])].copy()

                __df_emaps[["Origin", "Destination"]
                           ] = __df_emaps.Name.str.split("-", expand=True)
                __df_emaps["Origin"] = __df_emaps["Origin"].str.strip()
                __df_emaps["Destination"] = __df_emaps["Destination"].str.strip()
                __df_emaps = __df_emaps[__df_emaps.Origin !=
                                        __df_emaps.Destination].copy()

                __df_emaps['DrivingTime'] = __df_emaps.apply(lambda x: float(
                    x['Total_TravelTime']) if float(x['Total_TravelTime']) else (
                    float(x['Total_TruckTravelTime']) if float(x['Total_TruckTravelTime']) > 0 else 0), axis=1)

                __df_emaps = __df_emaps[__df_emaps.DrivingTime > 0].copy()
                __df_emaps['DrivingTime'] = __df_emaps.DrivingTime.apply(
                    lambda x: roundup_to_nearest_5(int(x)))
                __df_emaps['Distance'] = __df_emaps.Total_Kilometers.apply(
                    lambda x: int(float(x) + 0.5))

                __df_emaps['Drivers'] = __df_emaps.DrivingTime.apply(
                    lambda x: get_number_of_drivers(x))
                __df_emaps['BreakTime'] = __df_emaps.DrivingTime.apply(
                    lambda x: get_break_time(x))
                __df_emaps['RestTime'] = 0
                __df_emaps['OtherTime'] = 0
                __df_emaps['TotalTime'] = __df_emaps['DrivingTime'] + \
                    __df_emaps['BreakTime'] + __df_emaps['RestTime']
                __df_emaps['last_update'] = datetime.now().strftime(
                    '%Y-%m-%d %H:%M')

                df_data = concat([df_data, __df_emaps])

            except Exception:
                log_exception(
                    popup=False, remarks=f'Processing emaps file {os_path.basename(csv_file)} failed!')
                continue

        df_data = df_data.loc[:, ['Origin', 'Destination', 'VehicleType', 'Drivers', 'Distance', 'DrivingTime',
                                  'BreakTime', 'RestTime', 'OtherTime', 'TotalTime']].copy()
        df_data['loc_string'] = df_data.apply(
            lambda x: f"{x['Origin']}_{x['Destination']}", axis=1)
        
        if df_data.empty:
            show_error('No valid data found in the eGIS output files!')
            return DataFrame()

        df_data_copy = deepcopy(df_data)
        df_data_copy.rename(
            columns={'Origin': 'Destination', 'Destination': 'Origin'}, inplace=True)
        df_data_copy['loc_string'] = df_data_copy.apply(
            lambda x: f"{x['Origin']}_{x['Destination']}", axis=1)

        losstrngs = df_data.loc_string.tolist()
        df_data_copy = df_data_copy[~df_data_copy.loc_string.isin(
            losstrngs)].copy()

        if not df_data_copy.empty:
            df_data = concat([df_data, df_data_copy])

        df_data.drop(columns=['loc_string'], inplace=True, axis=1)
        df_data.to_csv(os_path.join(LION_ARCGIS_PATH,
                       'eGIS_Runtimes.csv'), index=False)

    except Exception:
        log_exception(popup=True, remarks='eMAPS data clean up failed!')
        return DataFrame()

    return df_data

if __name__ == '__main__':

    from lion.create_flask_app.create_app import LION_FLASK_APP
    with LION_FLASK_APP.app_context():
        df = get_clean_data()
        if not df.empty:
            print(df.head())
        else:
            print("No data found after cleaning up eGIS output.")