from lion.logger.exception_logger import log_exception
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError, OperationalError
from lion.logger.status_logger import log_message
from cachetools import TTLCache
from lion.orm_azure.scoped_mixins import BASE, GroupScopedBase


class LocationMapper(BASE, GroupScopedBase):

    __bind_key__ = 'azure_sql_db'
    __tablename__ = 'loc_code_mapping'
    
    loc_map_cache = TTLCache(maxsize=1000, ttl=8 * 3600)

    loc_code = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(20),
                         nullable=False, primary_key=True)
    mapping = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String, nullable=False)
    user_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True)
    group_name = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(150), nullable=True)
    
    def __init__(self, **loc_data):
        self.loc_code = loc_data.get('loc_code', '')
        self.mapping = loc_data.get('mapping', '')
        self.user_id = str(loc_data.get('user_id', ''))
        self.group_name = str(loc_data.get('group_name', ''))

    def __repr__(self):
        return f"<LocationMapper(loc_code='{self.loc_code}', mapping='{self.mapping}', user_id='{self.user_id}', group_name='{self.group_name}')>"

    @classmethod
    def clear_cache(cls):
        cls.loc_map_cache.clear()
        cls.loc_map_cache = TTLCache(maxsize=1000, ttl=8 * 3600)

    @classmethod
    def is_mapped(cls, loc_code1: str, loc_code2: str) -> bool:
        """
        Checks if a location is mapped.
        Returns:
            bool: True if the location is mapped, False otherwise.
        """
        if not 'dct_loc_mapping' in cls.loc_map_cache:
            cls.loc_map_cache['dct_loc_mapping'] = cls.get_mappings()

        return (cls.loc_map_cache['dct_loc_mapping'].get(loc_code1, loc_code1) == loc_code2) or (
            cls.loc_map_cache['dct_loc_mapping'].get(loc_code2, loc_code2) == loc_code1
        )

    @classmethod
    def get_mappings(cls) -> dict:
        """
        Retrieves and caches the location mappings from the database, e.g., {'MV9_H': 'MV9', 'MV9_L': 'MV9', ...}.
        Returns:
            dict: A dictionary mapping location codes to their corresponding mappings.
        If the mappings are already cached in `cls.loc_map_cache` under the key 'dct_loc_mapping',
        the cached value is returned. Otherwise, the method queries the database for all location
        mappings, caches the result, and returns it.
        Handles database errors (`ProgrammingError`, `OperationalError`) by logging the exception,
        caching an empty dictionary, and returning an empty dictionary. Any other exceptions are
        also logged and result in an empty dictionary being returned.
        """

        if 'dct_loc_mapping' in cls.loc_map_cache:
            return cls.loc_map_cache['dct_loc_mapping']
       
        try: 

            results = LION_SQLALCHEMY_DB.session.query(cls).all()
            dct_loc_mapping = {r.loc_code: r.mapping for r in results}

            cls.loc_map_cache['dct_loc_mapping'] = dct_loc_mapping

            return dct_loc_mapping
        except (ProgrammingError, OperationalError) as e:
            log_exception(popup=False, remarks=f'Could not fetch location mapping: {str(e)}')
            cls.loc_map_cache['dct_loc_mapping'] = {}
            return {}

        except Exception:
            log_exception(popup=False, remarks='Could not fetch location type')
            return {}

    @classmethod
    def location_map(cls, loc_code=None) -> str:
        """
        Returns the mapping of location based on the loc_code.
        """

        if 'dct_loc_mapping' not in cls.loc_map_cache:
            cls.location_types()

        try:
            if loc_code:
                return cls.loc_map_cache['dct_loc_mapping'][loc_code]

        except Exception:
            log_exception(popup=False, remarks='Could not fetch location mapping')
            return 'Unknown-Type'

    @classmethod
    def upsert(cls, **loc_data):

        loc_code = loc_data.get('loc_code', '')
        try:
            if loc_code != '':

                location = cls.query.filter_by(
                    loc_code=loc_data['loc_code']).first()

                if location is not None:
                    # Update attributes of the existing record
                    for key, value in loc_data.items():
                        setattr(location, key, value)
                else:
                    # Create a new record
                    location = LocationMapper(**loc_data)
                    LION_SQLALCHEMY_DB.session.add(location)

                LION_SQLALCHEMY_DB.session.commit()

        except Exception as err:
            log_message(message=str(err))
            LION_SQLALCHEMY_DB.session.rollback()

        cls.clear_cache()
        cls.loc_map_cache['dct_loc_mapping'] = cls.get_mappings()

    @classmethod
    def update(cls, **loc_data):

        loc_code = loc_data.get('loc_code', '')
        try:
            if loc_code != '':

                location = cls.query.filter_by(
                    loc_code=loc_data['loc_code']).first()

                if location is not None:
                    # Update attributes of the existing record
                    for key, value in loc_data.items():
                        setattr(location, key, value)
                else:
                    # Create a new record
                    location = LocationMapper(**loc_data)
                    LION_SQLALCHEMY_DB.session.add(location)

                LION_SQLALCHEMY_DB.session.commit()

        except SQLAlchemyError as err:
            log_message(message=str(err))
            LION_SQLALCHEMY_DB.session.rollback()

            return False

        cls.clear_cache()
        cls.loc_map_cache['dct_loc_mapping'] = cls.get_mappings()

        return loc_code in cls.loc_map_cache['dct_loc_mapping']



if __name__ == '__main__':
    from lion.create_flask_app.create_app import LION_FLASK_APP
    with LION_FLASK_APP.app_context():
        print(LocationMapper.get_mappings())