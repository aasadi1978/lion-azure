
from collections import defaultdict
from lion.driver_loc.location_finder import LocationFinder
from lion.optimization.cluster_movements import cluster_movements
from lion.optimization.get_proposed_locs_for_movement import ProposedLocationsOptimizer
from lion.optimization.opt_params import OPT_PARAMS
from lion.optimization.optimization_logger import OPT_LOGGER
from pandas import DataFrame
from lion.utils.safe_copy import secure_copy


def pre_processing():

    """
    Performs preprocessing steps for movement optimization, including clustering movements by driver location,
    handling movements without recommendations, and identifying closest driver locations when needed.
    Steps performed:

    1. Initializes recommended movements per driver location and movements with no recommendation.
    2. If driver locations per lane are specified, clusters movements and creates a DataFrame summarizing
        the number of movements per location.

    3. If extended optimization is enabled or no driver locations per lane are specified, sets all movements
        to be optimized as having no recommendation and logs the configuration.

    4. If the number of top closest driver locations is specified, finds and assigns the closest driver
        locations for movements with no recommendation, raising an error if none are found.

    5. Logs relevant information throughout the process.

    6. Exports the movement count per driver location to a CSV file in the optimization temporary directory.

    Raises:
         ValueError: If the dictionary of closest driver locations is empty when required.

    """

    OPT_LOGGER.log_statusbar(message='PreProcessing and clustering movements ... ')

    try:

        dct_recommended_movements_per_driver_loc = defaultdict(set)
        set_movements_with_no_recom = set()
        df_mov_cnt = DataFrame(columns=['loc_code', 'n_movements'])

        if OPT_PARAMS.DCT_DRIVER_LOCS_PER_LANE:

            dct_recommended_movements_per_driver_loc, \
                set_movements_with_no_recom = cluster_movements()

            df_mov_cnt = DataFrame(
                [{'loc_code': k,
                    'n_movements': len(v),
                    'movements': '|'.join([str(m) for m in v])}
                    for k, v in dct_recommended_movements_per_driver_loc.items()]
            )

            OPT_PARAMS.DCT_RECOMMENDED_MOVEMENTS_PER_DRIVER_LOC = secure_copy(dct_recommended_movements_per_driver_loc)

        if OPT_PARAMS.RUN_EXTENDED_OPTIMIZATION or (
                not OPT_PARAMS.DCT_DRIVER_LOCS_PER_LANE):

            set_movements_with_no_recom = set(OPT_PARAMS.DCT_MOVEMENTS_TO_OPTIMIZE)

            OPT_LOGGER.log_info(
                message=f"We identified {len(set_movements_with_no_recom)} movements to be clustered!")

        dct_close_by_driver_locs = {}

        if OPT_PARAMS.N_TOP_CLOSEST_DRIVER_LOC:

            """
            If there are movements with no recommendation, the following code will find the top 
            OPT_PARAMS.N_TOP_CLOSEST_DRIVER_LOC closest driver locations
            """

            OPT_LOGGER.log_info(
                message=f'Parameter used: n_top_closest_driver_loc: {OPT_PARAMS.N_TOP_CLOSEST_DRIVER_LOC}')

            close_by_locs = LocationFinder()
            close_by_locs.read_location_params()
            close_by_locs.clear_dct_close_by_driver_locs()
            dct_close_by_driver_locs = close_by_locs.dct_close_by_driver_locs

            if not dct_close_by_driver_locs:
                raise ValueError('dct_close_by_driver_locs is empty!')

            OPT_PARAMS.DCT_CLOSE_BY_DRIVER_LOCS = dct_close_by_driver_locs
            del close_by_locs
        
            ProposedLocationsOptimizer().get_proposed_locs_for_movement()

            if not OPT_PARAMS.DCT_RECOMMENDED_MOVEMENTS_PER_DRIVER_LOC:
                raise Exception('dct_recommended_movements_per_driver_loc is empty!')

        else:
            OPT_LOGGER.log_info(
                message=f'N_TOP_CLOSEST_DRIVER_LOC: {OPT_PARAMS.N_TOP_CLOSEST_DRIVER_LOC}')

    except Exception as e:
        OPT_LOGGER.log_exception(f"Error during preprocessing: {str(e)}")
        
    try:
        if not df_mov_cnt.empty:
            df_mov_cnt.to_csv(OPT_PARAMS.OPTIMIZATION_TEMP_DIR / 'NumberOfAllocatedMovementsPerDriverLoc.csv', index=False)
    except Exception as e:
        OPT_LOGGER.log_info(
            message=f'NumberOfAllocatedMovementsPerDriverLoc could be created: {str(e)}')
