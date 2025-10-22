from lion.runtimes.orm_runtimes_mileages import RuntimesMileages
from lion.utils.mile2km import mile2km
from lion.logger.exception_logger import log_exception
from lion.utils.roundup_to_nearest_5 import roundup_to_nearest_5


def update_user_defined_runtimes_mileages(**dct_params):

    try:

        bothdrct = dct_params.get('bothDir', True)

        lane = dct_params.get('loc_string', '')
        lane = lane.replace('->', '.')
        lane = lane.replace(';', '.')
        lane = lane.replace('>', '.')
        loc1, loc2 = lane.split('.')
        loc1 = loc1.upper()
        loc2 = loc2.upper()

        if bothdrct:
            loc_strings = ['%s.%s' % (loc1, loc2), '%s.%s' % (loc2, loc1)]
        else:
            loc_strings = ['%s.%s' % (loc1, loc2)]

        vhcle = dct_params.get('Vehicle', 'truck')
        vhcle_code: int = 1 if 'truck' in vhcle.lower() else 4

        dTime = 0 if dct_params.get('driving_time', 0) == '' else int(
            dct_params.get('driving_time', 0))
        dTime = 0 if dTime == 0 else roundup_to_nearest_5(dTime)

        miles = 0 if dct_params.get('miles', '') == '' else int(
            dct_params.get('miles', 0))

        status = 1
        for loc_string in loc_strings:

            loc1, loc2 = loc_string.split('.')
            dct_input = {'Origin': loc1,
                            'Destination': loc2,
                            'Distance': mile2km(miles),
                            'DrivingTime': dTime,
                            'VehicleType': vhcle_code}

            status *= int(RuntimesMileages.update(**dct_input))

    except Exception:
        _msg = f'Updating runtimes data failed. {log_exception(False)}'
        return {'error': _msg}
    
    return {'message': 'Changes have been successfully applied.'}
