from lion.orm.location import Location
from lion.orm.location_mapping import LocationMapper
from pyodbc import connect as pyodbc_connect
from lion.config.libraries import OS_PATH
from lion.delta_suite.delta_logger import DELTA_LOGGER
from pandas import concat, isnull, read_sql
from lion.utils.sqldb import SQLDB
from lion.create_flask_app.create_app import LION_FLASK_APP

def validate_lang():
    """
    Validates the region by checking if the DELTA database connection string is set.
    Returns:
        bool: True if the connection string is valid, False otherwise.
    """

    try:
        access_conn = pyodbc_connect(DELTA_LOGGER.DELTA_DB_CON_STR)
        df_locs = read_sql("SELECT * FROM G300_Locations", access_conn)
        if df_locs.empty:
            DELTA_LOGGER.log_message("No locations found in the DELTA database.")
            return False
        
        cntry_codes = df_locs['CountryCode'].unique()
        if len(cntry_codes) > 1:
            DELTA_LOGGER.log_message("Multiple country codes found in the DELTA database.")
            return False
        if not cntry_codes[0]:
            DELTA_LOGGER.log_message("Country code is empty in the DELTA database.")
            return False

    except Exception as e:
        DELTA_LOGGER.log_exception(popup=False, remarks=str(e))
        return False
    finally:
        if 'access_conn' in locals() and access_conn:
            access_conn.close()

    return True

def read_locations():
    """
        Reads and processes location data from the DELTA database, mapping depot and hub codes, and storing results in SQL tables.
        Steps performed:
            1. Validates the region using DELTA locations table, country_code field.
            2. Connects to the DELTA database.
            3. Reads depot and hub data from G301_Depots and G302_Hubs tables.
            4. Standardizes and merges location code mappings, removes duplicates and self-mappings, and stores in 'loc_code_mapping'.
            5. Reads all locations from G300_Locations, standardizes codes, assigns location types ('Station', 'Hub', 'Customer'), and validates location names.
            6. Stores processed location data in the 'location' table.
            7. Logs errors and ensures database connection is closed.
        
        Returns:
            bool: True if successful, False if an error occurs.
    """


    error_occurred = False
    try:
        
        if not validate_lang():
            raise Exception(f"Region validation failed: {DELTA_LOGGER.DELTA_GLOBAL_ERROR}")
        
        access_conn = pyodbc_connect(DELTA_LOGGER.DELTA_DB_CON_STR)
        df_depots = read_sql("SELECT * FROM G301_Depots", access_conn)
        df_hubs = read_sql("SELECT * FROM G302_Hubs", access_conn)

        df_depots_loc_codes = df_depots[['DepotCode', 'LocationCode']].copy()
        df_hubs_loc_codes = df_hubs[['HubCode', 'LocationCode']].copy()
        df_depots_loc_codes.rename(columns={'LocationCode': 'loc_code', 'DepotCode': 'delta_code'}, inplace=True)
        df_hubs_loc_codes.rename(columns={'LocationCode': 'loc_code', 'HubCode': 'delta_code'}, inplace=True)

        df_loc_codes = concat([df_depots_loc_codes,  df_hubs_loc_codes])

        df_loc_codes['loc_code'] = df_loc_codes['loc_code'].str.strip().str.upper()
        df_loc_codes['delta_code'] = df_loc_codes['delta_code'].str.strip().str.upper()

        df_loc_codes = df_loc_codes.drop_duplicates(subset=['loc_code', 'delta_code'], keep='first')
        df_loc_codes = df_loc_codes[df_loc_codes.delta_code != df_loc_codes.loc_code].copy()

        df_loc_codes.rename(columns={'delta_code': 'loc_code', 'loc_code': 'mapping'}, inplace=True)

        existing_mappings = list(LocationMapper.get_mappings())
        if existing_mappings:
            df_loc_codes = df_loc_codes[~df_loc_codes.loc_code.isin(existing_mappings)].copy()

        if not df_loc_codes.empty:
            SQLDB.to_sql(dataFrame=df_loc_codes,
                                    destTableName='loc_code_mapping', ifExists='append')

        del df_loc_codes, df_depots_loc_codes, df_hubs_loc_codes

        list_depots = df_depots['LocationCode'].tolist()
        list_hubs = df_hubs['LocationCode'].tolist()

        qry = """

            SELECT 
            G300_Locations.LocationCode AS loc_code, 
            G300_Locations.UTCDiff AS utcdiff, 
            'Station' AS loc_type, 
            1 AS active, 
            G300_Locations.LocationDescription AS location_name, 
            G300_Locations.yCoordinate AS latitude, 
            G300_Locations.XCoordinate AS longitude, 
            G300_Locations.Town AS town, 
            G300_Locations.PostCode AS postcode, 
            G300_Locations.CountryCode AS country_code, 
            10 AS chgover_driving_min, 
            15 AS chgover_non_driving_min, 
            30 AS dep_debrief_time, 
            30 AS arr_debrief_time, 
            '' AS remarks, 
            25 AS turnaround_min, 
            G300_Locations.LocationCode AS ctrl_depot, 
            Date() AS update_on,
            'Stand Load' AS live_stand_load
            FROM G300_Locations
            GROUP BY 
            G300_Locations.LocationCode, 
            G300_Locations.UTCDiff, 
            'Station', 
            1, 
            G300_Locations.LocationDescription, 
            G300_Locations.yCoordinate,
            G300_Locations.XCoordinate, 
            G300_Locations.Town, 
            G300_Locations.PostCode, 
            G300_Locations.CountryCode, 
            10, 
            15, 
            30, 
            30, 
            '', 
            25, 
            G300_Locations.LocationCode, 
            Date(),
            'Stand Load';

        """

        _df_locs = read_sql(f"{qry}", access_conn)

        _df_locs['loc_code'] = _df_locs['loc_code'].str.strip().str.upper()
        _df_locs['loc_type'] = _df_locs['loc_code'].apply(lambda x: 
                                                            'Station' if x in list_depots else ('Hub' if x in list_hubs else 'Customer'))
        
        _df_locs['group_name'] = LION_FLASK_APP.config['LION_USER_GROUP_NAME']

        existing_locs = list(Location.to_dict())
        _df_locs = _df_locs[~_df_locs.loc_code.isin(existing_locs)].copy()

        if not _df_locs.empty:

            _df_locs['location_name'] = _df_locs.apply(
                lambda x: x['location_name'] if (not isnull(
                    x['location_name'])) and len(x['location_name']) > 5 else x['loc_type'], axis=1)
            
            SQLDB.to_sql(dataFrame=_df_locs,
                        destTableName='location', 
                        ifExists='replace')
        
        else:
            DELTA_LOGGER.log_message('No new location has been imported into the database!')

    except Exception:   
        DELTA_LOGGER.log_exception(
            f"Error processing {OS_PATH.basename(DELTA_LOGGER.DELTA_DB_CON_STR)}.")
        error_occurred = True

    finally:
        if 'access_conn' in locals() and access_conn:
            access_conn.close()

    if not error_occurred:
        return True
    else:
        return False