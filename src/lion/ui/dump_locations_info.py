from datetime import datetime
from pandas import DataFrame
from lion.ui.split_fixed_unfixed_shifts import splitted_shifts_fixed_unfixed
from lion.logger.exception_logger import return_exception_code
from lion.orm.location import Location
from lion.config.paths import LION_LOGS_PATH
from lion.xl.write_excel import xlwriter


def dump_locs_data():

    _df_locs = DataFrame()

    try:

        _dct_footprint = Location.to_dict()
        _df_locs = DataFrame.from_dict(_dct_footprint, orient='index')
        _df_locs['active'] = _df_locs.active.apply(lambda x: int(x))

        # Load number of subco and employed drivers per location based on current schedule
        # Moreover, specify the number of fixed (out of scope) per location based on
        # OPT_PARAMS.SET_EXCLUDED_SHIFT_IDS
        _dct_loc_unfixed_employed_drivers, _dct_loc_fixed_employed_drivers, \
            _dct_loc_fixed_subco_drivers, \
            _dct_loc_unfixed_subco_drivers = splitted_shifts_fixed_unfixed()

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

            _df_locs['employed'] = _df_locs.apply(
                lambda x: sum(x[c] for c in ['un_fixed_employed', 'fixed_employed']), axis=1)

            _df_locs['subco'] = _df_locs.apply(
                lambda x: sum(x[c] for c in ['un_fixed_subco', 'fixed_subco']), axis=1)
        else:
            for c in ['un_fixed_employed', 'fixed_employed', 'fixed_subco', 'un_fixed_subco', 'employed', 'subco']:
                _df_locs[c] = 0

        del _dct_loc_unfixed_employed_drivers, _dct_loc_fixed_employed_drivers
        del _dct_loc_fixed_subco_drivers, _dct_loc_unfixed_subco_drivers

        _df_locs['remarks'] = ''

    except Exception:
        return return_exception_code(popup=False, remarks='Dumping locations info failed!')

    try:

        if _df_locs.empty:
            raise Exception('Loc Params data was empty!')

        _df_locs['Total_drivers'] = _df_locs.apply(
            lambda x: x['un_fixed_employed'] + x['un_fixed_subco'] + x['fixed_employed'] + x['fixed_subco'], axis=1)

        _df_locs['is_non_zero'] = _df_locs.Total_drivers.apply(lambda x: x > 0)
        _df_locs = _df_locs[_df_locs.Total_drivers > 0].copy()
        _df_locs['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        _df_locs.drop(columns=['is_non_zero'], axis=1, inplace=True)

        loc_columns_all = _df_locs.columns.tolist()
        loc_columns = ['loc_code', 'loc_type', 'active', 'live_stand_load', 'un_fixed_employed', 'country_code',
                       'fixed_employed', 'fixed_subco', 'un_fixed_subco', 'employed', 'subco']

        loc_columns_1 = [c for c in loc_columns_all if c not in loc_columns]
        loc_columns.extend(loc_columns_1)

        xlwriter(df=_df_locs[loc_columns].copy(),
                 sheetname='locations',
                 xlpath=LION_LOGS_PATH / 'Locations.xlsx', echo=False)

        del _df_locs

    except Exception:
        return return_exception_code(popup=False, remarks='Dumping locations info failed!')

    return {'code': 200, 'message': f'Locations info dumped successfully in\n{LION_LOGS_PATH}!'}
