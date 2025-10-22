COLUMNS = [
    'str_id',
    'loc_string',
    'TrafficType',
    'VehicleType',
    'InScope',
    'Comments',
    'From',
    'To', 
    'tu', 
    'DepDay',
    'DepTime',
    'Mon',
    'Tue',
    'Wed',
    'Thu',
    'Fri',
    'Sun']

REQUIRED_FIELDS = ['From',
                   'To',
                   'DepDay',
                   'DepTime'
                   ]

DEFAULT_VALUES = {
    'From': '',
    'To': '',
    'tu': '',
    'DepDay': 0,
    'DepTime': '0000',
    'str_id': '',
    'loc_string': '',
    'TrafficType': 'Express',
    'VehicleType': 'Tractor-trailer 2/3 Axles 80m3',
    'InScope': True,
    'Comments': '',
    'Mon': 1,
    'Tue': 1,
    'Wed': 1,
    'Thu': 1,
    'Fri': 1,
    'Sun': 0
}