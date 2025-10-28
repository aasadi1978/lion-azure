from flask import g, session
from lion.bootstrap.constants import LION_DEFAULT_GROUP_NAME
from lion.logger.exception_logger import log_exception
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.utils.session_manager import SESSION_MANAGER
from lion.utils.utcnow import utcnow


class ScenarioSequence(LION_SQLALCHEMY_DB.Model):
    __tablename__ = "scenario_sequence"

    id = LION_SQLALCHEMY_DB.Column(
        LION_SQLALCHEMY_DB.Integer,
        primary_key=True,
        autoincrement=True
    )
    created_at = LION_SQLALCHEMY_DB.Column(
        LION_SQLALCHEMY_DB.DateTime,
        default=utcnow(),
        nullable=False
    )

    group_name = LION_SQLALCHEMY_DB.Column(
        LION_SQLALCHEMY_DB.String(255),
        default=SESSION_MANAGER.get('group_name'),
        nullable=False
    )

    def __init__(self, **attrs):
        self.group_name = attrs.get('group_name', )

    @classmethod
    def get_next_scenario_id(cls):
        """
        Inserts a new row into the scenario_sequence table
        and returns the auto-generated unique scenario ID.
        """
        try:
            new_seq = cls()
            LION_SQLALCHEMY_DB.session.add(new_seq)
            LION_SQLALCHEMY_DB.session.flush()  # Ensures ID is generated immediately
            return new_seq.id

        except Exception as e:
            log_exception(
                popup=False,
                remarks=f"Failed to get next scenario id: {e}"
            )
            return None
