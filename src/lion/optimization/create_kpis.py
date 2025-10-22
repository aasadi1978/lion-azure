from lion.optimization.opt_params import OPT_PARAMS
from lion.optimization.optimization_logger import OPT_LOGGER
from lion.optimization.print_info_in_console import to_console
from lion.reporting.kpi_report import kpi_report
from lion.utils.safe_copy import secure_copy


def create():

    try:

        OPT_LOGGER.log_statusbar('Building KPI report before optimization ...')
        dct_current_kpi = kpi_report(weekdays=[OPT_PARAMS.OPTIMIZATION_REP_DAY])
        OPT_PARAMS.update(DCT_CURRENT_KPI=secure_copy(dct_current_kpi))

        # Display some information in console
        to_console()

    except Exception as e:
        OPT_LOGGER.log_exception(f"preparing pre optimization kpis failed! {str(e)}")