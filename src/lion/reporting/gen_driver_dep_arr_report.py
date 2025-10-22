from collections import defaultdict
from lion.config.paths import LION_FILES_PATH
from lion.shift_data.shift_data import UI_SHIFT_DATA
from lion.utils.df2csv import export_dataframe_as_csv
from lion.utils.minutes2hhmm import minutes2hhmm
from lion.utils.copy_file import copy_file
from lion.utils.safe_copy import secure_copy
from lion.utils.kill_file import kill_file
from lion.logger.exception_logger import log_exception
from pandas import DataFrame
from lion.orm.drivers_info import DriversInfo
from lion.utils.concat import concat
from lion.config.paths import LION_CONSOLIDATED_REPORT_PATH
from os import makedirs, path as os_path
from lion.orm.location import Location
from lion.orm.vehicle_type import VehicleType
from lion.utils.dfgroupby import groupby as df_groupby
from lion.utils.get_week_num import get_week_num
from lion.xl.write_excel import write_excel as xlwriter


class DepArrReport():

    def __init__(self):

        self.__dct_footprint = Location.to_dict()

        __locs = set(self.__dct_footprint)

        [self.__dct_footprint[__loc].update({'ctrl_depot': ''}) for __loc in __locs
         if self.__dct_footprint[__loc].get('ctrl_depot', '') == '' or
            self.__dct_footprint[__loc].get('ctrl_depot', '') == __loc]

        self.__set_hubs = set([loc for loc in set(
            self.__dct_footprint) if 'hub' in self.__dct_footprint[loc]['loc_type'].lower()])

        self.__set_customers = set([loc for loc in set(
            self.__dct_footprint) if 'customer' in self.__dct_footprint[loc]['loc_type'].lower()])

        self.__non_cust_locs = [
            lc for lc in __locs if lc not in self.__set_customers]

    @property
    def dump_directory(self):
        return self.__dump_directory

    @dump_directory.setter
    def dump_directory(self, x):
        self.__dump_directory = x

    @property
    def dct_optimal_drivers(self):
        return self.__dct_optimal_drivers

    def configure_base_data(self):

        try:
            self._dct_shift_running_on_weekday = DriversInfo.get_dct_shifts_per_weekday()

            if not UI_SHIFT_DATA:
                raise ValueError("Shift data cannot be NoneType!")

            self.__dct_optimal_drivers_base = UI_SHIFT_DATA.optimal_drivers
            self.__dict_all_movements_base = UI_SHIFT_DATA.dict_all_movements

            self.__dct_optimal_drivers_base.pop(1, None)
            self.__dct_optimal_drivers_base.pop(2, None)

        except Exception:
            log_exception(
                popup=False, remarks='Setting base data failed for reporting!')

    def gen_dep_arr_report(self, wkday='Mon'):

        try:

            __status_msg = ''

            self.__weekday = wkday
            dict_drivers = DriversInfo.to_dict()
            self.__dct_footprint = Location.to_dict()

            self.__dct_optimal_drivers = {}

            __dct_optimal_drivers_base = secure_copy({d: self.__dct_optimal_drivers_base[d] for d in self.__dct_optimal_drivers_base.keys()
                                                   if DriversInfo.shift_id_runs_on_weekday(shift_id=d, weekday=wkday)})

            if wkday != 'Mon':

                for shift_id in set(__dct_optimal_drivers_base):

                    dct_tour = __dct_optimal_drivers_base[shift_id]
                    dct_tour.refresh(target_weekday=wkday)

                    self.__dct_optimal_drivers[shift_id] = dct_tour
            else:
                self.__dct_optimal_drivers = secure_copy(
                    __dct_optimal_drivers_base)

            dict_all_movements = {}
            __dict_all_movements_base = secure_copy(
                self.__dict_all_movements_base)

            if wkday != 'Mon':

                for m in set(__dict_all_movements_base):

                    dct_m = __dict_all_movements_base[m]
                    dct_m.modify_dep_day(wkday=wkday)

                    dict_all_movements[m] = dct_m

            else:
                dict_all_movements = secure_copy(__dict_all_movements_base)

            __df_movements = DataFrame.from_dict(
                dict_all_movements, orient='index')

            __df_movements = __df_movements.loc[:, [
                'MovementID', 'From', 'To', 'DepDateTime',
                'ArrDateTime', 'DrivingTime', 'Dist']].copy()

            __df_driver_report = DataFrame(columns=[
                'Driver',
                'shift_id',
                'TourSequence',
                'MovementID',
                'vehicle',
                'From',
                'To',
                'DepDateTime',
                'ArrDateTime',
                'DrivingTime',
                'Dist',
                'Mile',
                'tu_loc',
                'total_dist_cost'
            ])

            __dct_report_day = defaultdict(str)
            __dct_shift_note = defaultdict(str)
            __dct_shift_remarks = defaultdict(str)

            for driver in set(self.__dct_optimal_drivers):

                try:

                    __dct_report_day[driver] = self.__dct_optimal_drivers[
                        driver]['dep_date_time'].strftime('%A')

                    __movs = self.__dct_optimal_drivers[driver]['list_movements']

                    if not __movs:
                        raise Exception(
                            f'Driver {driver} on {self.__weekday} does not have any movement!')

                    __dct_shift_note[driver] = self.__dct_optimal_drivers[driver].get(
                        'shift_note', '')

                    __dct_shift_remarks[driver] = self.__dct_optimal_drivers[
                        driver].get('remark', '')

                    __dct_movs_idx = {
                        m: idx + 1 for idx, m in enumerate(__movs)}

                    __df = __df_movements[
                        __df_movements.MovementID.isin(__movs)].copy()

                    __df['TourSequence'] = __df.MovementID.apply(
                        lambda x: __dct_movs_idx[x])

                    __df['vehicle'] = VehicleType.get_vehicle_name(
                        self.__dct_optimal_drivers[driver]['vehicle'])

                    __df['shift_id'] = driver
                    __df['Driver'] = dict_drivers.get(
                        driver, {}).get('shiftname', 'UnknownDriver')

                    __df['TotalMiles'] = int(
                        self.__dct_optimal_drivers[driver]['total_dist'] / 1.6 + 0.5)

                    __df['Mile'] = __df.Dist.apply(
                        lambda x: int(0.5 + x / 1.6))

                    __df['tu_loc'] = __df.MovementID.apply(
                        lambda x: dict_all_movements[x].get('tu', ''))

                    __df['DrivingTime'] = __df.DrivingTime.apply(
                        lambda x: "" + minutes2hhmm(x))

                    __df_driver_report = concat(
                        [__df_driver_report, __df])

                except Exception:
                    log_exception(
                        popup=False, remarks=f'{driver} was not processed!')

            __df_driver_report['Traffic Type'] = __df_driver_report.MovementID.apply(
                lambda x: dict_all_movements[x].get('TrafficType', ''))

            __df_driver_report.sort_values(
                by=['shift_id', 'TourSequence'], ascending=True, inplace=True)

            __df_driver_report = __df_driver_report.loc[:, [
                'Driver',
                'shift_id',
                'From',
                'To',
                'tu_loc',
                'DepDateTime',
                'ArrDateTime',
                'DrivingTime',
                'Mile',
                'Traffic Type'
            ]].copy()

            __df_driver_report.rename(
                columns={
                    'DrivingTime': 'Driving Time',
                    'Mile': 'Distance (miles)',
                    'tu_loc': 'TU Destination'
                },
                inplace=True
            )

            __df_driver_report['Driving Time'] = __df_driver_report['Driving Time'].apply(
                lambda x: "%s" % (x))

            __df_driver_report['remarks'] = __df_driver_report.shift_id.apply(
                lambda x: __dct_shift_remarks[x])

            __df_driver_report['notes'] = __df_driver_report.shift_id.apply(
                lambda x: __dct_shift_note[x])

            __df_driver_report['vehicle'] = __df_driver_report.shift_id.apply(
                lambda x: VehicleType.get_vehicle_name(self.__dct_optimal_drivers[x]['vehicle']))

            __df_driver_report['operator'] = __df_driver_report.shift_id.apply(
                lambda x: dict_drivers[x]['operator'])

            __df_driver_report['weekday'] = self.__weekday
            __df_driver_report['dep_day'] = __df_driver_report.shift_id.apply(
                lambda x: __dct_report_day[x])

            __set_all_locs = set(__df_driver_report.From.tolist())
            __set_all_locs.update(__df_driver_report.To.tolist())

            __df_driver_report['strDepDateTime'] = __df_driver_report.DepDateTime.apply(
                lambda x: x.strftime('%a %H:%M'))

            __df_driver_report['strArrDateTime'] = __df_driver_report.ArrDateTime.apply(
                lambda x: x.strftime('%a %H:%M'))

            export_dataframe_as_csv(dataframe=__df_driver_report.copy(), 
                                    csv_file_path=LION_CONSOLIDATED_REPORT_PATH / f'df_driver_report_{self.__weekday}.csv')

            __df_directs1 = __df_driver_report[__df_driver_report.From.isin(self.__set_hubs) &
                                               __df_driver_report.To.isin(self.__set_customers)].copy()

            __df_directs1['Category'] = 'Station customer'
            __df_directs1['LocationCode'] = __df_directs1['To'].apply(
                lambda toLoc: self.__dct_footprint.get(toLoc, {}).get('ctrl_depot', toLoc))

            __df_directs2 = __df_driver_report[
                __df_driver_report.To.isin(self.__set_hubs) &
                __df_driver_report.From.isin(self.__set_customers)].copy()

            __df_directs2['Category'] = 'Station customer'
            __df_directs2['LocationCode'] = __df_directs2['From'].apply(
                lambda fromLoc: self.__dct_footprint.get(fromLoc, {}).get('ctrl_depot', fromLoc))

            __df_directs = concat(
                [__df_directs1, __df_directs2])
            __df_directs = __df_directs[__df_directs.LocationCode != ''].copy()

            __df_directs['DepDateTime'] = __df_directs.DepDateTime.apply(
                lambda x: x.strftime('%a %H:%M')
            )

            __df_directs['ArrDateTime'] = __df_directs.ArrDateTime.apply(
                lambda x: x.strftime('%a %H:%M')
            )

            __df_directs['remarks'] = 'Customer directs'

            __df_departures = __df_driver_report.copy()
            __df_departures['Category'] = 'Departures'
            __df_departures['LocationCode'] = __df_departures.From.tolist()
            __df_departures.sort_values(
                by=['LocationCode', 'From', 'DepDateTime'], inplace=True)

            __df_arrivals = __df_driver_report.copy()
            __df_arrivals['Category'] = 'Arrivals'
            __df_arrivals['LocationCode'] = __df_arrivals.To.tolist()
            __df_arrivals.sort_values(
                by=['LocationCode', 'To', 'ArrDateTime'], inplace=True)

            __df1 = concat([__df_departures, __df_arrivals])

            __df1['DepDateTime'] = __df1.DepDateTime.apply(
                lambda x: x.strftime('%a %H:%M')
            )

            __df1['ArrDateTime'] = __df1.ArrDateTime.apply(
                lambda x: x.strftime('%a %H:%M')
            )

            __df1['remarks'] = ''

            __df = concat([__df1, __df_directs])

            columns_to_disp = ['LocationCode', 'Category', 'Driver', 'weekday', 'Start Point', 'End Point', 'TU Destination',
                               'Start Time', 'End Time', 'Driving Time', 'Distance (miles)', 'Traffic Type', 'vehicle', 'operator',
                               'dep_day', 'remarks']

            for __loc in self.__non_cust_locs:

                __df.rename(
                    columns={
                        'From': 'Start Point',
                        'To': 'End Point',
                        'DepDateTime': 'Start Time',
                        'ArrDateTime': 'End Time'
                    },
                    inplace=True
                )

                __df_loc = __df[__df.LocationCode == __loc].copy()

                if not __df_loc.empty:

                    __wb_file_path = self.__get_dep_arr_wb_path(
                        loc=__loc)

                    __df_loc = df_groupby(
                        df=__df_loc, groupby_cols=columns_to_disp)

                    xlwriter(df=__df_loc.copy(), sheetname='DeparturesArrivals',
                             xlpath=__wb_file_path, echo=False)

            __status_msg = 'Generating departure and arrivals has been successfully completed for %s!' % self.__weekday

        except Exception:
            __status_msg = f'Generating departure and arrivals report failed! {
                log_exception(False)}'

            return __status_msg

        return ''

    def __get_dep_arr_wb_path(self, loc):

        try:

            __loc_report_dir = '%s' % (self.__dump_directory)
            __loc_report_dir = os_path.join(
                __loc_report_dir, r'Driver plan %s' % (get_week_num()))

            makedirs(__loc_report_dir, exist_ok=True)

            __loc_report_dir = os_path.join(__loc_report_dir, f'{loc}')

            __filename = 'DepartureArrivals %s.%s.xlsx' % (
                loc, self.__weekday)

            makedirs(__loc_report_dir, exist_ok=True)
            __stn_wb_path = os_path.join(__loc_report_dir, __filename)

            kill_file(__stn_wb_path)
            copy_file(file_full_path=os_path.join(LION_FILES_PATH,
                                                  'DepartureArrivals.xlsx'),
                      dest_folder=__loc_report_dir, new_name=__filename)

            return __stn_wb_path

        except Exception:
            log_exception(popup=False)
            return ''
