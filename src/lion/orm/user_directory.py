from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB

# you should consistently store digital_id as a string (e.g., NVARCHAR(100)) both in the user_directory and in 
# any other tables (like shipments, resources, etc.) where user-level access is needed.

class UserDirectory(LION_SQLALCHEMY_DB.Model):

    __tablename__ = 'user_directory'

    user_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=False, primary_key=True)
    object_id = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(255), nullable=True)

    def __init__(self, **attrs):
        self.user_id = str(attrs.get('user_id', ''))
        self.object_id = str(attrs.get('object_id', ''))