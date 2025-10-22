from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB


class TempShiftMovementEntry(LION_SQLALCHEMY_DB.Model):

    __bind_key__ = 'temp_local_schedule_db'
    __tablename__ = 'local_movements'

    movement_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, primary_key=True, nullable=False)
    extended_str_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Text, nullable=True)
    str_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Text, nullable=False)
    loc_string = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Text, nullable=False, default='')
    tu_dest = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Text, nullable=False, default='')
    is_loaded = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Boolean, nullable=False, default=False)
    shift_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, nullable=True)

    def __init__(self, **attrs):

        super().__init__(**attrs)

        self.str_id = attrs.get('str_id', '')
        self.shift_id = attrs.get('shift_id', 0)

        is_repos = self.str_id.lower().endswith(
            '|empty') or '|empty|' in self.str_id.lower()

        self.movement_id = attrs.get('movement_id', 0)
        self.is_loaded = not is_repos
        self.loc_string = attrs.get('loc_string', '')
        self.tu_dest = attrs.get('tu_dest', '')

class AzureShiftMovementEntry(LION_SQLALCHEMY_DB.Model):

    __bind_key__ = 'azure_sql_db'
    __tablename__ = 'local_movements'

    movement_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, primary_key=True, nullable=False)
    extended_str_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True)
    str_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=False)
    loc_string = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=False, default='')
    tu_dest = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=False, default='')
    is_loaded = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Boolean, nullable=False, default=False)
    shift_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, nullable=True)

    def __init__(self, **attrs):

        super().__init__(**attrs)

        self.str_id = attrs.get('str_id', '')
        self.shift_id = attrs.get('shift_id', 0)

        is_repos = self.str_id.lower().endswith(
            '|empty') or '|empty|' in self.str_id.lower()

        self.movement_id = attrs.get('movement_id', 0)
        self.is_loaded = not is_repos
        self.loc_string = attrs.get('loc_string', '')
        self.tu_dest = attrs.get('tu_dest', '')