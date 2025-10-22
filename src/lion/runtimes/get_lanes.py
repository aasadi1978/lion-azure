from lion.orm.location import Location
from lion.logger.exception_logger import log_exception
from pandas import DataFrame

def get_lanes_data(**dct_params):

    try:

        LocStrings = dct_params.get('LocStrings', '').upper()
        locs_from = dct_params.get('LocsFrom', [])
        loc_to_types = dct_params.get('LocToTypes', [])
        dict_footprint = Location.to_dict()

        df_lanes = DataFrame()

        if LocStrings != '':

            loc_strings = LocStrings.split(';')
            __locs_from = []
            __locs_to = []

            for s in loc_strings:
                loc1from, locto = s.strip().split('.')
                __locs_from.append(loc1from.strip())
                __locs_to.append(locto.strip())

            if __locs_from and __locs_to:
                df_lanes['Origin'] = __locs_from
                df_lanes['Destination'] = __locs_to
                
            return df_lanes

        else:
            if loc_to_types:
                __locsTo = [x for x, v in dict_footprint.items() if v.get(
                    'loc_type', '') in loc_to_types and v.get('active', 1) == 1]
            else:
                __locsTo = list(dict_footprint)

            if not locs_from:
                locs_from = list(dict_footprint)

            if locs_from and __locsTo:
                df_lanes['Origin'] = locs_from
                df_lanes['Destination'] = __locsTo
            
            return df_lanes

    except Exception:
        log_exception(
            popup=False, remarks="Preparing eGIS input data failed!")

        return DataFrame()
