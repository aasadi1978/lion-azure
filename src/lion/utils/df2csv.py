import logging
from pathlib import Path
from pandas import DataFrame


def export_dataframe_as_csv(dataframe: DataFrame, csv_file_path: Path | str, FileDestination: Path | str = ''):

    try:
        if FileDestination:
            csv_file_path = Path(FileDestination) / Path(csv_file_path).name

        if not str(csv_file_path).lower().endswith('.csv'):
            csv_file_path = str(csv_file_path) + '.csv'

        dataframe.to_csv(Path(csv_file_path), index=False)

    except Exception:
        logging.error(f"Exporting dataframe to CSV failed: {Path(csv_file_path).name}")