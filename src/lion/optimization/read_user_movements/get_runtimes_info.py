from lion.optimization.opt_params import OPT_PARAMS
from lion.optimization.optimization_logger import OPT_LOGGER
from lion.runtimes.runtime_mileage_fetcher import UI_RUNTIMES_MILEAGES
from lion.utils.safe_copy import secure_copy


def get_temp_runtimes_info(orig, dest, vehicle, if_none={}):
    """
    Fetches and updates runtime and distance information for a given origin, destination, and vehicle.
    This function attempts to retrieve the runtime and distance between the specified origin and destination
    for the provided vehicle type using the UI_RUNTIMES_MILEAGES data source. If successful, it updates the
    OPT_PARAMS.DCT_LANE_RUNTIMES_INFO dictionary with the retrieved data and returns it. If the data cannot
    be retrieved, it logs the exception and returns None.
    Args:
        orig (str): The origin location identifier.
        dest (str): The destination location identifier.
        vehicle (Any): The vehicle type or identifier.
    Returns:
        dict or None: A dictionary containing 'dist' and 'runtime' if data is found, otherwise None.
    """

    try:

        dct_curr_info = secure_copy(OPT_PARAMS.DCT_LANE_RUNTIMES_INFO)
        runtime, dist = UI_RUNTIMES_MILEAGES.retrieve_travel_time_and_distance(
            orig=orig, dest=dest, vehicle=vehicle)

        if runtime and dist:
            dct_data = {'dist': dist, 'runtime': runtime}
            dct_curr_info.update(
                {'|'.join([orig, dest, str(vehicle)]): dct_data}
                )
            
            OPT_PARAMS.DCT_LANE_RUNTIMES_INFO = secure_copy(dct_curr_info)

            return dct_data

    except Exception:
        OPT_LOGGER.log_exception(popup=False,
                      remarks=f"No data runtimes data found for {'|'.join([orig, dest, str(vehicle)])}")
    
    return if_none