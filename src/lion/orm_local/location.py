from collections import defaultdict
from lion.logger.exception_logger import log_exception
from lion.create_flask_app.create_app import LION_FLASK_APP
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.orm.location_mapping import LocationMapper
from sqlalchemy.exc import SQLAlchemyError
from lion.logger.status_logger import log_message
from lion.config.paths import LION_FILES_PATH
from os.path import join
from pandas import DataFrame, read_excel
from lion.ui.ui_params import UI_PARAMS
from lion.utils.is_file_updated import is_file_updated
from cachetools import TTLCache


class Location(LION_SQLALCHEMY_DB.Model):

    __bind_key__ = 'local_data_bind'
    __tablename__ = 'location'

    dct_locations_cache = TTLCache(maxsize=1000, ttl=8 * 3600)

    loc_code = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(20),
                         nullable=False, primary_key=True)
    utcdiff = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, nullable=False, default=0)
    loc_type = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String, nullable=False)
    active = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Boolean, nullable=False, default=True)
    location_name = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String, nullable=False)
    latitude = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Double, nullable=False)
    longitude = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Double, nullable=False)
    town = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String, nullable=False)
    postcode = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String, nullable=False)
    country_code = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(5), nullable=False)
    chgover_driving_min = LION_SQLALCHEMY_DB.Column(
        LION_SQLALCHEMY_DB.Integer, nullable=False, default=10)
    chgover_non_driving_min = LION_SQLALCHEMY_DB.Column(
        LION_SQLALCHEMY_DB.Integer, nullable=False, default=15)
    dep_debrief_time = LION_SQLALCHEMY_DB.Column(
        LION_SQLALCHEMY_DB.Integer, nullable=False, default=30)
    arr_debrief_time = LION_SQLALCHEMY_DB.Column(
        LION_SQLALCHEMY_DB.Integer, nullable=False, default=30)
    remarks = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String, nullable=False)
    turnaround_min = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, nullable=False)
    live_stand_load = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String, nullable=False)
    ctrl_depot = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String)
    group_name = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String, nullable=False)

    def __init__(self, **loc_data):
        self.loc_code = loc_data.get('loc_code', '')
        self.utcdiff = loc_data.get('utcdiff', 0)
        self.loc_type = loc_data.get('loc_type', '')
        self.active = loc_data.get('active', True)
        self.location_name = loc_data.get('location_name', '')
        self.latitude = loc_data.get('latitude', 0)
        self.longitude = loc_data.get('longitude', 0)
        self.town = loc_data.get('town', '')
        self.postcode = loc_data.get('postcode', '')
        self.country_code = UI_PARAMS.LION_REGION
        self.chgover_driving_min = loc_data.get('chgover_driving_min', 10)
        self.chgover_non_driving_min = loc_data.get(
            'chgover_non_driving_min', 15)
        self.dep_debrief_time = loc_data.get('dep_debrief_time', 30)
        self.arr_debrief_time = loc_data.get('arr_debrief_time', 30)
        self.remarks = loc_data.get('remarks', '')
        self.turnaround_min = loc_data.get('turnaround_min', 25)
        self.live_stand_load = loc_data.get('live_stand_load', 'Stand Load')
        self.ctrl_depot = loc_data.get('ctrl_depot', '')
        self.group_name = loc_data.get('group_name', LION_FLASK_APP.config.get('LION_USER_GROUP_NAME', 'To Be Validated'))

    def __repr__(self):
        return f"<Location(location_name='{self.location_name}')>"
    
    @classmethod
    def clear_cache(cls):
        cls.dct_locations_cache.clear()
        cls.dct_locations_cache = TTLCache(maxsize=1000, ttl=8 * 3600)

    @classmethod
    def get_group_name(cls) -> str:
        """
        Fetch the group name for the user based on Location data.
        """
        try:
            return cls.query.first().group_name
        except Exception:
            log_exception(popup=False, remarks='Could not fetch group name')
            return ''

    @classmethod
    def validate_region(cls) -> bool:

        rgns = set([cntry for cntry, in cls.query.with_entities(cls.country_code).all()])

        if len(rgns) == 1:
            
            rgn = rgns.pop()
            LION_FLASK_APP.config['LION_USER_REGION_NAME'] = rgn
            LION_FLASK_APP.config['LION_USER_LANGUAGE_NAME'] = rgn
            UI_PARAMS.LION_REGION = rgn

    @classmethod
    def get_attr_value(cls, loc_code=None, attribute=''):
        try:
            location_obj = cls.query.filter_by(loc_code=loc_code).first()

            if location_obj and hasattr(location_obj, attribute):
                return getattr(location_obj, attribute)
            else:
                return None

        except Exception:
            return None

    @classmethod
    def location_types(cls) -> dict:
        """
        Returns a dict of the type of location based on the loc_code.
        """

        if 'dct_loc_types' in cls.dct_locations_cache:
            return cls.dct_locations_cache['dct_loc_types']
        
        dct_ftprnt = cls.to_dict()

        try:
            dct_loc_types = {}

            for loc_code, loc_data in dct_ftprnt.items():
                dct_loc_types[loc_code] = loc_data.get('loc_type', 'Unknown-Type')

            cls.dct_locations_cache['dct_loc_types'] = dct_loc_types

            return dct_loc_types
        
        except Exception:
            log_exception(popup=False, remarks='Could not fetch location type')
            return {}

    @classmethod
    def location_type(cls, loc_code=None) -> str:
        """
        Returns the type of location based on the loc_code.
        """

        if 'dct_loc_types' not in cls.dct_locations_cache:
            cls.location_types()

        try:
            if loc_code:
                return cls.dct_locations_cache['dct_loc_types'][loc_code]

        except Exception:
            log_exception(popup=False, remarks='Could not fetch location type')
            return 'Unknown-Type'

    @classmethod
    def is_customer(cls, loc_code='') -> bool:
        """
        Returns True if the location is a customer, False otherwise.
        """
        try:
            return loc_code in cls.dct_locations_cache['list_customers']
        except Exception:
            if 'list_customers' not in cls.dct_locations_cache:

                cls.get_customers()
                return loc_code in cls.dct_locations_cache['list_customers']

            log_exception(popup=False, remarks='Could not check if location is a customer')
            return False

    @classmethod
    def get_customers(cls) -> list:
        try:
            return cls.dct_locations_cache['list_customers']
        except KeyError:
            pass

        try:
            dct_ftprnt = cls.to_dict()
            cls.dct_locations_cache['list_customers'] = [loc for loc, v in dct_ftprnt.items() 
                                                    if v['loc_type'].lower() == 'customer']

            return cls.dct_locations_cache['list_customers']
        
        except Exception:
            log_exception(popup=False, remarks='Could not fetch list of customers')
            return []

    @classmethod
    def coordinates(cls, locs=[]):
        try:

            if locs:
                objs = cls.query.with_entities(cls.loc_code, cls.latitude, cls.longitude).filter(
                    cls.loc_code.in_(locs)
                ).all()
            
            else:
                objs = cls.query.with_entities(cls.loc_code, cls.latitude, cls.longitude).all()

            if objs:
                return DataFrame(objs, columns=['Name', 'Latitude', 'Longitude'])
        
        except Exception:
            log_exception(popup=False, remarks='Could not fetch list of customers')
            return DataFrame(columns=['Name', 'Latitude', 'Longitude'])
     

    @classmethod
    def to_dict(cls, clear_cache=False):
        """
        Returns a dictionary representation of location data, including mappings, optionally clearing the cache.
        This method retrieves location data from the cache if available, otherwise queries the database
        for locations matching the current region. It also applies location mappings and updates the cache.
        Args:
            clear_cache (bool, optional): If True, clears the cached location data before fetching fresh data.
                                          Defaults to False.
        Returns:
            dict: A dictionary mapping location codes to their respective location data.
        Raises:
            Exception: If footprint data is not found in the cache.
            SQLAlchemyError: If a database error occurs during location query.
        Side Effects:
            - Updates the class-level cache with the latest location footprint and customer list.
            - Logs exceptions encountered during execution.
        """

        if not clear_cache:

            try:
                dct_footprint = cls.dct_locations_cache.get('dct_footprint', {})
                if not dct_footprint:
                    raise Exception('Footprint data not found')
                
                return dct_footprint
            except:
                pass

        try:
            location_objs = cls.query.filter(cls.country_code == UI_PARAMS.LION_REGION).all()

            _dct_footprint = {
                loc_obj.loc_code: {
                    **{k: v for k, v in loc_obj.__dict__.items() if not k.startswith('_sa_')}
                }
                for loc_obj in location_objs if loc_obj is not None
            }

            dct_loc_mapping = LocationMapper.get_mappings()
            if dct_loc_mapping:

                dct_mapped_footprint = defaultdict(dict)

                for loc_code, mapping in dct_loc_mapping.items():
                    if mapping in _dct_footprint:
                        dct_mapped_footprint[loc_code].update(_dct_footprint[mapping])
                        dct_mapped_footprint[loc_code].update({'loc_code': loc_code})
                
                _dct_footprint.update(dct_mapped_footprint)

        except SQLAlchemyError as err:
            log_exception(popup=False, remarks=str(err))
            return {}

        except Exception:
            log_exception(popup=False)
            return {}

        cls.dct_locations_cache['dct_footprint'] = _dct_footprint
        cls.dct_locations_cache['list_customers'] = [loc for loc, v in _dct_footprint.items() 
                                                 if v['loc_type'].lower() == 'customer']
        return _dct_footprint

    @classmethod
    def upsert(cls, loc_data):

        loc_code = loc_data.get('loc_code', '')
        try:
            if loc_code != '':

                location = cls.query.filter(
                    cls.loc_code == loc_data['loc_code'], 
                    cls.country_code == UI_PARAMS.LION_REGION).first()

                if location is not None:
                    # Update attributes of the existing record
                    for key, value in loc_data.items():
                        setattr(location, key, value)
                else:
                    # Create a new record
                    location = Location(**loc_data)
                    LION_SQLALCHEMY_DB.session.add(location)

                LION_SQLALCHEMY_DB.session.commit()

        except Exception as err:
            log_message(message=str(err))
            LION_SQLALCHEMY_DB.session.rollback()

        del cls.dct_locations_cache['dct_footprint']
        cls.dct_locations_cache['dct_footprint'] = cls.to_dict()

    @classmethod
    def update(cls, **loc_data):

        loc_code = loc_data.get('loc_code', '')
        try:
            if loc_code != '':

                location = cls.query.filter(
                    cls.loc_code == loc_data['loc_code'], cls.country_code == UI_PARAMS.LION_REGION).first()

                if location is not None:
                    # Update attributes of the existing record
                    for key, value in loc_data.items():
                        setattr(location, key, value)
                else:
                    # Create a new record
                    location = Location(**loc_data)
                    LION_SQLALCHEMY_DB.session.add(location)

                LION_SQLALCHEMY_DB.session.commit()

        except SQLAlchemyError as err:
            log_message(message=str(err))
            LION_SQLALCHEMY_DB.session.rollback()

            return False

        del cls.dct_locations_cache['dct_footprint']
        cls.dct_locations_cache['dct_footprint'] = cls.to_dict()

        return loc_code in cls.dct_locations_cache['dct_footprint']

    @classmethod
    def no_customers(cls):
        try:
            return [loc for loc, in cls.query.with_entities(
                cls.loc_code).filter(cls.loc_type.lower() != 'customer', cls.country_code == UI_PARAMS.LION_REGION).all()]

        except SQLAlchemyError as err:
            log_message(message=str(err))
            return []

        except Exception:
            log_exception(popup=False)
            return []

    @classmethod
    def update_loc_names(cls):

        if is_file_updated(filename='LocationNames.xlsx', Path=LION_FILES_PATH):

            try:
                __df_user_locs = read_excel(
                    join(LION_FILES_PATH, 'LocationNames.xlsx'), sheet_name='locs')

                __df_user_locs.set_index('LocationCode', inplace=True)

                
                dct_loc_names = __df_user_locs.LocationName.to_dict()

            except Exception as err:
                dct_loc_names = {}

            if dct_loc_names:

                try:
                    for loc_code in dct_loc_names:

                        location = cls.query.filter(
                            cls.loc_code == loc_code, cls.country_code == UI_PARAMS.LION_REGION).first()

                        if location is not None:
                            cls.location_name = dct_loc_names[loc_code]
                            LION_SQLALCHEMY_DB.session.commit()

                except SQLAlchemyError as err:

                    log_message(message=str(err))
                    LION_SQLALCHEMY_DB.session.rollback()

                del cls.dct_locations_cache['dct_footprint']
                cls.dct_locations_cache['dct_footprint'] = cls.to_dict()

    @classmethod    
    def is_colocated(cls, loc_code1: str, loc_code2: str) -> bool:
        """
        Checks if a location is colocated with another location.
        Returns:
            bool: True if the location is colocated, False otherwise.
        """

        if not 'dct_footprint' in cls.dct_locations_cache:
            cls.dct_locations_cache['dct_footprint'] = cls.to_dict()

        try:
            lat1 = cls.dct_locations_cache['dct_footprint'].get(loc_code1, {}).get('latitude')
            lat2 = cls.dct_locations_cache['dct_footprint'].get(loc_code2, {}).get('latitude')

            if lat1 and lat2 and 0 < abs(lat1 - lat2) <= UI_PARAMS.LOCATION_COLLOCATION_THRESHOLD:

                lon1 = cls.dct_locations_cache['dct_footprint'].get(loc_code1, {}).get('longitude')
                lon2 = cls.dct_locations_cache['dct_footprint'].get(loc_code2, {}).get('longitude')

                if lon1 and lon2 and 0 < abs(lon1 - lon2) <= UI_PARAMS.LOCATION_COLLOCATION_THRESHOLD:
                    return True

        except Exception as e:
            log_exception(
                popup=False, remarks='Error checking colocated locations: ' + str(e))

        return False
