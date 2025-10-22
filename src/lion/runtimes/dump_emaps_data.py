from lion.orm.location import Location
from lion.logger.exception_logger import log_exception
from .export import export_data

def generate_eMAPS_lanes(**dct_params):

    try:

        dct_footprint = Location.to_dict()
        LocStrings = dct_params.get('LocStrings', '').upper()
        locs_from = dct_params.get('LocsFrom', [])
        loc_to_types = dct_params.get('LocToTypes', [])

        
        if LocStrings != '':

            loc_strings = LocStrings.split(';')
            __locs_from = []
            __locs_to = []

            for s in loc_strings:
                loc1from, locto = s.strip().split('.')
                __locs_from.append(loc1from.strip())
                __locs_to.append(locto.strip())

            export_data(locs_from=__locs_from, locs_to=__locs_to)

        else:
            if loc_to_types:
                __locsTo = [x for x, v in dct_footprint.items() if v.get(
                    'loc_type', '') in loc_to_types and v.get('active', 1) == 1]
            else:
                __locsTo = list(dct_footprint)

            if not locs_from:
                locs_from = list(dct_footprint)

            return export_data(locs_from=locs_from, locs_to=__locsTo)

    except Exception:
        return {'error': log_exception(
            popup=False, remarks="Preparing eMaps input data failed!")}
