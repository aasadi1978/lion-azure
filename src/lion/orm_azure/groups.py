from sqlalchemy import and_
from lion.create_flask_app.create_app import LION_FLASK_APP
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.logger.exception_logger  import log_exception
from lion.orm_azure.scoped_mixins import BASE, GroupScopedBase


class GroupName(BASE, GroupScopedBase):

    __bind_key__ = 'azure_sql_db'
    __tablename__ = 'groups'

    id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, nullable=False,
                         primary_key=True, autoincrement=True)
    group_name = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=False,
                             primary_key=True)
    
    user_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True, default='1')
    object_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=False)


    def __init__(self, **attrs):
        self.group_name = attrs.get('group_name', '')
        self.user_id = str(attrs.get('user_id', LION_FLASK_APP.config['LION_USER_ID']))
        self.object_id = str(attrs.get('object_id', ''))

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

