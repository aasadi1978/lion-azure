from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.optimization.optimization_logger import OPT_LOGGER
from lion.optimization.read_user_movements.locstring2movs import locstring2changeover
from lion.optimization.orm.opt_movements import OptMovements
from lion.movement.movements_manager import UI_MOVEMENTS


def save_movements_on_opt_movements(df_movs):
    """
    Processes a DataFrame of user movements, transforms the data as needed, and saves the results to the database.
    This function iterates over each row in the provided DataFrame (`df_movs`). For rows representing changeovers (identified by a non-empty 'tu' field and a unique 'loc_string'), it generates changeover records using the `locstring2changeover` function. For other rows, it creates `OptMovements` objects. All generated records are added to the database session and committed.
    If the DataFrame is empty, or if an error occurs during processing or database operations, the function logs the exception and returns False.
    Args:
        df_movs (pandas.DataFrame): DataFrame containing movement data with required columns such as 'tu', 'loc_string', 'DepDay', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sun', 'TrafficType', and 'str_id'.
    Returns:
        bool: False if the DataFrame is empty or an exception occurs; otherwise, None.
    """

    if df_movs.empty:
        OPT_LOGGER.log_exception('No movements found in the file!')
        return False
    
    try:
        processed_changeovers = []
        list_records = []
        OptMovements.clear_all()

        for idx, row in df_movs.iterrows():

            if row['tu'] != '' and row['loc_string'] not in processed_changeovers:
                processed_changeovers.append(row['loc_string'])
                dep_day = row['DepDay']

                running_days = [dy for dy in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sun']
                                            if row[dy] in [1, '1', 'x', 'X']]

                co_records = locstring2changeover(loc_string=row['loc_string'],
                                                                    weekday=running_days[0],
                                                                    day=running_days[0],
                                                                    running_days=running_days,
                                                                    traffictype=row['TrafficType'],
                                                                    vehicle=row['VehicleType'],
                                                                    tu_dest=row['tu'],
                                                                    co_con_time=15,
                                                                    shift_id=0,
                                                                    dep_day=dep_day)

                list_records.extend(co_records)


            else:
                rcrd = OptMovements(
                                movement_id=UI_MOVEMENTS.get_new_loaded_movement_id(),
                                str_id=row['str_id'],
                                loc_string=row['loc_string'],
                                tu_dest=row['tu'],
                                mon=int(row['Mon']) == 1,
                                tue=int(row['Tue']) == 1,
                                wed=int(row['Wed']) == 1,
                                thu=int(row['Thu']) == 1,
                                fri=int(row['Fri']) == 1,
                                sun=int(row['Sun']) == 1)

                list_records.append(rcrd)

        LION_SQLALCHEMY_DB.session.add_all(list_records)
        LION_SQLALCHEMY_DB.session.commit()

    except Exception as err:
        LION_SQLALCHEMY_DB.session.rollback()
        OPT_LOGGER.log_exception(f'Error processing movements: {str(err)}')
        return False
