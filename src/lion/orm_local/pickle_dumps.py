from lion.create_flask_app.create_app import LION_FLASK_APP
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.logger.exception_logger  import log_exception
from pickle import dumps as pickle_dumps, loads as pickle_loads


class PickleDumps(LION_SQLALCHEMY_DB.Model):

    __tablename__ = 'pickle_dumps'
    __bind_key__ = 'local_data_bind'

    filename = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(150), nullable=False,
                         primary_key=True)

    content = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.LargeBinary, nullable=True)

    user_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True, default='1')
    group_name = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(150), nullable=True)

    def __init__(self, **attrs):
        self.filename = attrs.get('filename', '')
        self.content = attrs.get('content', None)
        self.user_id = str(attrs.get('user_id', LION_FLASK_APP.config['LION_USER_ID']))
        self.group_name = str(attrs.get('group_name', LION_FLASK_APP.config['LION_USER_GROUP_NAME']))

    @classmethod
    def get_content(cls, filename=None, method_if_null=None, if_null=None):
        """
        Tries to load the content object and if not available,
        it will dump the class/instance provided in instance_if_null
        """
        try:
            pickle_file = cls.query.filter_by(
                filename=filename).first()

            if pickle_file is not None:
                __obj = pickle_loads(pickle_file.content)
                if __obj is not None:
                    return __obj

                return if_null
            else:
                if method_if_null is not None:

                    __obj = method_if_null()
                    cls.update(filename=filename,
                               obj=__obj)

                    return __obj

            return if_null

        except Exception:
            log_exception()
            return if_null

    @classmethod
    def update(cls, filename=None, obj=None):

        try:

            if obj is not None:

                pickle_file = cls.query.filter_by(
                    filename=filename).first()

                if pickle_file is not None:
                    pickle_file.content = pickle_dumps(obj)

                else:
                    pickle_file = PickleDumps(
                        filename=filename, content=None)

                    pickle_file.content = pickle_dumps(obj)
                    LION_SQLALCHEMY_DB.session.add(pickle_file)

                LION_SQLALCHEMY_DB.session.commit()
                return 'OK'

        except Exception:
            LION_SQLALCHEMY_DB.session.rollback()
            return log_exception(f"Storing pickle file {filename} failed.")

    @classmethod
    def remove(cls, filename=None):
        try:
            # Attempt to find the existing record.
            pickle_file = cls.query.filter_by(filename=filename).first()

            # If found, delete it.
            if pickle_file is not None:
                LION_SQLALCHEMY_DB.session.delete(pickle_file)
                LION_SQLALCHEMY_DB.session.commit()
                return 'Deleted'
            else:
                # If not found, indicate that there was nothing to delete.
                return 'No record to delete'

        except Exception as err:
            LION_SQLALCHEMY_DB.session.rollback()
            return log_exception()
