from lion.orm.changeover import Changeover
from lion.orm.location import Location
from lion.orm.location_mapping import LocationMapper
from lion.runtimes.orm_runtimes_mileages import RuntimesMileages

def clear_all():
    """
    Clear all caches used in the application.
    This function is called to ensure that all cached data is refreshed.
    """
    # Clear caches for various ORM models and utilities
    Location.dct_locations_cache.clear()
    LocationMapper.loc_map_cache.clear()
    RuntimesMileages.clear_cache()
    Changeover.clear_cache()
