from lion.delta_suite.delta_logger import DELTA_LOGGER
import pyodbc
import pandas as pd

"""
Developed and maintained by Matthieu Faber
Email: matthieu.faber@fedex.com"""

def get_volume_type(lh_network_code):
    if lh_network_code in ['Tsingle', 'Vsingle', 'Colocated']:
        return 'PayWeightAssignedVehicle', 'ConsAssignedVehicle'
    elif lh_network_code in ['Tloose', 'Tmix', 'Vloose', 'Vmix', 'Vloose_CDG']:
        return 'ConsAssignedVehicle', 'PayWeightAssignedVehicle'
    else:
        print('Unexpected LH network code to get volume type')
        return 'PayWeightAssignedVehicle', 'ConsAssignedVehicle'


def get_capacity(lh_network_code):
    if lh_network_code in ['Tsingle', 'Tmix']:
        return 26000
    elif lh_network_code == 'Tloose':
        return 32500
    elif lh_network_code in ['Vloose', 'Vloose_CDG']:
        return 5000
    elif lh_network_code in ['Vsingle', 'Vmix', 'Colocated']:
        return 4500
    else:
        print('Unexpected LH network code to get capacity')
        print(lh_network_code)
        return 26000


def get_route_id(x, flow_df):
    if x['Product'] in ['EU_EXP_PCL', 'IC_EXP_PCL']:
        return "SCE-" + x['ORIG'] + "-" + x['DEST'] + "-1-Main"
    elif x['Product'] in ['EU_EXP_PCL_2']:
        return "SCE-" + x['ORIG'] + "-" + x['DEST'] + "-4-Main"
    elif x['Product'] in ['EU_DOM_PCL_2']:
        return "SCE-" + x['ORIG'] + "-" + x['DEST'] + "-5-Main"
    elif len(flow_df[flow_df['RouteID'] == "SCE-" + x['ORIG'] + "-" + x['DEST'] + "-2-Main"]) > 0:
        return "SCE-" + x['ORIG'] + "-" + x['DEST'] + "-" + "2-Main"
    elif len(flow_df[flow_df['RouteID'] == "SCE-" + x['ORIG'] + "-" + x['DEST'] + "-3-Main"]) > 0:
        return "SCE-" + x['ORIG'] + "-" + x['DEST'] + "-" + "3-Main"
    else:
        print('Error getting route id: ' + "SCE-" + x['ORIG'] + "-" + x['DEST'] + "-" + x['Product'])


def get_service_requirement(db_path=DELTA_LOGGER.DELTA_DB_CON_STR):
    # Connection string
    conn_str = (
        r"Driver={Microsoft Access Driver (*.mdb, *.accdb)};"
        f"DBQ={db_path};"
    )

    # Establish the connection
    conn = pyodbc.connect(conn_str)

    # SQL query
    query_service_requirements = "SELECT * FROM G260_ServiceRequirements"

    # Load data into a DataFrame
    service_requirements = pd.read_sql(query_service_requirements, conn)

    # Close the connection
    conn.close()

    service_requirements['RouteID'] = "SCE-" + service_requirements.LocationFrom + "-" + \
                                      service_requirements.LocationTo + "-" + service_requirements.NSL + "-Main"

    service_requirements_dict = dict(zip(service_requirements.RouteID, service_requirements['NrOfDays']))

    return service_requirements_dict