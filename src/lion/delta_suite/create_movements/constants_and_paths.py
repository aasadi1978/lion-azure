from lion.config import paths
from lion.delta_suite.build_tour import DELTA_LOGGER


TEMP_OUTPUT_DATA_DUMP = paths.LION_TEMP_DELTA_DATA_DUMP_PATH / 'Output'
TEMP_INPUT_DATA_DUMP = paths.LION_TEMP_DELTA_DATA_DUMP_PATH / 'Input'
TEMP_QUERIES_PATH = paths.LION_TEMP_DELTA_DATA_DUMP_PATH / 'Queries'

QRY_CREATEROUTESWITHSEQUENCE_FA_PATH = TEMP_QUERIES_PATH / 'CreateRoutesWithSequence.csv'

TEMP_OUTPUT_DATA_DUMP.mkdir(parents=True, exist_ok=True)
TEMP_INPUT_DATA_DUMP.mkdir(parents=True, exist_ok=True)
TEMP_QUERIES_PATH.mkdir(parents=True, exist_ok=True)

SCN = 'vF'

MOVEMENTS_NETWORK_EXCEL_PATH = TEMP_OUTPUT_DATA_DUMP / f"{SCN}" / f'MovementsFullNetwork_{SCN}.xlsx'
