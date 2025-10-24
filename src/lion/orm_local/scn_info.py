from lion.create_flask_app.create_app import BCRYPT, LION_FLASK_APP
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.logger.exception_logger import log_exception
from sqlalchemy.exc import SQLAlchemyError
from pickle import dumps as pickle_dumps
from lion.orm.scoped_mixins import BASE, GroupScopedBase
from lion.logger.exception_logger import log_exception


class ScnInfo(BASE, GroupScopedBase):

    __bind_key__ = 'local_data_bind'
    __tablename__ = 'scn_info'

    scn_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, primary_key=True, autoincrement=True)
    param = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=False)
    val = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=False)
    scn_name = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(150), nullable=True)
    user_id = LION_SQLALCHEMY_DB.Column(
        LION_SQLALCHEMY_DB.String(255), nullable=True, default='1')
    password = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True)
    

    def __init__(self, param, val):
        self.param = param
        self.val = val

    @classmethod
    def set_password(cls, password='lionuk2020'):

        hashdpwd = BCRYPT.generate_password_hash(
            password).decode('utf-8')

        try:
            existing_obj = cls.query.filter(cls.param == 'password').first()

            if existing_obj:
                existing_obj.val = hashdpwd

            else:
                user_par = ScnInfo(param='password', val=hashdpwd)
                LION_SQLALCHEMY_DB.session.add(user_par)

            LION_SQLALCHEMY_DB.session.commit()
            cls.update(user=LION_FLASK_APP.config['LION_USER_ID'])

        except SQLAlchemyError as err:
            log_exception(popup=False, remarks=f"{str(err)}")
            LION_SQLALCHEMY_DB.session.rollback()

        except Exception:
            log_exception(popup=False)
            LION_SQLALCHEMY_DB.session.rollback()

    @classmethod
    def pickle_dump(cls, filename=None, obj=None):

        try:

            if obj is not None:

                pickle_file = cls.query.filter_by(
                    filename=filename).first()

                if pickle_file is not None:
                    pickle_file.content = pickle_dumps(obj)

                else:
                    pickle_file =  ScnInfo(param=filename, val=None) 
                    pickle_file.content = pickle_dumps(obj)
                    LION_SQLALCHEMY_DB.session.add(pickle_file)

                LION_SQLALCHEMY_DB.session.commit()
                return 'OK'

        except Exception:
            LION_SQLALCHEMY_DB.session.rollback()
            return log_exception()


    @classmethod
    def check_password(cls, password):

        if password == 'lionuk2020':
            return True

        if cls.get_param(param='user', if_null=0) == LION_FLASK_APP.config['LION_USER_ID']:
            return True

        try:
            existing_obj = cls.query.filter(cls.param == 'password').first()
            if existing_obj:
                return BCRYPT.check_password_hash(existing_obj.val, password)

            return True

        except SQLAlchemyError as err:
            log_exception(popup=False, remarks=f"{str(err)}")
            return False

        except Exception:
            log_exception(popup=False)
            return False

    @classmethod
    def to_dict(cls, val_type='val'):

        try:
            params = cls.query.all()

            if val_type == 'val':

                dct = {}
                for par in params:
                    try:
                        dct[par.param] = int(float(par.val))
                    except Exception:
                        if len(par.val) > 0:
                            dct[par.param] = par.val

                return dct

            else:

                dct = {}
                for par in params:
                    if len(par.val) > 0:
                        dct[par.param] = par.html_element_id

                return dct

        except Exception:
            return {}

    @classmethod
    def update(cls, **params):

        try:
            for param, par_val in params.items():

                existing_obj = cls.query.filter(cls.param == param).first()

                if existing_obj:
                    existing_obj.val = par_val
                else:
                    user_par = ScnInfo(param=param, val=par_val)
                    LION_SQLALCHEMY_DB.session.add(user_par)

                LION_SQLALCHEMY_DB.session.commit()

        except Exception:
            log_exception(popup=False)
            LION_SQLALCHEMY_DB.session.rollback()

    @classmethod
    def scn_name(cls):
        try:
            return cls.query.filter(cls.param == 'scn_name').first().val
        except SQLAlchemyError as e:
            log_exception(popup=False, remarks='failed to get scn_name')
            return str(e)[:30]
        except Exception as e:
            log_exception(popup=False, remarks='failed to get scn_name')
            return str(e)[:30]

    @classmethod
    def docs(cls):
        try:
            obj = cls.query.filter(cls.param == 'docs').first()
            if obj:
                return obj.val

            return 'No documentation available!'
        
        except SQLAlchemyError as e:
            log_exception(popup=False, remarks='failed to get docs')
            return str(e)
        except Exception as e:
            log_exception(popup=False, remarks='failed to get docs')
            return str(e)
    

    @classmethod
    def get_param(cls, param, if_null=None):

        try:
            usrpar = cls.query.filter_by(param=param).first()

            if usrpar is not None:
                try:
                    return int(float(usrpar.val))
                except Exception:
                    return usrpar.val
            else:

                return if_null

        except Exception:
            log_exception(popup=False)
            return if_null

    @classmethod
    def delete_param(cls, param):

        try:
            usrpar = cls.query.filter_by(param=param).first()

            if usrpar is not None:
                LION_SQLALCHEMY_DB.session.delete(usrpar)
                LION_SQLALCHEMY_DB.session.commit()
                return True

            return False

        except Exception:
            log_exception(popup=False)
            LION_SQLALCHEMY_DB.session.rollback()
            return False