from lion.optimization.driver_locs_per_lane import calculate_dct_driver_locs_per_lane
from lion.optimization.excluded_shifts import update_excluded_shifts_and_movements
from lion.optimization.optimization_logger import OPT_LOGGER
from lion.optimization.opt_params import OPT_PARAMS
from lion.optimization.read_user_movements.import_movements_xlsm import import_user_movements
from lion.orm.drivers_info import DriversInfo
from lion.orm.shift_movement_entry import ShiftMovementEntry
from lion.movement.movements_manager import UI_MOVEMENTS
from lion.shift_data.shift_data import UI_SHIFT_DATA


def run_strategic_optimization(self):

    self._dict_movements_to_optimize = {}

    OPT_LOGGER.log_info('Setting scope ...')
    OPT_PARAMS.LION_TEMP_STATUSBAR_INFO = 'Setting scope ...'
    update_excluded_shifts_and_movements()

    try:
        if OPT_PARAMS.USER_LOADED_MOVEMENTS_FLAG:

            UI_MOVEMENTS.refresh_movement_id()

            # Read movements that run on Wed
            if not import_user_movements(
                    weekdays=[OPT_PARAMS.OPTIMIZATION_REP_DAY],
                    set_excluded_movements=self._set_excluded_movements):

                raise ValueError(
                    'Reading user defined movements has failed!')

            self._dict_movements_to_optimize = UI_MOVEMENTS.dict_all_movements

            message = f'Per request from the user, user defined loaded movements will be optimized.'
            message = f'{message}\nPlease note that the excldued tours/movements will be based on'
            message = f'{message} {UI_SHIFT_DATA.scn_name}.'

            OPT_LOGGER.log_info(message)

            self._set_movements_in_scope = set(
                self._dict_movements_to_optimize)

        else:

            self._set_movements_in_scope = set()

            for t in self._set_drivers_in_scope:
                self._set_movements_in_scope.update(
                    UI_SHIFT_DATA.optimal_drivers[t][
                        'list_movements'])

            self._dict_movements_to_optimize = {m: v for m, v in UI_SHIFT_DATA.dict_all_movements.items()
                                                    if m in self._set_movements_in_scope and v.is_loaded()}

            list_movements_to_optimize = list(
                self._dict_movements_to_optimize)

            if list_movements_to_optimize:

                self._max_loaded_id, _max_repos_id = ShiftMovementEntry.get_max_movement_ids()

                def _get_new_loaded_movement_id():
                    self._max_loaded_id += 1
                    return self._max_loaded_id

                mov_ids = [movement_id for movement_id, in ShiftMovementEntry.query.with_entities(
                    ShiftMovementEntry.movement_id).filter(ShiftMovementEntry.movement_id.in_(list_movements_to_optimize)).all()]

                dct_mov_ids = {m: _get_new_loaded_movement_id()
                                for m in mov_ids}

                records = ShiftMovementEntry.query.filter(
                    ShiftMovementEntry.movement_id.in_(list_movements_to_optimize)).all()

                for m in list_movements_to_optimize:

                    dct_m = self._dict_movements_to_optimize.pop(m)
                    dct_m['MovementID'] = dct_mov_ids[m]
                    dct_m.shift_id = 0

                    self._dict_movements_to_optimize[dct_mov_ids[m]] = dct_m

                list_records = [
                    ShiftMovementEntry(
                        movement_id=dct_mov_ids[rcrd.movement_id],
                        str_id=rcrd.str_id,
                        tu_dest=rcrd.tu_dest,
                        loc_string=rcrd.loc_string,
                        is_loaded=rcrd.is_loaded,
                        shift_id=0
                    ) for rcrd in records
                ]

                db.session.add_all(list_records)
                db.session.commit()

        _set_incl_shift_ids_rep_day = set()

        if self._set_drivers_in_scope:

            _set_incl_shift_ids_rep_day = set([d for d in self._set_drivers_in_scope
                                                if DriversInfo.shift_id_runs_on_weekday(
                                                    shift_id=d, weekday=OPT_PARAMS.OPTIMIZATION_REP_DAY)])

            try:

                all_objs_in_scope = DriversInfo.query.filter(
                    DriversInfo.shift_id.in_(self._set_drivers_in_scope)).all()

                for obj in all_objs_in_scope:

                    for dy in self._optimization_weekdays:
                        setattr(obj, dy.lower(), False)

                db.session.commit()
                del all_objs_in_scope

            except SQLAlchemyError as e:
                db.session.rollback()
                OPT_LOGGER.log_exception(popup=False, remarks=f"{str(e)}")

            except Exception:
                db.session.rollback()
                OPT_LOGGER.log_exception(popup=False)

            shifts2del = DriversInfo.clean_up_unused_shifts()
            shifts2del_outofScope = [
                d for d in shifts2del if d not in self._set_drivers_in_scope]

            if shifts2del_outofScope:
                OPT_LOGGER.log_info(
                    f'These shift ids labeled to be deleted but they are out of scope: {shifts2del_outofScope}')

                shifts2del = [
                    d for d in shifts2del if d in self._set_drivers_in_scope]

            if OPT_PARAMS.USER_LOADED_MOVEMENTS_FLAG:
                """
                If user-defined movements are used for optimization, the movements, run by deleted shifts,
                can be deleted from local movements table
                """

                try:
                    ShiftMovementEntry.query.filter(
                        ShiftMovementEntry.shift_id.in_(shifts2del)).delete()
                    db.session.commit()

                except SQLAlchemyError as e:
                    db.session.rollback()
                    OPT_LOGGER.log_exception(
                        popup=False, remarks=f"Deleting redundant movements failed: {str(e)}")

                except Exception:
                    db.session.rollback()
                    OPT_LOGGER.log_exception(
                        popup=False, remarks="Deleting redundant movements failed.")

        # End of if not self._dict_movements_to_optimize:

        # backup_local_schedule()

        UI_MOVEMENTS.refresh_movement_id()
        UI_MOVEMENTS.dict_all_movements = self._dict_movements_to_optimize


        self._set_movements_in_scope = set(
            self._dict_movements_to_optimize)

        self._set_double_man_movements = [m for m in self._set_movements_in_scope
                                            if self._dict_movements_to_optimize[m]['DrivingTime'] >= self._double_man_shift_detecting_runtime]

        OPT_LOGGER.log_info(
            'Runtimes and mileages will be updated based on the selected runtimes scenario!')

        _set_excluded_shift_ids_single_day = set([d for d in self._set_excluded_shift_ids
                                                    if DriversInfo.shift_id_runs_on_weekday(
                                                        shift_id=d, weekday=OPT_PARAMS.OPTIMIZATION_REP_DAY)])
        __t_obj = Duration()

        n_all_m = len(self._set_excluded_movements) + \
            len(self._set_movements_in_scope)

        __n_drivers_to_optimize = len(self._set_drivers_in_scope)
        __n_excluded_tours = len(self._set_excluded_shift_ids)
        _all_tours = __n_drivers_to_optimize + __n_excluded_tours

        OPT_LOGGER.log_info(
            message=f'Excluded/incl/total shifts count (scope): {__n_excluded_tours}/{__n_drivers_to_optimize}/{_all_tours}; ' +
            f'Excl. {OPT_PARAMS.OPTIMIZATION_REP_DAY} data: {len(_set_excluded_shift_ids_single_day)}')

        OPT_LOGGER.log_info(
            message=f'Movements count to optimize (scope): {len(self._set_movements_in_scope)}/{n_all_m}')

        OPT_LOGGER.log_info(
            message=f'# of tours to be replaced on {';'.join(self._optimization_weekdays)}: {__n_drivers_to_optimize}')

        OPT_LOGGER.log_info(
            message=f'# of tours to be replaced on {OPT_PARAMS.OPTIMIZATION_REP_DAY}: {len(_set_incl_shift_ids_rep_day)}')

        if not self._dict_movements_to_optimize:
            raise ValueError('No movement was selected for optimization!')

        self._dct_recommended_movements_per_driver_loc = defaultdict(set)
        __set_movements_with_no_recom = set()

        df_mov_cnt = DataFrame(columns=['loc_code', 'n_movements'])

        if OPT_PARAMS.DCT_DRIVER_LOCS_PER_LANE:

            self._dct_recommended_movements_per_driver_loc, \
                __set_movements_with_no_recom = self._cluster_movements(
                    lane_base_only=run_full_opt)

            df_mov_cnt = DataFrame(
                [{'loc_code': k,
                    'n_movements': len(v),
                    'movements': '|'.join([str(m) for m in v])}
                    for k, v in self._dct_recommended_movements_per_driver_loc.items()]
            )

        if self._run_extended_optimisation or (
                not OPT_PARAMS.DCT_DRIVER_LOCS_PER_LANE):

            __set_movements_with_no_recom = set(
                self._dict_movements_to_optimize.keys())

            OPT_LOGGER.log_info(
                message=f"dct_driver_locs_per_lane is empty: {len(OPT_PARAMS.DCT_DRIVER_LOCS_PER_LANE) == 0}" +
                f"\nRun extended optimisation: {self._run_extended_optimisation}")

        # if OPT_PARAMS.DCT_DRIVER_LOCS_PER_LANE:
        #     ScnInfo.pickle_dump(filename='dct_driver_locs_per_lane', obj=self._dct_driver_locs_per_lane)

        self._dct_close_by_driver_locs = {}

        if OPT_PARAMS.N_TOP_CLOSEST_DRIVER_LOC:

            """
            If there are movements with no recommendation, the following code will find the top 
            OPT_PARAMS.N_TOP_CLOSEST_DRIVER_LOC closest driver locations
            """

            OPT_LOGGER.log_info(
                message=f'There are {len(
                    __set_movements_with_no_recom)} movements with no recommendation. n_top_closest_driver_loc: {OPT_PARAMS.N_TOP_CLOSEST_DRIVER_LOC}')

            __close_by_locs = LocationFinder()
            __close_by_locs.read_location_params()
            __close_by_locs.clear_dct_close_by_driver_locs()
            self._dct_close_by_driver_locs = __close_by_locs.dct_close_by_driver_locs

            if not self._dct_close_by_driver_locs:
                raise ValueError('dct_close_by_driver_locs is empty!')

            del __close_by_locs

            self._logFileMessage = ''
            self._loc_capacity_limit = 80 if self._run_extended_optimisation else 1e6
            [self._get_propsoed_locs_for_movement(
                movement_id=m) for m in __set_movements_with_no_recom]

            OPT_LOGGER.log_info(
                message=f'Movements with no recommendations have been processed! {self._logFileMessage}')

            if df_mov_cnt.empty:
                df_mov_cnt = DataFrame(
                    [{'loc_code': k, 'n_movements_based_on_closed_loc': len(v), 'updated_movements': '|'.join([str(m) for m in v])}
                        for k, v in self._dct_recommended_movements_per_driver_loc.items()]
                )

            else:
                df_mov_cnt['n_movements_based_on_closed_loc'] = df_mov_cnt['loc_code'].apply(
                    lambda x: len(self._dct_recommended_movements_per_driver_loc.get(x, set())))

                df_mov_cnt['updated_movements'] = df_mov_cnt['loc_code'].apply(
                    lambda x: '|'.join([str(m) for m in self._dct_recommended_movements_per_driver_loc.get(x, set())]))

        else:
            OPT_LOGGER.log_info(
                message=f'set_movements_with_no_recom empty: {len(__set_movements_with_no_recom) == 0}')

        df_mov_cnt.to_csv(os_path.join(self._optimization_output_dir, 'NumberOfAllocatedMovementsPerDriverLoc.csv'),
                            index=False)

        __n_movements = len(self._dict_movements_to_optimize)

        __logFileMessage = f"Optimization process started with {__n_movements} loaded movements. "

        __logFileMessage = f"{__logFileMessage}Initial tours count: {
            __n_drivers_to_optimize}"

        OPT_LOGGER.log_info(message=__logFileMessage)

        __driver_optimization = strategic_DriverOptimization(
            weekdays=self._optimization_weekdays)

        # only when __dct_recommended_movements_per_driver_loc is empty!
        __driver_optimization.n_top_closest_driver_loc = OPT_PARAMS.N_TOP_CLOSEST_DRIVER_LOC
        __driver_optimization.movements = UI_MOVEMENTS
        __driver_optimization.dct_loc_recommended_movements = self._dct_recommended_movements_per_driver_loc

        if not __driver_optimization.generate_and_optimize():
            return False

        __logFileMessage = f"Optimization time elapse: {__t_obj.collapsed_time()}"
        __logFileMessage = f"{__logFileMessage}\nProcessing output & generating reprots ..."
        OPT_LOGGER.log_info(message=__logFileMessage)

        self._dct_recommended_movements_per_driver_loc = {}

        UserParams.update(excluded_locs='')
        if '__LION_TEMP__excluded_locs' in environ.keys():
            del environ['__LION_TEMP__excluded_locs']

        scn_name = ScnInfo.get_param(
            param='scn_name', if_null='')

        if scn_name:
            scn_name = f'Optimised-{scn_name} - {datetime.now().strftime('%Y%m%d-%H%M')}'
        else:
            scn_name = f"Optimised schedule {datetime.now().strftime('%Y%m%d-%H%M')}"

        environ['__LION_TEMP__OPTIMIZED_SCN_NAME'] = scn_name

        ScnInfo.update(scn_name=scn_name)
        ScnInfo.query.filter(ScnInfo.param == 'scn_id').delete()
        db.session.commit()

        # UI_SHIFT_DATA = self._BuildSchedule.load_baseline_shift_data()

        unplanned = [m for m, in ShiftMovementEntry.query.with_entities(
            ShiftMovementEntry.movement_id).filter(ShiftMovementEntry.shift_id == 0).all()]

        unplanned_long_movs = [
            m for m in unplanned if m in self._set_double_man_movements]

        __success_message = 'Optimization completed successfully.'

        if unplanned:

            __success_message = f'{__success_message}: {len(unplanned)} out of {len(self._set_movements_in_scope)} movements not scheduled'

            if unplanned_long_movs:
                __success_message = f'{__success_message} out of which {len(unplanned_long_movs)} are more suitable for double man shift!'
                __success_message = f'{__success_message} Thus the number of unplanned regular movements is: {len(unplanned) - len(unplanned_long_movs)}.'
            else:
                __success_message = f'{__success_message}.'

        __success_message = f'{__success_message}\nElapsed time: {
            __t_obj.collapsed_time()}'

        OPT_LOGGER.log_info(message=__success_message)
        self._dump_kpi_reports()

        UI_PARAMS.DICT_DRIVERS_PER_PAGE = {}
        UI_MOVEMENTS.reset()
        UI_SHIFT_DATA.reset()

        if not self.load_movements_object():
            OPT_LOGGER.log_info(
                message='load_movements_object has failed!')

        return {'success': __success_message, 'failure': ''}

    except Exception:

        __err = OPT_LOGGER.log_exception(
            popup=False, remarks='Optimization failed!')

        OPT_LOGGER.log_info(message=__err)

        return {'failure': __err, 'success': ''}
