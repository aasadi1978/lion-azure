from os import path as os_path, makedirs
from shutil import rmtree
from lion.config.paths import LION_ARCGIS_PATH
from lion.logger.exception_logger import log_exception
from lion.xl.write_excel import write_excel as xlwriter
from lion.orm.location import Location


def export_data(locs_from, locs_to):
    try:

        rmtree(LION_ARCGIS_PATH)
        makedirs(LION_ARCGIS_PATH, exist_ok=True)

        df_origins = Location.coordinates(locs=locs_from)
        df_dest = Location.coordinates(locs=locs_to)

        xlwriter(df=df_origins, sheetname='origins',
                    xlpath=os_path.join(LION_ARCGIS_PATH, "Origins.xlsx"), echo=False)

        xlwriter(df=df_dest, sheetname='destinations',
                    xlpath=os_path.join(LION_ARCGIS_PATH, "Destinations.xlsx"), echo=False)

        del df_origins, df_dest

    except Exception:
        return {'error': log_exception(
            popup=False, remarks=f"Dumping eMAPS data failed!")}
    
    return {'message': f'eMAPS data has been dumped successfully to {LION_ARCGIS_PATH}'}