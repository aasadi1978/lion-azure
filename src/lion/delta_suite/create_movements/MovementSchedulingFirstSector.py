import pandas as pd
import numpy as np

from lion.delta_suite.create_movements.SharedFunctionality import *
from lion.delta_suite.create_movements import constants_and_paths

"""
Developed and maintained by Matthieu Faber
Email: matthieu.faber@fedex.com"""


def process_first_sector_flow():

    df = parse_df()
    service_requirement = get_service_requirement()

    output_list = []
    output_list_mvt = []
    flow_assignment_list = []
    # Loop through the flow/sector list till it's empty and all flow is scheduled on movements
    unique_sectors = df['Output_RouteSectors+1_ServiceSectorID'].unique()
    for sector in unique_sectors:
        i = 0
        triggered_index = -1

        sector_df = df[df['Output_RouteSectors+1_ServiceSectorID'] == sector]
        sector_df.reset_index(drop=True, inplace=True)

        # Get the capacity of the vehicle for this particular movement (an error check could be created to see
        # whether there is an inconsistency in the network code for the different sectors)
        lh_network = sector_df.loc[0, 'Output_Links_LHNetworkCode']
        capacity = get_capacity(lh_network)

        # Check whether DeadWeight or PayWeight should be used
        volume_type, volume_type_other = get_volume_type(lh_network)
        # TEST ---------------------------
        # sector_df['CumulativeVolume'] = sector_df[volume_type].cumsum()
        # sector_df['VolumeMovementTrigger'] = (sector_df['CumulativeVolume'] // capacity) * capacity
        # sector_df['VolumeMovementTrigger2'] = sector_df['VolumeMovementTrigger'].diff().fillna(
        # sector_df['VolumeMovementTrigger'])
        # for index, row in unique_sector.iterrows()
        # -------------------------------
        while i <= max(sector_df.index):

            # Create a small version of the df with all flows of the specific sector that already arrived
            small_df = sector_df[triggered_index + 1:i + 1]

            # Check whether a movement should be scheduled. This is either because enough volume arrived, or no more
            # volume will arrive.
            volume_movement_triggered = sum(small_df[volume_type]) >= (capacity - 0.00001)
            service_movement_triggered = len(sector_df[i + 1:]) == 0

            if volume_movement_triggered or service_movement_triggered:
                # Initialize variables
                payweight_assigned_mvmnt = deadweight_assigned_mvmnt = cons_assigned_mvmnt = volume_assigned_mvmnt = 0
                triggered_index = i
                dep_time = small_df.at[max(small_df.index), 'MovementArr+ProcessTime']
                driving_time = small_df.at[max(small_df.index), 'Output_Links_Time'] / 1440
                # Loop through all elements and add
                for index, row in small_df.iterrows():
                    # Either remove (all volume scheduled) or adjust (part of flow still needs to be scheduled) flow
                    volume_added = 0
                    if (volume_assigned_mvmnt + row[volume_type]) <= (capacity + 0.00001):
                        payweight_assigned_OD, deadweight_assigned_OD, cons_assigned_OD = \
                           row['PayWeightAssignedVehicle'], row['DeadWeightAssignedVehicle'], row['ConsAssignedVehicle']
                        if max(small_df.index) == index and volume_movement_triggered:
                            if volume_type == 'PayWeightAssignedVehicle':
                                payweight_assigned_OD = capacity - payweight_assigned_mvmnt
                            else:
                                cons_assigned_OD = capacity - cons_assigned_mvmnt
                        volume_added += row[volume_type]
                    else:
                        volume_added_it = capacity - volume_assigned_mvmnt
                        volume_added += volume_added_it
                        # Adjust pieces and other volume type current flow
                        sector_df.at[index, volume_type] = row[volume_type] - volume_added_it
                        sector_df.at[index, volume_type_other] = (row[volume_type] - volume_added_it) / \
                                                                 row[volume_type] * row[volume_type_other]
                        sector_df.at[index, 'DeadWeightAssignedVehicle'] = (row[volume_type] -
                                        volume_added_it) / row[volume_type] * row['DeadWeightAssignedVehicle']
                        payweight_assigned_OD = volume_added_it if volume_type == 'PayWeightAssignedVehicle' else \
                            volume_added_it / row[volume_type] * row[volume_type_other]
                        cons_assigned_OD = volume_added_it if volume_type == 'ConsAssignedVehicle' else \
                            volume_added_it / row[volume_type] * row[volume_type_other]
                        deadweight_assigned_OD = volume_added_it / row[volume_type] * row['DeadWeightAssignedVehicle']
                        triggered_index -= 1
                        i -= 1

                    # Update volume on movement
                    volume_assigned_mvmnt += volume_added
                    payweight_assigned_mvmnt += payweight_assigned_OD
                    deadweight_assigned_mvmnt += deadweight_assigned_OD
                    cons_assigned_mvmnt += cons_assigned_OD

                    # Create a record for next phase and flow assignment
                    if row['Output_RouteSectors+1_1_ServiceSectorID'] != 0:
                        add_list = create_output_list_to_add(row, dep_time, driving_time, deadweight_assigned_OD,
                                                             payweight_assigned_OD, cons_assigned_OD)
                        output_list.append(add_list)
                    route_id = row['RouteID']
                    # if deadweight_assigned_OD < 0:
                    #     print('test')
                    flow_assignment_list.append([len(output_list_mvt) + 1, sector, route_id, route_id.split('-')[1],
                            route_id.split('-')[2], route_id.split('-')[3], payweight_assigned_OD,
                            deadweight_assigned_OD, cons_assigned_OD, dep_time, dep_time + driving_time,
                            service_requirement[route_id]])
                # Create a movement
                list_to_add = [len(output_list_mvt) + 1, sector, sector.split('-')[0], sector.split('-')[1],
                               sector.split('-')[2], dep_time, dep_time + driving_time, lh_network,
                               payweight_assigned_mvmnt, deadweight_assigned_mvmnt, cons_assigned_mvmnt,
                               service_movement_triggered, volume_movement_triggered]
                output_list_mvt.append(list_to_add)
                print(list_to_add)
            i += 1

    # Write output
    write_output(df, output_list, output_list_mvt, flow_assignment_list)


def parse_df():

    df = pd.read_csv(
        f'{constants_and_paths.TEMP_QUERIES_PATH}/Qry_CreateRoutesWithSequence_FA.csv',
        dtype={'PayWeightAssignedVehicle': np.float64, 'Weight': np.float64}, sep=';')

    df.dropna(subset=['Output_RouteSectors+1_ServiceSectorID'], inplace=True)
    df.fillna(0, inplace=True)

    # Split dataframe in a part where pallets need to be built and need to be adjusted
    df_filtered = df[df['Output_Links_LHNetworkCode'].isin(["Tsingle", "Vsingle", "Colocated"])].copy()
    df_remainder = df[~df['Output_Links_LHNetworkCode'].isin(["Tsingle", "Vsingle", "Colocated"])]

    # Add column when route is going via a hub
    df_filtered['ViaHub'] = df_filtered.apply(lambda x: check_route_via_hub(x['Output_RouteSectors+1_ServiceSectorID'],
                                                          x['Output_RouteSectors+1_1_ServiceSectorID'],
                                                          x['Output_RouteSectors+1_2_ServiceSectorID'],
                                                          x['Output_RouteSectors+1_3_ServiceSectorID'],
                                                          x['Output_RouteSectors+1_4_ServiceSectorID']), axis=1)
    df_filtered = df_filtered.sort_values(by=['MovementArr+ProcessTime'], ascending=[True])

    # Split filtered df in part for which route is going via a hub and part where it isn't
    df_via_hub = df_filtered[df_filtered['ViaHub'] != ""].copy()
    df_not_via_hub = df_filtered[df_filtered['ViaHub'] == ""].copy()

    df_not_via_hub = process_routes_not_via_hub(df_not_via_hub)
    df_via_hub = process_routes_via_hub(df_via_hub)

    df = pd.concat([df_via_hub, df_not_via_hub, df_remainder])

    df = df[df['PayWeightAssignedVehicle'] != 0]
    df.loc[:, 'payweight_modulo'] = df.loc[:, 'PayWeightAssignedVehicle'] % 999
    df = df.sort_values(by=['MovementArr+ProcessTime', 'payweight_modulo'], ascending=[True, False])
    df = df.drop('payweight_modulo', axis=1)
    df.reset_index(drop=True, inplace=True)
    df['Original_index'] = df.index
    df = df.sort_values(by=['MovementArr+ProcessTime', 'Original_index'],
                        ascending=[True, True])
    df.reset_index(drop=True, inplace=True)

    return df


def process_routes_via_hub(df):
    # Preprocess, correct payweight
    payweight_correction = df.groupby(['ViaHub'])[[
        'PayWeightAssignedVehicle', 'ConsAssignedVehicle']].sum().reset_index()
    payweight_correction['NewRounding'] = payweight_correction['ConsAssignedVehicle'].divide(
        1000).apply(np.ceil).multiply(1000)
    new_payweight_dict = dict(zip(payweight_correction.ViaHub, payweight_correction.NewRounding))
    old_cons_dict = dict(zip(payweight_correction.ViaHub, payweight_correction.ConsAssignedVehicle))
    df['PayWeightAssignedVehicle'] = df['ConsAssignedVehicle'] / df.ViaHub.map(old_cons_dict) * df.ViaHub.map(
        new_payweight_dict)
    df['Weight'] = df['RouteID'].map(df.groupby(['RouteID'])['PayWeightAssignedVehicle'].sum())

    # Step 1: Calculate total sum of PayWeightAssignedVehicle for each Batch-ViaHub combination
    df_sum = df.groupby(['ViaHub', 'Batch'])['PayWeightAssignedVehicle'].sum().reset_index()

    # Calculate cumulative weights within each RouteID
    df_sum['CumulativePayWeight'] = round(df_sum.groupby('ViaHub')['PayWeightAssignedVehicle'].cumsum(), 7)

    # Step 2: Floor the total sum to the nearest lower multiple of 1000
    df_sum['FinalPayWeight'] = (df_sum['CumulativePayWeight'] // 1000) * 1000

    df_sum['FinalPayWeight'] = np.where(df_sum['Batch'] == "B1", df_sum['FinalPayWeight'],
                                        df_sum['FinalPayWeight'].diff().fillna(
                                            df_sum['FinalPayWeight']))

    # Step 3: Merge the target payweight back to the original dataframe
    df = df.merge(df_sum[['ViaHub', 'Batch', 'FinalPayWeight']], on=['ViaHub', 'Batch'], how='left')

    # Step 4: Calculate the proportion of each RouteID's  relative to the total for that Batch-ViaHub combination
    df['Proportion'] = df['PayWeightAssignedVehicle'] / df.groupby(['ViaHub', 'Batch'])[
        'PayWeightAssignedVehicle'].transform('sum').fillna(0)

    # Step 5: Calculate the new payweight
    df['PayWeightAssignedVehicle'] = df['FinalPayWeight'] * df['Proportion']
    df['PayWeightAssignedVehicle'].fillna(0, inplace=True)

    # Step 6: Adjust DeadWeightAssignedVehicle and ConsAssignedVehicle
    df['DeadWeightAssignedVehicle'] = df['PayWeightAssignedVehicle'] / df['Weight'] * df['DeadWeight']
    df['ConsAssignedVehicle'] = df['PayWeightAssignedVehicle'] / df['Weight'] * df['Cons']

    df.drop(['Proportion', 'FinalPayWeight'], inplace=True, axis=1)

    return df


def process_routes_not_via_hub(df):
    # Process all routes that are not going to a hub
    df = df.sort_values(by=['RouteID', 'Batch']).reset_index(drop=True)

    #  Group by RouteID
    grouped = df.groupby('RouteID')

    # Calculate cumulative weights within each RouteID
    df['CumulativePayWeight'] = grouped['PayWeightAssignedVehicle'].cumsum()

    # Calculate the floor weight (multiples of 1000) for each cumulative value
    df['FinalPayWeight'] = (df['CumulativePayWeight'] // 1000) * 1000

    # Calculate the valid weight for each batch as the difference between floors
    df['PayWeightAssignedVehicle'] = np.where(df['Batch'] == "B1", df['FinalPayWeight'],
                                            df['FinalPayWeight'].diff().fillna(df['FinalPayWeight']))

    # Ensure weights are reset for each RouteID
    df['DeadWeightAssignedVehicle'] = df['PayWeightAssignedVehicle'] / df['Weight'] * df['DeadWeight']
    df['ConsAssignedVehicle'] = df['PayWeightAssignedVehicle'] / df['Weight'] * df['Cons']

    df.drop(['FinalPayWeight', 'CumulativePayWeight'], inplace=True, axis=1)

    return df


def check_route_via_hub(rs1, rs2, rs3, rs4, rs5):
    if rs1[:3] in ["LST", "MV9"]:
        return ""
    if rs2 != 0:
        if rs2[:3] in ["LST", "MV9"]:
            return rs1
    if rs3 != 0:
        if rs3[:3] in ["LST", "MV9"]:
            return rs1 + "|" + rs2
    if rs4 != 0:
        if rs4[:3] in ["LST", "MV9"]:
            return rs1 + "|" + rs2 + "|" + rs3
    if rs5 != 0:
        if rs5[:3] in ["LST", "MV9"]:
            return rs1 + "|" + rs2 + "|" + rs3 + "|" + rs4
    return ""


def get_processing_time(row):
    if row['Output_Links_LHNetworkCode'] == "Colocated":
        if row['Output_RouteSectors+1_ServiceSectorID'].split('-')[1][:-2] == \
                row['Output_RouteSectors+1_ServiceSectorID'].split('-')[0]:
            return 1
        else:
            return 0
    elif row['H660_Links_1_LHNetworkCode'] == "Vloose_CDG":
        return 30
    elif row['Output_RouteSectors+1_1_ServiceSectorID'][:3] in ["MV9", "LST"]:
        return 90
    else:
        return 45


def create_output_list_to_add(row, dep_time, driving_time, deadweight_assigned_OD, payweight_assigned_OD,
                              cons_assigned_OD):
    new_datetime = dep_time + driving_time + get_processing_time(row) / 1440
    add_list = [new_datetime, deadweight_assigned_OD, payweight_assigned_OD,
                cons_assigned_OD, row['RouteID'], row['Weight'], row['DeadWeight'],
                row['Cons'], row['LinkID'], row['Output_RouteSectors+1_RouteSequence'],
                row['Output_Links_LHNetworkCode']]
    add_list.extend(row.loc['Output_RouteSectors+1_1_RouteSequence':'Sector6_EndTime'].to_list())
    add_list.append(row['RouteID'].split('-')[2])
    return add_list


def write_output(df, output_list, output_list_mvt, flow_assignment_list):
    output_columns = df.columns[1:-2].drop(['Output_RouteSectors+1_ServiceSectorID', 'Output_Links_Time', 'StartTime',
                                            'EndTime'])
    output_columns = output_columns.to_list()
    output_columns.append('Dest')
    output_df = pd.DataFrame(output_list, columns=output_columns)

    # Group output_df and sum volume metrics
    output_df = output_df.groupby(output_df.columns.drop(['DeadWeightAssignedVehicle', 'ConsAssignedVehicle',
                                                          'PayWeightAssignedVehicle']).to_list()).sum().reset_index()
    output_df = output_df[output_df['Output_RouteSectors+1_1_ServiceSectorID'] != 0]
    output_df = output_df.reindex(columns=output_columns)

    output_mvt_df = pd.DataFrame(output_list_mvt, columns=['MovementID', 'ServiceSectorID', 'FromLocation',
                'ToLocation', 'VehicleType', 'DepTime', 'ArrTime', 'LHNetworkCode', 'SinglePallets', 'Pieces',
                'MixedPallets', 'ServiceMovement', 'VolumeMovement'])
    flow_df = pd.DataFrame(flow_assignment_list, columns=['MovementID', 'ServiceSectorID', 'RouteID', 'Origin',
        'Destination', 'NSL', 'SinglePallets', 'Pieces', 'MixedPallets', 'Departure time', 'Arrival time', 'NrOfDays'])
    output_mvt_df.to_csv(f'{constants_and_paths.TEMP_OUTPUT_DATA_DUMP}/' + constants_and_paths.SCN + '/MovementsFirstSector.csv', index=False)
    flow_df.to_csv(f'{constants_and_paths.TEMP_OUTPUT_DATA_DUMP}/' + constants_and_paths.SCN + '/FlowAssignmentFirstSector.csv', index=False)
    output_df.to_csv(f'{constants_and_paths.TEMP_OUTPUT_DATA_DUMP}/' + constants_and_paths.SCN + '/input_full_network.csv', index=False)


if __name__ == "__main__":
    process_first_sector_flow()
