from collections import defaultdict
from lion.orm.pickle_dumps import PickleDumps
from sqlalchemy import and_, tuple_
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.orm.location import Location
from lion.logger.exception_logger import log_exception
from lion.logger.exception_logger  import log_exception
from cachetools import TTLCache

from lion.utils.session_manager import SESSION_MANAGER

class RuntimesMileages(LION_SQLALCHEMY_DB.Model):

    __scope_hierarchy__ = ["group_name"]
    __tablename__ = 'runtimes'
    
    runtimes_cache = TTLCache(maxsize=1000, ttl=3600 * 8)

    orig = LION_SQLALCHEMY_DB.Column('Origin', LION_SQLALCHEMY_DB.TEXT, primary_key=True, nullable=False)
    dest = LION_SQLALCHEMY_DB.Column('Destination',
                     LION_SQLALCHEMY_DB.TEXT, primary_key=True, nullable=False)

    vehicle = LION_SQLALCHEMY_DB.Column('VehicleType', LION_SQLALCHEMY_DB.Integer, primary_key=True,
                        nullable=False)

    remarks = LION_SQLALCHEMY_DB.Column(
        'Remarks', LION_SQLALCHEMY_DB.TEXT, nullable=True)

    dist = LION_SQLALCHEMY_DB.Column('Distance', LION_SQLALCHEMY_DB.Integer, nullable=False)
    driving_time = LION_SQLALCHEMY_DB.Column('DrivingTime', LION_SQLALCHEMY_DB.Integer, nullable=False)
    break_time = LION_SQLALCHEMY_DB.Column('BreakTime', LION_SQLALCHEMY_DB.Integer)
    rest_time = LION_SQLALCHEMY_DB.Column('RestTime', LION_SQLALCHEMY_DB.Integer)
    drivers = LION_SQLALCHEMY_DB.Column('Drivers', LION_SQLALCHEMY_DB.Integer)
    group_name = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(150), nullable=True)

    def __init__(self, **kwargs):

        self.orig = kwargs.get('orig')
        self.dest = kwargs.get('dest')
        self.vehicle = kwargs.get('vehicle')
        self.dist = kwargs.get('dist')
        self.driving_time = kwargs.get('driving_time')
        self.break_time = kwargs.get('break_time')
        self.rest_time = kwargs.get('rest_time')
        self.drivers = kwargs.get('drivers')
        self.remarks = kwargs.get('remarks')
        self.group_name = kwargs.get('group_name', SESSION_MANAGER.get('group_name'))


    @classmethod
    def get_existing_records(cls) -> list:

        try:
            list_existing_records = LION_SQLALCHEMY_DB.session.query(
                cls.orig,
                cls.dest,
                cls.vehicle).filter(and_(cls.driving_time > 0, cls.dist > 0)).all()

            return ['|'.join(
                [obj.orig, obj.dest, str(obj.vehicle)]) for obj in list_existing_records]

        except Exception:
            return []

    @classmethod
    def get_existing_tuples(cls) -> list:

        try:
            list_existing_records = LION_SQLALCHEMY_DB.session.query(
                cls.orig,
                cls.dest,
                cls.vehicle).filter(cls.driving_time > 0, cls.dist > 0).all()

            return [(obj.orig, obj.dest, obj.vehicle) for obj in list_existing_records]

        except Exception:
            return []
        
    @classmethod
    def get_existing_lanes(cls) -> list:

        try:
            list_existing_records = LION_SQLALCHEMY_DB.session.query(
                cls.orig,
                cls.dest).all()

            return ['|'.join([obj.orig, obj.dest]) for obj in list_existing_records]

        except Exception:
            return []


    def __repr__(self):
        return "<DistanceTime: {}-{}-{}>".format(self.orig, self.dest,
                                                 self.vehicle)

    @classmethod
    def get_dist_runtime(cls, orig, dest, vehicle=1) -> tuple:
        """
        This method retrieves the driving time and distance between two locations for a specified vehicle type.
        returns runtime, distance tuple.
        """

        multiplier = 0.8 if int(cls.runtimes_cache.pop('vehicle_change', False)) else 1
        try:
            _dct = cls.runtimes_cache['dict_dist_time'][orig][dest][vehicle]
            return _dct['driving_time'], _dct['dist']

        except KeyError:
            if 'dict_dist_time' not in cls.runtimes_cache:
                cls.to_dict()

                _dct = cls.runtimes_cache['dict_dist_time'][orig][dest][vehicle]
                return _dct['driving_time'], _dct['dist']

            else:
                
                obj = cls.query.filter(and_(cls.orig == orig, 
                                            cls.dest == dest, 
                                            cls.vehicle == vehicle)).first()
                
                if obj:
                    return obj.driving_time * multiplier, obj.dist

                obj = cls.query.filter(and_(cls.orig == dest, 
                                            cls.dest == orig, 
                                            cls.vehicle == vehicle)).first()

                if obj:
                    return obj.driving_time * multiplier, obj.dist
                
                if vehicle == 4:
                    cls.runtimes_cache['vehicle_change'] = True
                    return cls.get_dist_runtime(orig=orig, dest=dest, vehicle=1)
        
        return None, None

    @classmethod
    def get_runtime(cls, **kwargs):

        try:
            return cls.runtimes_cache['dict_dist_time'][kwargs['orig']][kwargs['dest']][kwargs['vehicle']]['driving_time']
        except Exception:
            if 'dict_dist_time' not in cls.runtimes_cache:
                cls.to_dict()
            else:
                return None

        try:
            return cls.runtimes_cache['dict_dist_time'][kwargs['orig']][kwargs['dest']][kwargs['vehicle']]['driving_time']
        except Exception:
            log_exception(popup=True, remarks=f"Runtime not found for {kwargs['orig']} to {kwargs['dest']} with vehicle {kwargs['vehicle']}")

        return None

    @classmethod
    def get_mileage(cls, **kwargs):

        try:
            return cls.runtimes_cache['dict_dist_time'][kwargs['orig']][kwargs['dest']][kwargs['vehicle']]['dist']
        except Exception:
            if 'dict_dist_time' not in cls.runtimes_cache:
                cls.to_dict()
            else:
                return None

        try:
            return cls.runtimes_cache['dict_dist_time'][kwargs['orig']][kwargs['dest']][kwargs['vehicle']]['dist']
        except Exception:
            log_exception(popup=True, remarks=f"Runtime not found for {kwargs['orig']} to {kwargs['dest']} with vehicle {kwargs['vehicle']}")

        return None

    @classmethod
    def query_runtime_mileage(cls, **kwargs):

        try:
            obj = cls.query.filter(cls.orig==kwargs['orig'],
                                   cls.dest == kwargs['dest'], 
                                   cls.vehicle == kwargs['vehicle']).first()
            
            if obj:
                return obj.driving_time, obj.dist
            
        except Exception as e:
            log_exception(f"Querying from lion.runtimes db failed {str(e)}")
        
        return None, None


    @classmethod
    def to_dict(cls):

        try:
            return cls.runtimes_cache['dict_dist_time']
        except:
            pass

        try:
        
            set_locs = set(Location.to_dict())
            dict_dist_time = defaultdict(lambda: defaultdict(dict))

            all_data = cls.query.with_entities(
                cls.orig, cls.dest, cls.vehicle, cls.driving_time, cls.dist
            ).filter(and_(cls.orig.in_(set_locs), cls.dest.in_(set_locs))).all()

            for org, dst, vhcl, rntime, dist in all_data:
                dict_dist_time[org][dst][vhcl] = {
                    'driving_time': rntime,
                    'dist': dist
                }

        except Exception:
            log_exception(
                popup=True, remarks='Could not build dct_dist_time!')

            return {}

        dict_dist_time['runtimes_region'] = 'Default'
        cls.runtimes_cache['dict_dist_time'] = dict_dist_time

        return dict_dist_time

    @classmethod
    def import_df(cls, df_new_disttime=None, overwite_existing_lanes=False):

        if df_new_disttime is None or df_new_disttime.empty:
            return

        list_of_dicts = df_new_disttime.to_dict('records')
        hdrs = list_of_dicts[0].keys()
        _err = ''

        if 'Origin' in hdrs and 'Destination' in hdrs and 'VehicleType' in hdrs:

            while list_of_dicts:

                dct = list_of_dicts.pop()
                try:

                    if dct["DrivingTime"] == 0 or dct["Distance"] == 0:
                        lane = f"{dct['Origin']}->{dct['Destination']}"
                        raise ValueError(
                            f"Invalid input data {lane}: {dct['DrivingTime']}; {dct['Distance']}")
                    else:
                        existing_obj = cls.query.filter(
                            cls.orig == dct['Origin'],
                            cls.dest == dct['Destination'],
                            cls.vehicle == dct['VehicleType']
                        ).first()

                        if existing_obj is not None:
                            if overwite_existing_lanes:
                                LION_SQLALCHEMY_DB.session.delete(existing_obj)
                                LION_SQLALCHEMY_DB.session.commit()
                            else:
                                continue

                        new_data = cls(
                            orig=dct['Origin'],
                            dest=dct['Destination'],
                            vehicle=dct['VehicleType'],
                            dist=dct['Distance'],
                            driving_time=dct["DrivingTime"],
                            break_time=dct["BreakTime"],
                            rest_time=dct['RestTime'],
                            drivers=dct['Drivers'],
                            remarks=dct['remarks']
                        )

                        LION_SQLALCHEMY_DB.session.add(new_data)
                except Exception as err:
                    _err = f"{_err} {str(err)}"
                    log_exception(remarks=_err)

            LION_SQLALCHEMY_DB.session.commit()

        else:
            _err = ''

        cls.clear_cache()
        cls.runtimes_cache['dict_dist_time'] = cls.to_dict()
        return _err

    @classmethod
    def update(cls, **kwargs):
        """
        Updates single record in DistanceTime database. Origin, Destination and VehicleType
        are critical componenets to provide.
        """
        hdrs = kwargs.keys()

        if 'Origin' in hdrs and 'Destination' in hdrs and 'VehicleType' in hdrs:

            cls.runtimes_cache.pop((
                kwargs['Origin'], kwargs['Destination'], kwargs['VehicleType']), None)

            try:
                existing_obj = cls.query.filter(
                    cls.orig == kwargs['Origin'],
                    cls.dest == kwargs['Destination'],
                    cls.vehicle == kwargs['VehicleType']
                ).first()

                dct_data = {}
                if existing_obj is not None:
                    dct_data = existing_obj.as_dict()

                dist = kwargs.get('Distance', dct_data.get('dist', 0))
                if not dist:
                    raise ValueError('Zero mileage not allowed!')

                driving_time = kwargs.get(
                    'DrivingTime', dct_data.get('driving_time', 0))

                if not driving_time:
                    raise ValueError('Zero driving_time not allowed!')

                drivers = kwargs.get('Drivers', dct_data.get('drivers', 1))
                if not drivers:
                    raise ValueError('Zero drivers not allowed!')

                remarks = kwargs.get('Remarks', dct_data.get('remarks', ''))

                if dct_data:
                    LION_SQLALCHEMY_DB.session.delete(existing_obj)
                    LION_SQLALCHEMY_DB.session.commit()

                new_data = cls(
                    orig=kwargs['Origin'],
                    dest=kwargs['Destination'],
                    vehicle=kwargs['VehicleType'],
                    dist=dist,
                    driving_time=driving_time,
                    break_time=0,
                    rest_time=0,
                    drivers=drivers,
                    remarks=remarks
                )

                LION_SQLALCHEMY_DB.session.add(new_data)
                LION_SQLALCHEMY_DB.session.commit()

            except Exception:
                LION_SQLALCHEMY_DB.session.rollback()
                log_exception()
                return False

            
            try:
                dict_dist_time = cls.runtimes_cache.get('dict_dist_time', {})

                if dict_dist_time:
                    dict_dist_time[kwargs['Origin']][kwargs['Destination']][kwargs['VehicleType']] = {
                        'driving_time': driving_time, 'dist': dist}

                    cls.runtimes_cache['dict_dist_time'] = dict_dist_time
                else:
                    cls.clear_cache()
                    cls.runtimes_cache['dict_dist_time'] = cls.to_dict()

            except Exception:
                cls.clear_cache()
                cls.runtimes_cache['dict_dist_time'] = cls.to_dict()

            return True

        try:
            raise ValueError(
                f'One or more key headers, i.e., Origin, Destination and VehicleType are missing')
        except Exception:
            log_exception()

        return False

    @classmethod
    def delete_existing_tuples(cls, tuples_to_delete=[]) -> bool:
        """
        Deletes existing records from the database. tuples_to_delete is a list of tuples
        where each tuple contains (orig, dest, vehicle).
        """

        if not tuples_to_delete:
            return False
        
        try:
            cls.query.filter(and_(tuple_(cls.orig,
                                    cls.dest,
                                    cls.vehicle).in_(tuples_to_delete))).delete(synchronize_session=False)
            LION_SQLALCHEMY_DB.session.commit()
            cls.clear_cache()

        except Exception as e:
            LION_SQLALCHEMY_DB.session.rollback()
            log_exception(f"Error deleting existing tuples: {str(e)}")
            return False
        
        return True


    @classmethod
    def clear_cache(cls):
        cls.runtimes_cache.clear()
        PickleDumps.remove(
            filename='runtimes_mileages')