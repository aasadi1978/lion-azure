from lion.create_flask_app.create_app import LION_FLASK_APP
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB


class Cost(LION_SQLALCHEMY_DB.Model):
    
    __scope_hierarchy__ = ["group_name"]
    __tablename__ = 'Cost'

    operator = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(200), primary_key=True)
    cost_component = LION_SQLALCHEMY_DB.Column(
        LION_SQLALCHEMY_DB.String(200), primary_key=True, nullable=False)

    value = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Double, nullable=False, default=0)
    group_name = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(150), nullable=True)

    def __init__(self, **attrs):
        self.operator = attrs.get('operator', '')
        self.cost_component = attrs.get('cost_component', '')
        self.value = attrs.get('value', 0)
        self.group_name = attrs.get('group_name', LION_FLASK_APP.config['LION_USER_GROUP_NAME'])

    @classmethod
    def to_dict(cls, operator=None):
        try:
            if operator:
                obj_costs = Cost.query.filter_by(operator=operator).all()

                __dct_cost = {}
                for obj_cost in obj_costs:
                    __dct_cost[obj_cost.cost_component] = obj_cost.value
                return __dct_cost

            else:
                obj_costs = Cost.query.all()
                __dct_cost = {}
                for obj_cost in obj_costs:
                    if obj_cost.operator not in __dct_cost:
                        __dct_cost[obj_cost.operator] = {}
                    __dct_cost[obj_cost.operator][obj_cost.cost_component] = obj_cost.value

                return __dct_cost

        except Exception:
            return {}
