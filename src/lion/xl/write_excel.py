from lion.logger.exception_logger import log_exception
from openpyxl import load_workbook, Workbook, styles as openpyxl_styles
from openpyxl.utils.dataframe import dataframe_to_rows
from os import path
from lion.utils.popup_notifier import show_popup, show_error
from lion.utils.kill_file import kill_file
from lion.config.paths import LION_FILES_PATH
from shutil import copyfile
from pandas import DataFrame


def save_wb(wb, xlpath):

    try:
        wb.save(xlpath)
    except Exception as er_msg:
        err = log_exception(popup=False)
        if 'permission denied' in err.lower():
            show_error(
                f"The file {xlpath} seems to be opened by another user or application." +
                " Please clsoe the file and Press OK to continue!")

            wb.save(xlpath)

        else:
            show_error(
                f'The file {xlpath} was not saved successfully!\n{str(er_msg)}')


def copy_file(xlpath=''):

    if str(xlpath).lower().endswith('movements.xlsm'):
        while True:
            try:
                copyfile(path.join(LION_FILES_PATH,
                         'movements.xlsm'), xlpath)
                break
            except Exception as er_msg:
                err = log_exception(popup=False)
                if 'permission denied' in err.lower():
                    show_error(
                        f"The file {xlpath} seems to be opened by another user or application." +
                        " Please clsoe the file and Press OK to continue!")

                    copyfile(path.join(LION_FILES_PATH,
                                       'movements.xlsm'), xlpath)

                else:
                    show_error(
                        f'The file {xlpath} was not saved successfully!\n{str(er_msg)}')


def create_blank_wb(xlpath):

    try:
        kill_file(xlpath)
    except Exception:
        pass

    if str(xlpath).lower().endswith('movements.xlsm'):
        copy_file(xlpath)
    else:
        wb = Workbook()
        save_wb(wb=wb, xlpath=xlpath)

def write_excel(df, xlpath='movements.xlsm',
                sheetname='NoName', keep=False,
                header=True, echo=True):

    try:

        if not keep:
            create_blank_wb(xlpath)

        if str(xlpath).lower().endswith('.xlsm'):
            wb = load_workbook(xlpath, read_only=False, keep_vba=True)
        else:
            if not path.exists(xlpath):
                create_blank_wb(xlpath)

            wb = load_workbook(xlpath, read_only=False)

        if sheetname != '':

            if sheetname in wb.sheetnames:
                worksheet = wb[sheetname]
                for row in worksheet.iter_rows(min_row=1 + int(not header)):
                    for cell in row:
                        cell.value = None

            elif 'Sheet' in wb.sheetnames:
                s_sheet = wb['Sheet']
                s_sheet.title = sheetname
                worksheet = wb[sheetname]

            else:
                worksheet = wb.create_sheet(sheetname)

            rows = dataframe_to_rows(df, index=False, header=header)
            for r_idx, row in enumerate(rows, 1 + int(not header)):
                for c_idx, value in enumerate(row, 1):
                    worksheet.cell(row=r_idx,
                                   column=c_idx, value=value)

            __my_hdr_fill = openpyxl_styles.fills.PatternFill(
                patternType='solid', start_color='4D148C')

            # Formatting sheet
            for column in worksheet.columns:

                max_length = 0
                column = [cell for cell in column]

                for cell in column:
                    try:
                        cell.font = openpyxl_styles.Font(
                            name='FedEx Sans Cd', size=10)

                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass

                adjusted_width = (max_length + 5)
                worksheet.column_dimensions[column[0]
                                            .column_letter].width = adjusted_width

            worksheet.auto_filter.ref = worksheet.dimensions
            worksheet.freeze_panes = 'A2'

            for cell in worksheet["1:1"]:
                cell.fill = __my_hdr_fill
                cell.font = openpyxl_styles.Font(
                    color='FFFFFF', bold=True, name='FedEx Sans Cd', size=10)

            save_wb(wb=wb, xlpath=xlpath)

    except Exception:

        show_error(
            f'Creating {path.basename(xlpath)} failed! {log_exception()}')
        return False

    if echo:
        show_popup(
            f'Data has been successfully exported to {xlpath}!')

    return True

def xlwriter(df, xlpath='movements.xlsm',
                sheetname='NoName', keep=False,
                header=True, echo=True):
    
    return write_excel(df=df, xlpath=xlpath,
                sheetname=sheetname, keep=keep,
                header=header, echo=echo)


if __name__ == '__main__':

    
    dict_ = {'key 1': 'value 1', 'key 2': 'value 2', 'key 3': 'value 3'}
    write_excel(df=DataFrame([dict_]))
