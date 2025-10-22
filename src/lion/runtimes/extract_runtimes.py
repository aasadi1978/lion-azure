from lion.utils.km2mile import km2mile
from lion.utils.minutes2hhmm import minutes2hhmm
from lion.utils.df2csv import export_dataframe_as_csv
from lion.logger.exception_logger import log_exception
from lion.orm.vehicle_type import VehicleType
from lion.utils.roundup_to_nearest_5 import roundup_to_nearest_5
from lion.runtimes.orm_runtimes_mileages import RuntimesMileages
from lion.config.paths import LION_LOGS_PATH
from os import path as os_path
from lion.runtimes.get_lanes import get_lanes_data


def extract_data(**dct_params):

    loc_str = dct_params.get('LocStrings', '').upper()

    if loc_str != '':

        if len(loc_str.split(';')) == 1:

            str_info = ''
            loc_str = loc_str.split(';')[0]

            if len(loc_str.split('.')) == 2:

                loc1, loc2 = [x.strip() for x in loc_str.split('.')]
                dist = 0

                for vhcl in [1, 4]:

                    dr, dist2 = RuntimesMileages.get_dist_runtime(
                        orig=loc1, dest=loc2, vehicle=vhcl)

                    if not dist:
                        dist = dist2

                    if dr:
                        str_info = f'{str_info}{VehicleType.get_vehicle_short_name(
                            vhcl)}-hh:mm: {minutes2hhmm(roundup_to_nearest_5(dr))}\n'

                if dist:
                    str_info = f'{str_info}Miles: {km2mile(dist)}\n'

            return {'message': str_info}

    df_lanes = get_lanes_data(**dct_params)
    
    if df_lanes.empty:
        return {'error': 'No lanes were specified!'}
    
    dict_dist_time = RuntimesMileages.to_dict()
    csv_file = os_path.join(LION_LOGS_PATH, 'Runtimes.csv')
    try:

        for vhcl in [1, 4]:

            df_lanes[VehicleType.get_vehicle_short_name(vhcl)] = df_lanes.apply(
                lambda x: dict_dist_time.get(x['Origin'], {}).get(
                    x['Destination'], {}).get(vhcl, {}).get('driving_time', 0), axis=1)

        df_lanes['Miles'] = df_lanes.apply(
            lambda x: dict_dist_time.get(x['Origin'], {}).get(
                x['Destination'], {}).get(1, {}).get('dist', 0), axis=1)

        df_lanes['Miles'] = df_lanes.apply(
            lambda x: x['Miles'] if x['Miles'] > 0 else dict_dist_time.get(x['Origin'], {}).get(
                x['Destination'], {}).get(4, {}).get('dist', 0), axis=1)

        df_lanes = df_lanes[df_lanes.Miles > 0].copy()
        df_lanes['Miles'] = df_lanes['Miles'].apply(
            lambda x: km2mile(x))

        df_lanes['Artic'] = df_lanes.Artic.apply(
            lambda x: minutes2hhmm(roundup_to_nearest_5(x)))

        df_lanes['Van'] = df_lanes.Van.apply(
            lambda x: minutes2hhmm(roundup_to_nearest_5(x)))

        export_dataframe_as_csv(dataframe=df_lanes.copy(), csv_file_path=csv_file)

    except Exception:
        return {'error': log_exception(
            popup=False, remarks='Runtimes data could not extracted!')}
        

    return {'message': f'Runtimes data has been successfully exported as \n {csv_file}'}