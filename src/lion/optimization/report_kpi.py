from lion.config.libraries import OS_PATH
from lion.optimization.opt_params import OPT_PARAMS
from lion.optimization.optimization_logger import OPT_LOGGER
from lion.reporting.kpi_report import kpi_report
from lion.shift_data.shift_data import UI_SHIFT_DATA
from lion.logger.exception_logger import log_exception
from lion.utils.print2console import display_in_console
from lion.xl.write_excel import xlwriter


def dump_kpi_reports():

    try:

        dct_kpi_data = OPT_PARAMS.get('DCT_CURRENT_KPI', {})

        OPT_LOGGER.log_statusbar('Building KPI report after optimization ...')
        OPT_LOGGER.log_statusbar(message='creating kpi data ...')
        
        dct_kpi_data.update(kpi_report(weekdays=[OPT_PARAMS.OPTIMIZATION_REP_DAY]))
        
        OPT_LOGGER.log_statusbar('Exporting consolidated KPI report ...')

        dct_employed_drivers_count_per_loc = OPT_PARAMS.DCT_EMPLOYED_DRIVERS_COUNT_PER_LOC
        dct_subco_drivers_count_per_loc = OPT_PARAMS.DCT_SUBCO_DRIVERS_COUNT_PER_LOC

        __cntr = 0
        for scnname in dct_kpi_data.keys():

            __cntr += 1

            if __cntr == 1:

                df_kpi = dct_kpi_data[scnname]['df_kpi']
                df_kpi.rename(columns={'Value': scnname}, inplace=True)

                df_loc = dct_kpi_data[scnname]['df_loc']
                df_loc.rename(
                    columns={'TotalDrivers': scnname}, inplace=True)

                df_loc['Employed'] = df_loc.loc_code.apply(
                    lambda x: dct_employed_drivers_count_per_loc.get(x, 0))

                df_loc['Subco'] = df_loc.loc_code.apply(
                    lambda x: dct_subco_drivers_count_per_loc.get(x, 0))

            else:
                __dct = dct_kpi_data[scnname]['dct_kpi']
                df_kpi[scnname] = df_kpi.Vehicle_CType_KPI_Weekday.apply(
                    lambda x: __dct.get(x, 0))

                __dct = dct_kpi_data[scnname]['dct_loc']
                df_loc[scnname] = df_loc.loc_code.apply(
                    lambda x: __dct.get(x, 0))

                df_loc.sort_values(
                    by=[scnname], inplace=True, ascending=False)

                df_loc['AllEmployedUtilized'] = df_loc.apply(
                    lambda x: 'Yes' if x[scnname] >= x['Employed'] else 'No', axis=1)

                del __dct

        df_kpi.drop(['Vehicle_CType_KPI_Weekday', 'ScnName', 'INDX'],
                    axis=1, inplace=True)

        df_loc.drop(['ScnName', 'INDX'], axis=1, inplace=True)

        dct_kpi_data = {}

        xlwriter(df=df_kpi, sheetname='kpis',  xlpath=OS_PATH.join(
            OPT_PARAMS.OPTIMIZATION_TEMP_DIR, 'kpi-report.xlsx'), echo=False)

        xlwriter(df=df_loc, sheetname='LocDrivers',  xlpath=OS_PATH.join(
            OPT_PARAMS.OPTIMIZATION_TEMP_DIR, 'kpi-report.xlsx'), keep=True, echo=False)

        OPT_LOGGER.update(
            message='Appending unplanned movements to kpi-report ...')

        UI_SHIFT_DATA.extract_dct_unplanned_movements(
            xlFilepath=OS_PATH.join(OPT_PARAMS.OPTIMIZATION_TEMP_DIR, 'kpi-report.xlsx'))

        OPT_LOGGER.update(
            message=f'KPI reports have been successfully dumped in {OPT_PARAMS.OPTIMIZATION_TEMP_DIR}')

        display_in_console(obj=df_kpi, pause=False)
        display_in_console(obj=df_loc, pause=False)

        del df_kpi, df_loc

    except Exception:
        OPT_LOGGER.log_exception(message=log_exception(
            popup=False, remarks='Generating KPI reports failed!'))
