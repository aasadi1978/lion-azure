from os import listdir
from pathlib import Path
from pandas import DataFrame, concat, read_csv

from lion.config.paths import LION_CONSOLIDATED_REPORT_PATH
from lion.logger.exception_logger import log_exception
from lion.orm.location import Location
from lion.utils import df2csv
from lion.xl.write_excel import xlwriter


def generate_consolidated_driver_report(pr_cons_driver_rep_path: str | Path =  LION_CONSOLIDATED_REPORT_PATH):

    __df_driver_report = DataFrame()

    if isinstance(pr_cons_driver_rep_path, str):
        pr_cons_driver_rep_path = Path(pr_cons_driver_rep_path)

    try:

        __OK_csvfiles = ['df_driver_report_Mon.csv', 'df_driver_report_Tue.csv', 'df_driver_report_Wed.csv',
                            'df_driver_report_Thu.csv', 'df_driver_report_Fri.csv', 'df_driver_report_Sat.csv',
                            'df_driver_report_Sun.csv']

        __csvfiles = [f for f in listdir(
            pr_cons_driver_rep_path) if f in __OK_csvfiles]

        for __csvfile in __csvfiles:

            try:
                df = read_csv(pr_cons_driver_rep_path / __csvfile, low_memory=False)
            except Exception:
                df = DataFrame()
                log_exception(
                    popup=False, remarks=f"Reading {__csvfile} failed! ")

            if not df.empty:
                __df_driver_report = concat(
                    [__df_driver_report, df])

        df2csv.export_dataframe_as_csv(dataframe=__df_driver_report.copy(), csv_file_path=pr_cons_driver_rep_path / 'df_driver_report.csv')

        for clnm in ['remarks', 'notes', 'dep_day', 'DepDateTime', 'ArrDateTime']:
            if clnm in __df_driver_report.columns.tolist():
                __df_driver_report.drop(
                    columns=[clnm], axis=1, inplace=True)

        __df_driver_report.rename(columns=(
            {'strDepDateTime': 'Start Time',  'strArrDateTime': 'End Time'}), inplace=True)

    except Exception:
        log_exception(popup=True,
                        remarks='Generated consolidated driver report failed!')
        __df_driver_report = DataFrame()

    if not __df_driver_report.empty:

        try:
            __stn_wb_path = pr_cons_driver_rep_path / 'consolidated_driver_plan.xlsx'

            if 'From' in __df_driver_report.columns:

                __df_driver_report['From'] = __df_driver_report.From.apply(
                    lambda x: f"{x}/{Location.to_dict().get(x, {}).get('location_name', '')}")

                __df_driver_report['To'] = __df_driver_report.To.apply(
                    lambda x: f"{x}/{Location.to_dict().get(x, {}).get('location_name', '')}")

                __df_driver_report['TU Destination'] = __df_driver_report['TU Destination'].apply(
                    lambda x: '' if x == '' else f"{x}/{Location.to_dict().get(x, {}).get('location_name', '')}")

                __df_driver_report.rename(
                    columns={'From': 'Start Point', 'To': 'End Point'}, inplace=True)

            __cols = ['weekday', 'Driver', 'Start Point', 'End Point', 'TU Destination', 'Start Time', 'End Time',
                        'Driving Time', 'Distance (miles)', 'Traffic Type', 'vehicle', 'operator']

            xlwriter(df=__df_driver_report.loc[:, __cols].copy(), sheetname='DriverPlan',
                        xlpath=__stn_wb_path, echo=False)

        except Exception:
            log_exception(popup=True,
                            remarks='Could not generate consolidated_driver_plan.xlsx!')