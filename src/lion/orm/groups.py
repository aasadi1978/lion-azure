from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from lion.bootstrap.constants import LION_DEFAULT_GROUP_NAME
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.logger.exception_logger  import log_exception
from lion.utils.session_manager import SESSION_MANAGER

class GroupName(LION_SQLALCHEMY_DB.Model):

    __tablename__ = 'groups'
    __scope_hierarchy__ = ["user_id"]

    id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, nullable=False,
                         primary_key=True, autoincrement=True)
    group_name = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=False)
    user_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True, default='1')

    def __init__(self, **attrs):
        self.group_name = attrs.get('group_name', SESSION_MANAGER.get('group_name'))
        self.user_id = str(attrs.get('user_id', SESSION_MANAGER.get('user_id')))


    @classmethod
    def get_user_groups(cls) -> list:

        groups = []
        try:
            groups = [grp for grp, in cls.query.with_entities(cls.group_name).all()]
        except SQLAlchemyError:
            groups = []
            log_exception(popup=False, remarks=f"get_user_groups failed.")

        except Exception:
            groups=[]
            log_exception(popup=False, remarks=f"get_user_groups failed.")
        
        return groups or [LION_DEFAULT_GROUP_NAME]
        

    @classmethod
    def set_group_name(cls, **kwargs):

        try:
            user_id = kwargs.get('user_id',  '')
            object_id = kwargs.get('object_id',  '')
            group_name = kwargs.get('group_name',  '')

            existing_user = cls.query.filter_by(user_id=user_id).first()

            if existing_user:
                existing_group = cls.query.filter(and_(cls.user_id == user_id, cls.object_id == object_id, cls.group_name == group_name)).first()
                if not existing_group:

                    new_group = cls(
                        user_id=user_id,
                        object_id=object_id,
                        group_name=group_name
                    )
                    LION_SQLALCHEMY_DB.session.add(new_group)

            else:
                new_group = cls(
                    user_id=user_id,
                    object_id=object_id,
                    group_name=group_name
                )
                LION_SQLALCHEMY_DB.session.add(new_group)
            
            LION_SQLALCHEMY_DB.session.commit()

        except Exception:
            LION_SQLALCHEMY_DB.session.rollback()
            log_exception("Error occurred while setting group name")

