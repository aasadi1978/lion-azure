from lion.delta_suite.create_movements import constants_and_paths
import pandas as pd
import numpy as np
from lion.delta_suite.create_movements.SharedFunctionality import *

"""
Developed and maintained by Matthieu Faber
Email: matthieu.faber@fedex.com"""

DAYS_SIMULATED = 4  

def generate_movements():

    df = parse_df()
    service_requirement = get_service_requirement()

    # Correct the cons to be not higher than payweight. In practice this could have been te case when smalls are
    # stacked on top of pallets. However, this is interfering with the current Python logic to build pallets for
    # destinations at hubs.
    df = df.assign(ConsAssignedVehicle=lambda d: d[['PayWeightAssignedVehicle', 'ConsAssignedVehicle']].min(1))

    output_list = []
    flow_assignment_list = []
    df_next_index = len(df.index)
    i = 0
    # Loop through the flow/sector list till it's empty and all flow is scheduled on movements
    while len(df.index) > 0:
        # Create a small version of the df with all flows of the specific sector that already arrived
        small_df, sector, service_time = get_small_df(df, i)

        # Get the LH network
        lh_network = small_df.loc[0, 'H660_Links_1_LHNetworkCode']

        # Get the capacity of the vehicle for this particular movement (an error check could be created to see whether
        # there is an inconsistency in the network code for the different sectors)
        capacity = get_capacity(lh_network)

        # Check whether DeadWeight or PayWeight should be used
        volume_type, volume_type_other = get_volume_type(lh_network)

        # Create a small version of the df to check whether any volume is still to arrive for the specific sector
        sm_triggered = sm_trigger(df, sector, service_time, i)

        grouped_small_df = []
        # Sort on destination level when volume goes from hub to platform
        if sector[:3] in ["MV9", "LST"] and volume_type == 'PayWeightAssignedVehicle':
            # Adjust small_df and create grouped_small_df to process hub to platform movement
            vm_triggered, grouped_small_df, small_df = check_h2p(sm_triggered, small_df, capacity)
        else:
            # Check whether a movement should be scheduled. This is either because enough volume arrived, or no more
            # volume will arrive.
            vm_triggered = sum(small_df[volume_type]) >= (capacity - 0.00001)

        if vm_triggered or sm_triggered:
            # Initialize variables
            payweight_assigned_mvmnt = deadweight_assigned_mvmnt = cons_assigned_mvmnt = volume_assigned_mvmnt = \
                remove_count = not_removed = 0
            dep_time = small_df.at[max(small_df.index), 'MovementArr+ProcessTime']
            driving_time = small_df.at[max(small_df.index), 'H660_Links_1_Time'] / 1440

            # Either remove (all volume scheduled) or adjust (part of flow still needs to be scheduled) flow
            for index, row in small_df.iterrows():
                volume_added = 0
                # Check how much can be added based on grouped df when sector from hub to platform
                volume_to_add = row[volume_type]
                if len(grouped_small_df) > 0:
                    dest = row['Dest']
                    volume_to_add = min(grouped_small_df[dest] - grouped_small_df[dest + 'Counter'],
                        row[volume_type]) if grouped_small_df[dest] > grouped_small_df[dest + 'Counter'] else 0
                if volume_to_add > 0:
                    # Create new record in df
                    if row['Output_RouteSectors+1_2_RouteSequence'] != 0:
                        df, df_next_index = create_new_record(df, row, df_next_index, dep_time + driving_time)
                    # If all volume from the row can fit in the vehicle, schedule it and remove flow
                    volume_ratio = 1
                    if (volume_assigned_mvmnt + volume_to_add) <= (capacity + 0.00001) and \
                            abs(volume_to_add - row[volume_type]) < 0.0000001:
                        payweight_assigned_mvmnt += row['PayWeightAssignedVehicle']
                        deadweight_assigned_mvmnt += row['DeadWeightAssignedVehicle']
                        cons_assigned_mvmnt += row['ConsAssignedVehicle']
                        volume_added += row[volume_type]
                        volume_assigned_mvmnt += volume_added
                        df.drop(row['index'], inplace=True)
                        remove_count += 1
                    # If part of the volume from the row can fit in the vehicle, schedule it and adjust the
                    else:
                        not_removed += 1
                        # Check how much volume can still be added to the vehicle
                        volume_added = min(capacity - volume_assigned_mvmnt, volume_to_add)
                        volume_ratio = volume_added / row[volume_type]
                        # Adjust pieces and other volume type current flow
                        df.at[row['index'], volume_type] = row[volume_type] - volume_added
                        df.at[row['index'], volume_type_other] = (row[volume_type] - volume_added) / \
                            row[volume_type] * row[volume_type_other]
                        df.at[row['index'], 'DeadWeightAssignedVehicle'] = (row[volume_type] - volume_added) \
                            / row[volume_type] * row['DeadWeightAssignedVehicle']
                        payweight_assigned_mvmnt += volume_added if volume_type == 'PayWeightAssignedVehicle' \
                            else volume_ratio * row[volume_type_other]
                        cons_assigned_mvmnt += volume_added if volume_type == 'ConsAssignedVehicle' \
                            else volume_ratio * row[volume_type_other]
                        deadweight_assigned_mvmnt += volume_ratio * row['DeadWeightAssignedVehicle']
                        # Adjust pieces and other volume type next sector (only if there is a next sector)
                        if row['Output_RouteSectors+1_2_RouteSequence'] != 0 and volume_added > 0:
                            df.at[df_next_index - 1, volume_type] = volume_added
                            df.at[df_next_index - 1, volume_type_other] = volume_ratio * row[volume_type_other]
                            df.at[df_next_index - 1, 'DeadWeightAssignedVehicle'] = volume_ratio * \
                                                                                    row['DeadWeightAssignedVehicle']
                        volume_assigned_mvmnt += volume_added
                    if len(grouped_small_df) > 0:
                        grouped_small_df[row['Dest'] + 'Counter'] += volume_added

                    # Add connection from flow to movement to flow assignment list
                    route_id = row['RouteID']
                    flow_assignment_list.append([len(output_list) + 1, sector,  route_id, route_id.split('-')[1],
                        route_id.split('-')[2], route_id.split('-')[3], volume_ratio * row['PayWeightAssignedVehicle'],
                        volume_ratio * row['DeadWeightAssignedVehicle'], volume_ratio * row['ConsAssignedVehicle'],
                        dep_time, dep_time + driving_time, service_requirement[route_id]])

            # create a movement
            list_to_add = [len(output_list) + 1, sector, sector.split('-')[0], sector.split('-')[1],
                            sector.split('-')[2], dep_time, dep_time + driving_time, lh_network,
                            round(payweight_assigned_mvmnt, 5), round(deadweight_assigned_mvmnt, 5),
                            round(cons_assigned_mvmnt, 5), sm_triggered, vm_triggered]
            output_list.append(list_to_add)

            # sort again
            df = df.sort_values(by=['MovementArr+ProcessTime', 'Original_index'],
                                ascending=[True, True])
            df.reset_index(drop=True, inplace=True)

            # Set i to correct value
            if not_removed == 0:
                i -= (remove_count + 1)
                i = max(i, -1)
            else:
                test = df.where(df['Output_RouteSectors+1_1_ServiceSectorID'] == sector).dropna(
                    subset=['Output_RouteSectors+1_1_ServiceSectorID'])
                i = test.index[0] - 1 if len(test.index) > 0 else -1
        i += 1

    # Create pandas df from output lists
    movements_df = pd.DataFrame(output_list, columns=['MovementID', 'ServiceSectorID', 'FromLocation',
                'ToLocation', 'VehicleType', 'DepTime', 'ArrTime', 'LHNetworkCode', 'SinglePallets', 'Pieces',
                'MixedPallets', 'ServiceMovement', 'VolumeMovement'])
    flow_df = pd.DataFrame(flow_assignment_list, columns=['MovementID', 'ServiceSectorID', 'RouteID', 'Origin',
        'Destination', 'NSL', 'SinglePallets', 'Pieces', 'MixedPallets', 'Departure time', 'Arrival time', 'NrOfDays'])

    # Write output
    write_output(movements_df, flow_df)


def check_h2p(sm_triggered, small_df, capacity):
    vm_triggered = False
    if sm_triggered:
        grouped_small_df = small_df.groupby(['Dest'])['ConsAssignedVehicle'].sum().divide(
            1000).apply(np.ceil).multiply(1000)
    else:
        grouped_small_df = small_df.groupby(['Dest'])['ConsAssignedVehicle'].sum().divide(
            1000).apply(np.floor).multiply(1000)
        vm_triggered = sum(grouped_small_df) >= (capacity - 0.00001)

    if sm_triggered or vm_triggered:
        # Select a set of destinations to be added to the movement. It could be the case there are more
        # destinations than capacity (in case of a service movement). In case of a volume movement there are
        # not more destinations, but per destination you'll potentially have more volume than could fit on
        # the number of pallets assigned to the destination.
        counter = 0
        dest_list = []
        for dest in grouped_small_df.index:
            to_add = min(grouped_small_df[dest], max(capacity - counter, 0))
            grouped_small_df[dest] = to_add
            counter += min(grouped_small_df[dest], capacity - counter)
            if to_add > 0:
                dest_list.append(dest)
        small_df = small_df[small_df.Dest.isin(dest_list)].reset_index(drop=True)
        grouped_small_df = grouped_small_df[grouped_small_df > 0]

        # Get the actual mixed pallets to be added to the movement to determine payweight correction
        payweight_correction_df = small_df.groupby(['Dest'])['ConsAssignedVehicle'].sum()
        for dest in grouped_small_df.index:
            grouped_small_df[dest + 'PayWeightCorrection'] = grouped_small_df[dest] / \
                                                    min(payweight_correction_df[dest], grouped_small_df[dest])
            grouped_small_df[dest + 'Counter'] = 0

        # Map 'Dest' values to the corresponding 'PayWeightCorrection' values
        payweight_correction_map = grouped_small_df[small_df['Dest'] + 'PayWeightCorrection'].values

        # Calculate and assign 'PayWeightAssignedVehicle'
        small_df['PayWeightAssignedVehicle'] = small_df['ConsAssignedVehicle'] * payweight_correction_map

    return vm_triggered, grouped_small_df, small_df


def create_new_record(df, row, df_next_index, arr_time):
    df = pd.concat([df, df.iloc[[0], :]])
    index_list = df.index.tolist()
    index_list[len(df.index) - 1] = df_next_index
    df.index = index_list
    if row['H660_Links_2_LHNetworkCode'] == "Colocated":
        if row['Output_RouteSectors+1_2_ServiceSectorID'].split('-')[1][:-2] == \
                row['Output_RouteSectors+1_2_ServiceSectorID'].split('-')[0]:
            processing_time = 1
        else:
            processing_time = 0
    elif row['H660_Links_1_LHNetworkCode'] == "Vloose_CDG" and \
            row['Output_RouteSectors+1_2_ServiceSectorID'][:3] == "CDG":
        return 30
    elif row['Output_RouteSectors+1_2_ServiceSectorID'][:3] in ["MV9", "LST"]:
        processing_time = 90
    else:
        processing_time = 45

    df.iloc[-1, 0] = arr_time + processing_time / 1440
    # Copy info and shift sectors
    df.iloc[-1, 1:10] = row.iloc[2:11].values
    df.iloc[-1, 11:len(row) - 9] = row.iloc[18:len(row) - 2].values
    df.iloc[-1, len(row) - 9:len(row) - 3] = 0
    df.iloc[-1, len(row) - 3] = row.iloc[len(row)-2]
    df.iloc[-1, len(row) - 2] = df_next_index
    df_next_index += 1

    return df, df_next_index


def get_small_df(df, i):
    small_df = df[:i + 1]
    small_df.reset_index(inplace=True)
    sector = small_df.at[len(small_df.index) - 1, 'Output_RouteSectors+1_1_ServiceSectorID']
    small_df = small_df[small_df['Output_RouteSectors+1_1_ServiceSectorID'] == sector]
    small_df.reset_index(inplace=True, drop=True)
    service_time = small_df.at[len(small_df.index) - 1, 'Sector2_StartTime']
    small_df = small_df[abs((small_df['Sector2_StartTime'] - service_time)) < 0.0000001]
    small_df.reset_index(drop=True, inplace=True)

    return small_df, sector, service_time


def parse_df():
    df_1_day = pd.read_csv(f'{constants_and_paths.TEMP_OUTPUT_DATA_DUMP}/' + constants_and_paths.SCN + '/input_full_network.csv')
    df_1_day_copy = df_1_day.copy()
    df = df_1_day
    if DAYS_SIMULATED > 1:
        for i in range(DAYS_SIMULATED - 1):
            df_1_day = df_1_day_copy.copy()
            df_1_day['MovementArr+ProcessTime'] += (i + 1)
            for j in range(2, 7):
                start_time_str = 'Sector' + str(j) + '_StartTime'
                end_time_str = 'Sector' + str(j) + '_EndTime'
                df_1_day[start_time_str] += (i + 1)
                df_1_day[end_time_str] += (i + 1)
            df = pd.concat([df, df_1_day])

    df = df[df['Output_RouteSectors+1_1_ServiceSectorID'] != 0]
    df['payweight_modulo'] = df['PayWeightAssignedVehicle'] % 999
    df = df.sort_values(by=['MovementArr+ProcessTime', 'payweight_modulo'], ascending=[True, False])
    df.drop('payweight_modulo', inplace=True, axis=1)
    df.reset_index(drop=True, inplace=True)
    df['Original_index'] = df.index
    df = df.sort_values(by=['MovementArr+ProcessTime', 'Original_index'], ascending=[True, True])
    df.reset_index(drop=True, inplace=True)

    return df


def sm_trigger(df, sector, service_time, i):
    sm_check_df = df[i + 1:]
    # Define mappings for sectors and times
    sector_columns = ['Output_RouteSectors+1_1_ServiceSectorID', 'Output_RouteSectors+1_2_ServiceSectorID',
        'Output_RouteSectors+1_3_ServiceSectorID', 'Output_RouteSectors+1_4_ServiceSectorID']
    start_time_columns = ['Sector2_StartTime', 'Sector3_StartTime', 'Sector4_StartTime', 'Sector5_StartTime']

    for sector_col, time_col in zip(sector_columns, start_time_columns):
        mask = ((sm_check_df[sector_col] == sector) &
                (abs(sm_check_df[time_col] - service_time) < 0.0000001))
        if mask.any():
            return False  # Movement exists for this sector

    for sector_col, time_col in zip(sector_columns[1:], start_time_columns[1:]):
        mask = ((df[sector_col] == sector) &
                (abs(df[time_col] - service_time) < 0.0000001))
        if mask.any():
            return False  # Movement exists for this sector

    return True


def write_output(movements_df, flow_df):
    # Read first sector movement df
    movements_first_sector = pd.read_csv(f'{constants_and_paths.TEMP_OUTPUT_DATA_DUMP}/' + constants_and_paths.SCN + '/MovementsFirstSector.csv')
    flow_assignment_first_sector = pd.read_csv(f'{constants_and_paths.TEMP_OUTPUT_DATA_DUMP}/' + constants_and_paths.SCN + '/FlowAssignmentFirstSector.csv')

    # Multiply first sector movements and adjust arrival and departure days and movement id
    for i in range(DAYS_SIMULATED):
        movements_1_day = movements_first_sector.copy()
        flows_1_day = flow_assignment_first_sector.copy()
        movements_1_day['DepTime'] += i
        movements_1_day['ArrTime'] += i
        movements_1_day['MovementID'] += (i + 1) * 10000
        flows_1_day['MovementID'] += (i + 1) * 10000
        flows_1_day['Departure time'] += i
        flows_1_day['Arrival time'] += i
        movements_df = pd.concat([movements_df, movements_1_day])
        flow_df = pd.concat([flow_df, flows_1_day])

    # Limit to fewer days
    if DAYS_SIMULATED > 1:
        movements_df = movements_df[(movements_df['DepTime'] >= (DAYS_SIMULATED - 1)) &
                                    (movements_df['DepTime'] < DAYS_SIMULATED)]
        flow_df = flow_df[flow_df['MovementID'].isin(movements_df['MovementID'].unique())]

    flow_df = flow_df.groupby(['MovementID', 'ServiceSectorID', 'RouteID', 'Origin',
                               'Destination', 'NSL', 'Departure time', 'Arrival time', 'NrOfDays']).sum().reset_index()

    # Create next service sector and next departure time
    flow_df['Arrival_Location'] = flow_df['ServiceSectorID'].str.split('-').str[1]
    flow_df['Departure_Location'] = flow_df['ServiceSectorID'].str.split('-').str[0]

    # Apply the function row-wise
    flow_df[['Next_ServiceSector', 'Next_Departure_Time']] = \
        flow_df.apply(lambda row: pd.Series(find_next_service(row, flow_df)), axis=1)
    flow_df[['PreviousServiceSectorID', 'PreviousArrivalTime']] = \
        flow_df.apply(lambda row: pd.Series(find_previous_service(row, flow_df)), axis=1)
    flow_df.drop(['Arrival_Location', 'Departure_Location'], inplace=True, axis=1)

    last_sector_per_routeid = flow_df[flow_df['ServiceSectorID'].str.split('-').str[1] ==
                                flow_df['Destination']].groupby(['RouteID', 'ServiceSectorID']).sum().reset_index()
    flow_df['LastSector'] = flow_df.RouteID.map(dict(zip(last_sector_per_routeid.RouteID,
                                                         last_sector_per_routeid.ServiceSectorID)))
    flow_df['TopOffPlatform'] = np.where(np.logical_and(
        (flow_df['ServiceSectorID'].str.split('-').str[1] == flow_df['LastSector'].str.split('-').str[0]),
        (~flow_df['ServiceSectorID'].str.split('-').str[1].isin(["LST_h", "MV9_h"]))),
        flow_df['LastSector'].str.split('-').str[0], "")

    flow_df.drop('LastSector', inplace=True, axis=1)

    flow_df_final = flow_df.copy()

    flow_df_final.to_csv(f'{constants_and_paths.TEMP_OUTPUT_DATA_DUMP}/FlowAssignment.csv', index=False)

    # Extract the second part of the ServiceSectorID
    flow_df['SectorTo'] = flow_df['ServiceSectorID'].str.split('-').str[1]

    # Determine what is transit and what is PUD
    flow_df['Transit'] = flow_df.apply(lambda x: "PUD" if x['Destination'] in x['SectorTo'] else "Transit", axis=1)

    # Create dict to get from routeid to FRT/PCL ratio
    volume = pd.read_csv(f'{constants_and_paths.TEMP_INPUT_DATA_DUMP}/Raw_volume ' + constants_and_paths.SCN + '.csv')

    volume['RouteID'] = volume.apply(lambda x: get_route_id(x, flow_df), axis=1)
    volume['ParcelType'] = volume['Product'].str[7:10]

    # Group by RouteID and ParcelType and sum the Pieces
    grouped_volume = volume.groupby(['RouteID', 'ParcelType'])['Pieces'].sum()

    # Convert the grouped data to a dictionary using unstack and to_dict
    parceltype_dict = grouped_volume.unstack().fillna(0).to_dict(orient='index')
    flow_df['Pcl'] = flow_df.apply(lambda x: parceltype_dict[x['RouteID']]['PCL'] /
                (parceltype_dict[x['RouteID']]['PCL'] + parceltype_dict[x['RouteID']]['FGT']) * x['Pieces'], axis=1)
    flow_df['Frt'] = flow_df.apply(lambda x: parceltype_dict[x['RouteID']]['FGT'] /
                (parceltype_dict[x['RouteID']]['PCL'] + parceltype_dict[x['RouteID']]['FGT']) * x['Pieces'], axis=1)

    # Group by 'ID' and 'Category' in df2 and sum the 'Value' column
    int_locations = pd.read_csv(f'{constants_and_paths.TEMP_INPUT_DATA_DUMP}/IntLocationCodes.csv')
    flow_df_transit = flow_df[flow_df.Transit == "Transit"]
    flow_df_transit_dom = flow_df_transit[(~flow_df_transit.Origin.isin(int_locations.LocationCode)) &
                                          (~flow_df_transit.Destination.isin(int_locations.LocationCode))]
    flow_df_transit_int = flow_df_transit[~flow_df_transit.index.isin(flow_df_transit_dom.index)]
    flow_df_pud = flow_df[flow_df.Transit == "PUD"]
    flow_df_pud_dom = flow_df_pud[(~flow_df_pud.Origin.isin(int_locations.LocationCode)) &
                                  (~flow_df_pud.Destination.isin(int_locations.LocationCode))]
    flow_df_pud_int = flow_df_pud[~flow_df_pud.index.isin(flow_df_pud_dom.index)]
    flow_df_1_day = flow_df[flow_df['NrOfDays'] == 1]
    flow_df_2_days = flow_df[flow_df['NrOfDays'] == 2]
    flow_df_transit_dom = flow_df_transit_dom.groupby(['MovementID'], as_index=False)['Pieces'].sum()
    flow_df_transit_int = flow_df_transit_int.groupby(['MovementID'], as_index=False)['Pieces'].sum()
    flow_df_pud_dom = flow_df_pud_dom.groupby(['MovementID'], as_index=False)['Pieces'].sum()
    flow_df_pud_int = flow_df_pud_int.groupby(['MovementID'], as_index=False)['Pieces'].sum()
    flow_df_transit_pcl = flow_df_transit.groupby(['MovementID'], as_index=False)['Pcl'].sum()
    flow_df_transit_frt = flow_df_transit.groupby(['MovementID'], as_index=False)['Frt'].sum()
    flow_df_pud_pcl = flow_df_pud.groupby(['MovementID'], as_index=False)['Pcl'].sum()
    flow_df_pud_frt = flow_df_pud.groupby(['MovementID'], as_index=False)['Frt'].sum()
    flow_df_1_day = flow_df_1_day.groupby(['MovementID'], as_index=False)['Pieces'].sum()
    flow_df_2_days = flow_df_2_days.groupby(['MovementID'], as_index=False)['Pieces'].sum()
    flow_df.drop(['Transit', 'SectorTo'], inplace=True, axis=1)

    # Merge the result with df1 based on 'ID' and 'Category'
    movements_df = pd.merge(movements_df, flow_df_transit_dom.rename(columns={'Pieces': 'TransitDomPieces'}),
                            on='MovementID', how='left')
    movements_df = pd.merge(movements_df, flow_df_pud_dom.rename(columns={'Pieces': 'PUDDomPieces'}),
                            on='MovementID', how='left')
    movements_df = pd.merge(movements_df, flow_df_transit_int.rename(columns={'Pieces': 'TransitIntPieces'}),
                            on='MovementID', how='left')
    movements_df = pd.merge(movements_df, flow_df_pud_int.rename(columns={'Pieces': 'PUDIntPieces'}),
                            on='MovementID', how='left')
    movements_df = pd.merge(movements_df, flow_df_pud_pcl.rename(columns={'Pcl': 'PUDPclPieces'}),
                            on='MovementID', how='left')
    movements_df = pd.merge(movements_df, flow_df_pud_frt.rename(columns={'Frt': 'PUDFrtPieces'}),
                            on='MovementID', how='left')
    movements_df = pd.merge(movements_df, flow_df_transit_pcl.rename(columns={'Pcl': 'TransitPclPieces'}),
                            on='MovementID', how='left')
    movements_df = pd.merge(movements_df, flow_df_transit_frt.rename(columns={'Frt': 'TransitFrtPieces'}),
                            on='MovementID', how='left')
    movements_df = pd.merge(movements_df, flow_df_1_day.rename(columns={'Pieces': '24h'}),
                            on='MovementID', how='left')
    movements_df = pd.merge(movements_df, flow_df_2_days.rename(columns={'Pieces': '48h'}),
                            on='MovementID', how='left')

    movements_df['DepartureSlot'] = movements_df['FromLocation'] + "-" + \
                                    np.floor((movements_df['DepTime'] % 1) * 24).astype(int).astype(str)
    movements_df['ArrivalSlot'] = movements_df['ToLocation'] + "-" + \
                                    np.floor((movements_df['ArrTime'] % 1) * 24).astype(int).astype(str)
    movements_df.to_csv(f'{constants_and_paths.TEMP_OUTPUT_DATA_DUMP}/' + constants_and_paths.SCN + '/MovementsFullNetwork.csv', index=False)

    # Create a Pandas Excel writer using openpyxl as the engine
    with pd.ExcelWriter(constants_and_paths.MOVEMENTS_NETWORK_EXCEL_PATH, engine='openpyxl') as writer:
        # Write each DataFrame to a different worksheet
        flow_df_final.to_excel(writer, sheet_name='FlowAssignment', index=False)
        flow_df.to_excel(writer, sheet_name='FlowAssignmentDetails', index=False)
        movements_df.to_excel(writer, sheet_name='Movements', index=False)


# Function to find next service sector and connecting departure time
def find_next_service(row, df):
    # Filter within the same RouteID
    route_df = df[df['RouteID'] == row['RouteID']]

    # if row['RouteID'] == 'SCE-37A-NCEA-3-Main':
    #     print('test')

    # Find the next movement where ServiceSectorID starts with the Arrival Location
    next_services = route_df[route_df['ServiceSectorID'].str.startswith(row['Arrival_Location'] + '-')].copy()

    if next_services.empty:
        return None, None  # No next service found

    # Filter for valid departures after the current arrival time
    processing_time = 0
    if next_services.iloc[0, :]['ServiceSectorID'].split('-')[2] != 'Colocated' and \
            row['ServiceSectorID'].split('-')[2] != 'Colocated':
        if next_services.iloc[0, :]['ServiceSectorID'].split('-')[0] in ['MV9_h', 'LST_h']:
            processing_time = 90
        else:
            processing_time = 45
    valid_departures = next_services[next_services['Departure time'] >= (row['Arrival time'] + processing_time / 1440)]

    if not valid_departures.empty:
        # Get the next service sector with the earliest departure after arrival
        next_idx = valid_departures['Departure time'].idxmin()
        next_service = valid_departures.loc[next_idx]
        departure_time = next_service['Departure time']
    else:
        # If no later departure exists, take the earliest available departure and add 24h
        valid_departures = next_services[
            (next_services['Departure time'] + 1) >= (row['Arrival time'] + processing_time / 1440 - 0.000000001)]
        if not valid_departures.empty:
            next_idx = valid_departures['Departure time'].idxmin()
            next_service = next_services.loc[next_idx] if not next_services.empty else None
            departure_time = next_service['Departure time'] + 1
        else:
            valid_departures = next_services[
                (next_services['Departure time'] + 2) >= (row['Arrival time'] + processing_time / 1440)]
            if not valid_departures.empty:
                next_idx = valid_departures['Departure time'].idxmin()
                next_service = next_services.loc[next_idx] if not next_services.empty else None
                departure_time = next_service['Departure time'] + 2
            else:
                return None, None

    if next_service is not None:
        return next_service['ServiceSectorID'], departure_time
    else:
        return None, None


def find_previous_service(row, df):
    departure_location = row['Departure_Location']
    route_df = df[df['RouteID'] == row['RouteID']].copy()

    # Extract the second segment of ServiceSectorID for comparison
    route_df['Departure_Location_Extracted'] = route_df['ServiceSectorID'].str.split('-').str[1]

    # Adjust arrival times for midnight crossover
    route_df['Adjusted_Arrival'] = route_df['Arrival time']
    route_df.loc[route_df['Arrival time'] > row['Departure time'], 'Adjusted_Arrival'] -= 1  # subtract 1 day

    # Filter for matching departure location and valid adjusted arrival time
    previous_services = route_df[
        (route_df['Departure_Location_Extracted'] == departure_location) &
        (route_df['Adjusted_Arrival'] <= row['Departure time'])
    ]

    if previous_services.empty:
        return None, None

    # Get the latest adjusted arrival before the current departure
    prev_idx = previous_services['Adjusted_Arrival'].idxmax()
    prev_service = previous_services.loc[prev_idx]

    return prev_service['ServiceSectorID'], prev_service['Arrival time']


if __name__ == "__main__":
    generate_movements()
