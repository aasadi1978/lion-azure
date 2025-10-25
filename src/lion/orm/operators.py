from typing import List
from lion.create_flask_app.create_app import LION_FLASK_APP
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.logger.status_logger import log_message
from lion.utils.popup_notifier import show_error
from lion.utils.print2console import display_in_console
from cachetools import TTLCache

dct_oper_cache = TTLCache(maxsize=1000, ttl=3600 * 8)


class Operator(LION_SQLALCHEMY_DB.Model):

    __scope_hierarchy__ = ["group_name"]
    __tablename__ = 'operator'

    operator_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, primary_key=True,
                            nullable=False, autoincrement=True)
    operator = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(150), nullable=False)
    group_name = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(225), nullable=True)

    def __init__(self, **attrs):
        self.operator = attrs.get('operator', '')
        self.group_name = attrs.get('group_name', LION_FLASK_APP.config.get('LION_USER_GROUP_NAME', 'To Be Validated'))

    @classmethod
    def list_operators(cls):    
        """
        Returns a dict with loc_string as keys and idx as values.
        """
        try:
            objs = cls.query.all()
            lst = sorted([obj.operator for obj in objs])
            lst.remove('FedEx Express')
            lst.insert(0, 'FedEx Express')
            return lst

        except Exception as e:
            log_message(f"list_operators failed: {str(e)}")
            show_error(f"list_operators failed: {str(e)}")
            return ['FedEx Express']

    @classmethod
    def to_dict(cls, clear_cache=False):

        if not clear_cache:
            if dct_oper_cache.get('dct_operators', {}):
                return dct_oper_cache['dct_operators']

        cls.to_dict_reverse(clear_cache=True)
        try:
            objs = cls.query.with_entities(cls.operator_id, cls.operator).all()
            if objs:
                dct_operators = dict(objs)
                dct_operators.update({0: 'Unattached'})
                return dct_operators

        except Exception as e:
            log_message(f"to_dict failed: {str(e)}")
            return {}

    @classmethod
    def to_dict_reverse(cls, clear_cache=False):

        if not clear_cache:
            if dct_oper_cache.get('dct_operators_rev', {}):
                return dct_oper_cache['dct_operators_rev']

        try:
            objs = cls.query.with_entities(cls.operator, cls.operator_id).all()
            if objs:
                dct_operators = dict(objs)
                dct_operators.update({'Unattached': 0})
                return dct_operators

        except Exception as e:
            log_message(f"to_dict_reverse failed: {str(e)}")
            return {}

    @classmethod
    def clear_all(cls):

        try:
            cls.query.delete()
            LION_SQLALCHEMY_DB.session.commit()

        except Exception as err:
            log_message(f'clearing table failed! {str(err)}')

    @classmethod
    def delete_operators(cls, operator_names: List | str):

        try:
            operator_names_list = []
            if isinstance(operator_names, str):
                operator_names_list = [operator_names]
            else:
                operator_names_list.extend(operator_names)

            cls.query.filter(cls.operator.in_(operator_names_list)).delete(synchronize_session=False)
            LION_SQLALCHEMY_DB.session.commit()

            if cls.query.filter(cls.operator.in_(operator_names_list)).all() is not None:
                log_message(f'Deleting operators {operator_names_list} failed!')

        except Exception as err:
            log_message(f'clearing table failed! {str(err)}')
        
        log_message(f'Deleted operators: {operator_names_list}')

    @classmethod
    def get_operator_id(cls, operator_name=''):

        try:
            OprObj = cls.query.with_entities(
                cls.operator_id).filter(cls.operator == operator_name).first()

            if not OprObj:
                return cls.add_operator(operator_name=operator_name)

            return OprObj[0]

        except Exception as e:
            LION_SQLALCHEMY_DB.session.rollback()
            log_message(f'Getting operator id for {operator_name} failed! {str(e)}')

        return None

    @classmethod
    def add_operator(cls, operator_name=''):

        if operator_name == '':
            return None

        try:

            operator_ = cls.query.filter(cls.operator == operator_name).first()
            if not operator_:

                new_obj = Operator(
                    operator=operator_name
                )

                LION_SQLALCHEMY_DB.session.add(new_obj)
                LION_SQLALCHEMY_DB.session.commit()

                cls.to_dict_reverse(clear_cache=True)
                cls.to_dict(clear_cache=True)

                operator_ = cls.query.filter(
                    cls.operator == operator_name).first()

            return operator_.operator_id

        except Exception as e:

            display_in_console(f'adding operator {operator_name} failed! {str(e)}')
            LION_SQLALCHEMY_DB.session.rollback()
            log_message(f'adding operator {operator_name} failed! {str(e)}')

        return None

    @classmethod
    def add_operators(cls, list_of_operators=[]):

        list_of_operators = [x for x in list_of_operators
                             if x not in cls.list_operators()]

        if list_of_operators:

            for oprt in list_of_operators:

                try:
                    new_obj = Operator(
                        operator=oprt
                    )

                    LION_SQLALCHEMY_DB.session.add(new_obj)
                    LION_SQLALCHEMY_DB.session.commit()

                except Exception as e:

                    LION_SQLALCHEMY_DB.session.rollback()
                    log_message(f'adding operator {oprt} failed! {str(e)}')

        cls.to_dict_reverse(clear_cache=True)
        cls.to_dict(clear_cache=True)

