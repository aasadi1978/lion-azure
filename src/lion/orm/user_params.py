from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.logger.exception_logger  import log_exception


class UserParams(LION_SQLALCHEMY_DB.Model):

    # This tells SQLAlchemy to use the lion_user_db for this model
    __bind_key__ = 'lion_db'
    __tablename__ = 'user_params'

    param = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.TEXT, nullable=False, primary_key=True)
    val = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.TEXT, nullable=False)
    html_element_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.TEXT)
    category = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(200), nullable=False, default='General')
    default_value = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.TEXT, nullable=False, default='General')

    def __init__(self, param, val, html_element_id, category='General', default_value=''):
        self.param = param
        self.val = val
        self.html_element_id = html_element_id
        self.category = category
        self.default_value = default_value

    @classmethod
    def to_elem_dict(cls):
        return UserParams.to_dict(val_type='elem')

    @classmethod
    def optimization_default_params(cls) -> dict:

        try:
            params = UserParams.query.filter_by(category='optimization').all()
            if params is not None:
                dct = {}
                for par in params:
                    try:
                        dct[par.param] = float(par.default_value)
                    except Exception:
                        if len(par.default_value) > 0:
                            dct[par.param] = par.default_value

                return dct

        except Exception:
            return {}

    @classmethod
    def optimization_params(cls):

        try:
            params = cls.query.filter(cls.category=='optimization').all()

            if params is not None:
                dct = {}
                for par in params:
                    try:
                        dct[par.param] = float(
                            par.val) if par.param == 'MipGap' else int(float(par.val))
                    except Exception:
                        if len(par.val) > 0:
                            dct[par.param] = par.val

                return dct

        except Exception:
            return {}

    @classmethod
    def to_dict(cls, val_type='val'):

        try:
            params = UserParams.query.all()

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
    def delete_param(cls, param_to_del=''):

        if param_to_del:

            try:
                cls.query.filter(cls.param==param_to_del).delete()
                LION_SQLALCHEMY_DB.session.commit()
            except Exception:
                log_exception(f"The parameter {param_to_del} was not cleared!")

    @classmethod
    def update(cls,
               html_element_id='',
               default_value='',
               category='',
               **params):
        """
        Updates existing parameters. If param exists, only its value will be updated
        This means that if the parameter has other attributes such as html_element_id, default_value, etc.
        they will not be modified. For new parameters, if such attributes are required, they must be 
        entered/modified manually by the developer!
        """

        try:
            for param, par_val in params.items():

                existing_obj = UserParams.query.filter_by(
                    param=param
                ).first()

                if existing_obj:

                    if html_element_id:
                        existing_obj.html_element_id = html_element_id
                    
                    if par_val is not None and par_val != '':
                        existing_obj.val = par_val
                    
                    if category:
                        existing_obj.category = category

                    if default_value:
                        existing_obj.default_value = default_value

                else:
                    user_par = UserParams(
                        param=param,
                        val=par_val,
                        html_element_id=html_element_id,
                        default_value=default_value,
                        category=category)

                    LION_SQLALCHEMY_DB.session.add(user_par)

                LION_SQLALCHEMY_DB.session.commit()

        except Exception:
            log_exception()
            LION_SQLALCHEMY_DB.session.rollback()

    @classmethod
    def get_param(cls, param, if_null=None):

        try:
            usrpar = UserParams.query.filter_by(param=param).first()

            if usrpar is not None:
                try:
                    return int(float(usrpar.val))
                except Exception:
                    return usrpar.val
            else:

                return if_null

        except Exception:
            log_exception(remarks=f"Getting param {param} failed!")
            return if_null

    @classmethod
    def get_param_element_id(cls, param, if_null=None):

        try:
            usrpar = UserParams.query.filter(UserParams.param == param).first()

            if usrpar is not None:
                return usrpar.html_element_id
            else:
                return if_null

        except Exception:
            return if_null
