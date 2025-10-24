from lion.orm.location_mapping import LocationMapper
from pyodbc import connect as pyodbc_connect
from lion.delta_suite.delta_logger import DELTA_LOGGER
from pandas import DataFrame, concat, read_sql
from lion.orm.orm_runtimes_mileages import RuntimesMileages
from lion.utils.is_null import is_null
from lion.runtimes.runtime_mileage_fetcher import UI_RUNTIMES_MILEAGES
from lion.utils.sqldb import SQLDB
from lion.ui.ui_params import UI_PARAMS
from lion.create_flask_app.create_app import LION_FLASK_APP


def read_runtimes():
    """
        Note that this function assumes that location mappings are already set up in the database.
        Reads runtime and mileage data from an Access database, processes and cleans the data, 
        and updates the 'DistanceTime' table in the target SQL database.
        The function performs the following steps:
        1. Connects to the Access database using the connection string from DELTA_LOGGER.
        2. Executes a SQL query to retrieve runtime and mileage data, grouping by relevant fields.
        3. Cleans and processes the data:
            - Strips and uppercases 'Origin' and 'Destination' fields.
            - Converts 'Distance' and 'DrivingTime' to integers, replacing nulls with 0.
            - Filters out records with non-positive 'Distance' or 'DrivingTime'.
            - Ensures minimum values for 'Distance' (1) and 'DrivingTime' (5).
            - Generates a unique record key for each row.
        4. Identifies records that already exist and deletes them from the target table.
        5. Appends the new/updated data to the 'DistanceTime' table in the SQL database.
        6. Resets the UI cache if the update is successful.
        7. Handles exceptions by logging errors and ensures the database connection is closed.
        Returns:
            bool: True if the operation completed successfully, False otherwise.
    """

    error_occurred = False
    df_runtimes = DataFrame()

    try:

        DELTA_LOGGER.log_statusbar(message='Updating runtimes ... ')
        access_conn = pyodbc_connect(DELTA_LOGGER.DELTA_DB_CON_STR)

        qry = """

            SELECT IIf([G410_DistanceTime].[VehicleType]='Truck',1,4) AS VehicleType, G410_DistanceTime.Origin, 
            G410_DistanceTime.Destination, '' AS Remarks, G410_DistanceTime.Distance, 
            G410_DistanceTime.[Driving time] as DrivingTime, G410_DistanceTime.[Break time] as BreakTime, 
            G410_DistanceTime.[Rest Time] as RestTime,  
            G410_DistanceTime.Drivers
            FROM G410_DistanceTime
            GROUP BY IIf([G410_DistanceTime].[VehicleType]='Truck',1,4), G410_DistanceTime.Origin, G410_DistanceTime.Destination, 
            '', G410_DistanceTime.Distance, G410_DistanceTime.[Driving time], G410_DistanceTime.[Break time], 
            G410_DistanceTime.[Rest Time], G410_DistanceTime.Drivers;

        """

        df_runtimes = read_sql(f"{qry}", access_conn)

        if df_runtimes.empty:
            raise Exception(f"No data found in {DELTA_LOGGER.DELTA_DB_CON_STR}.")

        df_runtimes['Origin'] = df_runtimes['Origin'].str.strip().str.upper()
        df_runtimes['Destination'] = df_runtimes['Destination'].str.strip().str.upper()
        df_runtimes['Distance'] = df_runtimes['Distance'].apply(lambda x: 0 if is_null(x) else int(x))
        df_runtimes['DrivingTime'] = df_runtimes['DrivingTime'].apply(lambda x: 0 if is_null(x) else int(x))

        df_runtimes = df_runtimes[(df_runtimes['Distance'] > 0) & (df_runtimes['DrivingTime'] > 0)].copy()

        df_runtimes['Distance'] = df_runtimes.Distance.apply(lambda x: 1 if x < 1 else x)
        df_runtimes['DrivingTime'] = df_runtimes.DrivingTime.apply(lambda x: 5 if x <= 5 else x)

        df_runtimes['group_name'] = LION_FLASK_APP.config['LION_USER_GROUP_NAME']

        df_runtimes = append_mapped_locs(df_runtimes)
        df_runtimes = exclude_existing_records(df_runtimes)

        if SQLDB.to_sql(dataFrame=df_runtimes,
                            destTableName='DistanceTime', ifExists='replace'):
            UI_RUNTIMES_MILEAGES.reset()
        else:
            raise Exception('Runtimes data was not updated!')

    except Exception:
        error_occurred = True
        DELTA_LOGGER.log_exception(f"Error processing {DELTA_LOGGER.DELTA_DB_CON_STR}")

    finally:
        if 'access_conn' in locals() and access_conn:
            access_conn.close()

    return not error_occurred

def exclude_existing_records(df_runtimes):

    try:

        _df_runtimes = df_runtimes.copy()
        existing_records = RuntimesMileages.get_existing_tuples()

        # Generate a unique record key for each row as a tuple of (Origin, Destination, VehicleType)
        new_records = list(
            zip(
            _df_runtimes['Origin'],
            _df_runtimes['Destination'],
            _df_runtimes['VehicleType']
            )
        )

        new_records = [rec for rec in new_records if rec not in existing_records]
        if not new_records:
            DELTA_LOGGER.log_statusbar(message='No new runtimes to process.')
            return DataFrame()
        
        _df_runtimes['flag'] = _df_runtimes.apply(lambda x: (x['Origin'], x['Destination'], x['VehicleType']) in new_records, axis=1)
        _df_runtimes = _df_runtimes[_df_runtimes['flag']].copy()
        _df_runtimes.drop(columns=['flag'], inplace=True)

        return _df_runtimes.copy()

    except Exception as e:
        DELTA_LOGGER.log_exception(f"Error running sync_runtimes_with_existing {str(e)}")
        return DataFrame()  # Return empty DataFrame on error


def append_mapped_locs(df_runtimes):

    try:

        DELTA_LOGGER.log_statusbar(message='Constructing runtimes data for mapped locations ... ')
        dct_mappings = LocationMapper.get_mappings()

        if not dct_mappings:
            return df_runtimes

        for loccode, mapped_loc in dct_mappings.items():

            if loccode == mapped_loc:
                continue  # skip self-mapping

            df_origin_matches = df_runtimes[df_runtimes['Origin'] == mapped_loc].copy()
            if not df_origin_matches.empty:
                df_origin_matches['Origin'] = loccode
                df_runtimes = concat([df_runtimes, df_origin_matches], ignore_index=True)

        for loccode, mapped_loc in dct_mappings.items():

            if loccode == mapped_loc:
                continue  # skip self-mapping

            df_dest_matches = df_runtimes[df_runtimes['Destination'] == mapped_loc].copy()
            if not df_dest_matches.empty:
                df_dest_matches['Destination'] = loccode
                df_runtimes = concat([df_runtimes, df_dest_matches], ignore_index=True)

        # Remove rows where Origin == Destination
        df_runtimes = df_runtimes[df_runtimes['Origin'] != df_runtimes['Destination']].copy()

    except Exception as e:
        DELTA_LOGGER.log_exception(f"Error appending mapped locations: {str(e)}")
        return DataFrame()  # Return empty DataFrame on error
    
    DELTA_LOGGER.log_statusbar(message='Appending mapped locations to the runtimes data ... completed.')
    return df_runtimes
