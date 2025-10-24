from datetime import datetime
from lion.optimization.dump_dct_drivers_per_loc import dump_dct_drivers_per_location
from lion.optimization.optimization_logger import OPT_LOGGER
from lion.optimization.opt_params import OPT_PARAMS
from lion.orm.drivers_info import DriversInfo
from lion.orm.location import Location
from pandas import DataFrame
from lion.orm.resources import Resources
from lion.shift_data.shift_data import UI_SHIFT_DATA
from lion.optimization.optimization_logger import OPT_LOGGER
from lion.utils.sqldb import SqlDb
from lion.xl.write_excel import xlwriter
from os import path as os_path

def set_defaults():

    OPT_PARAMS.DCT_EMPLOYED_DRIVERS_COUNT_PER_LOC = {}
    OPT_PARAMS.DCT_SUBCO_DRIVERS_COUNT_PER_LOC = {}
    OPT_PARAMS.SET_DRIVER_LOCS = set()
    OPT_PARAMS.DCT_DRIVERS_COUNT_PER_LOC = {}

def extract_locs_data():
    """
    Extracts and processes location-related driver resource data for optimization and reporting.
    This function performs the following steps:
    1. Loads location data and converts it into a DataFrame.
    2. Retrieves the number of employed and subcontracted (subco) drivers per location, distinguishing between fixed and unfixed assignments.
    3. Incorporates user-provided resource information, calculating any extra employed or subco drivers per location.
    4. Prepares a summary DataFrame with resource details, including remarks, and saves it to a SQL database table ('loc_params').
    5. Calculates total drivers, filters out locations with zero drivers, and computes separate counts for employed and subco drivers.
    6. Exports the processed data to an Excel file for reporting.
    7. Updates global optimization parameters with the processed driver counts per location.
    8. Handles exceptions gracefully, logging errors and falling back to default values if necessary.
    Returns:
        pandas.DataFrame: The processed DataFrame containing location and driver resource information.
    """

    _df_locs = DataFrame()
    set_defaults()

    try:

        OPT_LOGGER.log_statusbar(
            message='Extracting locations and driver resources data for optimization...')
        
        _dct_footprint = Location.to_dict()
        _df_locs = DataFrame.from_dict(_dct_footprint, orient='index')
        _df_locs['active'] = _df_locs.active.apply(lambda x: int(x))

        # Load number of subco and employed drivers per location based on current schedule
        # Moreover, specify the number of fixed (out of scope) per location based on
        # OPT_PARAMS.SET_EXCLUDED_SHIFT_IDS
        _dct_loc_unfixed_employed_drivers, _dct_loc_fixed_employed_drivers, \
            _dct_loc_fixed_subco_drivers, \
            _dct_loc_unfixed_subco_drivers = dump_dct_drivers_per_location()

        # Load number of subco and employed drivers per location based user input
        _dct_employed_by_user = Resources.dct_employed_by_user()
        _dct_subco_by_user = Resources.dct_subco_by_user()


        if _dct_loc_unfixed_employed_drivers or _dct_loc_fixed_employed_drivers or \
            _dct_loc_fixed_subco_drivers or _dct_loc_unfixed_subco_drivers:

            # Prepare locations resource details data for optimization or report
            _df_locs['un_fixed_employed'] = _df_locs.loc_code.apply(
                lambda x: len(_dct_loc_unfixed_employed_drivers.get(x, [])))

            _df_locs['fixed_employed'] = _df_locs.loc_code.apply(
                lambda x: len(_dct_loc_fixed_employed_drivers.get(x, [])))

            _df_locs['fixed_subco'] = _df_locs.loc_code.apply(
                lambda x: len(_dct_loc_fixed_subco_drivers.get(x, [])))

            _df_locs['un_fixed_subco'] = _df_locs.loc_code.apply(
                lambda x: len(_dct_loc_unfixed_subco_drivers.get(x, [])))

            _df_locs['Employed'] = _df_locs.apply(
                lambda x: sum(x[c] for c in ['un_fixed_employed', 'fixed_employed']), axis=1)

            _df_locs['Subco'] = _df_locs.apply(
                lambda x: sum(x[c] for c in ['un_fixed_subco', 'fixed_subco']), axis=1)
        else:
            for c in ['un_fixed_employed', 'fixed_employed', 'fixed_subco', 'un_fixed_subco', 'Employed', 'Subco']:
                _df_locs[c] = 0

        if _dct_employed_by_user:
            _df_locs['extra_employed'] = _df_locs.apply(
                lambda x: _dct_employed_by_user.get(x['loc_code'], 0) - x['Employed'], axis=1)
        else:
            _df_locs['extra_employed'] = 0

        if _dct_subco_by_user:
            _df_locs['extra_subco'] = _df_locs.apply(
                lambda x: _dct_subco_by_user.get(x['loc_code'], 0) - x['Subco'], axis=1)
        else:
            _df_locs['extra_subco'] = 0

        del _dct_loc_unfixed_employed_drivers, _dct_loc_fixed_employed_drivers
        del _dct_loc_fixed_subco_drivers, _dct_loc_unfixed_subco_drivers
        del _dct_employed_by_user, _dct_subco_by_user

        _df_locs['remarks'] = 'Fixed includes fixed drivers, Non-Artic and Filtered-out shifts'

    except Exception:
        OPT_LOGGER.log_info(OPT_LOGGER.log_exception(popup=False, remarks='Extracting locations failed!'))
        set_defaults()
        return DataFrame()

    try:
        _opt_cols = ['loc_code', 'loc_type', 'active', 'un_fixed_employed',
                        'fixed_employed', 'fixed_subco', 'un_fixed_subco', 'extra_employed',
                        'extra_subco', 'remarks']

        _df_locs_opt = _df_locs.loc[:, _opt_cols].copy()
        _df_locs_opt['timestamp'] = datetime.now()

        SqlDb().to_sql(dataFrame=_df_locs_opt,
                            destTableName='loc_params', ifExists='replace')

    except Exception:
        OPT_LOGGER.log_exception(popup=True, remarks='Dumping locations failed!')
        return DataFrame()


    try:

        if _df_locs_opt.empty:
            raise Exception('Loc Params data was empty!')

        _df_locs_opt['Total_drivers'] = _df_locs_opt.apply(
            lambda x: x['un_fixed_employed'] + x['un_fixed_subco'] +
            x['fixed_employed'] + x['fixed_subco'] + x['extra_employed'] + x['extra_subco'], axis=1)

        _df_locs_opt['is_non_zero'] = _df_locs_opt.Total_drivers.apply(
            lambda x: x > 0)

        _df_locs_opt = _df_locs_opt[
            _df_locs_opt.Total_drivers > 0].copy()
        
        _df_locs_opt['SubcoDrivers'] = 0
        _df_locs_opt['EmployedDrivers'] = 0

        if not _df_locs_opt.empty:
           
            _df_locs_opt['SubcoDrivers'] = _df_locs_opt.apply(
                lambda x: max(0, int(x['fixed_subco'] + x[
                    'un_fixed_subco'] + x['extra_subco'])), axis=1)

            _df_locs_opt['EmployedDrivers'] = _df_locs_opt.apply(
                lambda x: max(0, int(x['fixed_employed'] + x[
                    'un_fixed_employed'] + x['extra_employed'])), axis=1)

        xlwriter(df=_df_locs_opt.copy(),
                    sheetname='params',  xlpath=os_path.join(
            OPT_PARAMS.OPTIMIZATION_TEMP_DIR, 'Location_params.xlsx'), echo=False)

        OPT_LOGGER.log_info(
            message=f'Location_params.xlsx has been dumped in {OPT_PARAMS.OPTIMIZATION_TEMP_DIR}')

        _df_locs_opt.set_index(['loc_code'], inplace=True)

        OPT_PARAMS.DCT_EMPLOYED_DRIVERS_COUNT_PER_LOC = _df_locs_opt.EmployedDrivers.to_dict()
        OPT_PARAMS.DCT_SUBCO_DRIVERS_COUNT_PER_LOC = _df_locs_opt.SubcoDrivers.to_dict()
        OPT_PARAMS.SET_DRIVER_LOCS = set(OPT_PARAMS.DCT_EMPLOYED_DRIVERS_COUNT_PER_LOC)
        OPT_PARAMS.SET_DRIVER_LOCS.update(set(OPT_PARAMS.DCT_SUBCO_DRIVERS_COUNT_PER_LOC))
        OPT_PARAMS.DCT_DRIVERS_COUNT_PER_LOC = _df_locs_opt.Total_drivers.to_dict()

        del _df_locs_opt

    except Exception:
        
        OPT_LOGGER.log_exception(
            popup=False,
            remarks='Reading location params failed. Employed drivers cnt set to default!')

        OPT_PARAMS.DCT_EMPLOYED_DRIVERS_COUNT_PER_LOC = UI_SHIFT_DATA.dct_employed_drivers_per_loc
        OPT_PARAMS.SET_DRIVER_LOCS = set([x for x, in DriversInfo.query.with_entities(
            DriversInfo.start_loc).all()])

        OPT_PARAMS.DCT_SUBCO_DRIVERS_COUNT_PER_LOC = {}