import logging
from flask import g, session
from flask import has_request_context

class SessionManager:

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        
        return cls._instance

    def __init__(self):

        if not self._initialized:
            self._initialized = True

    @classmethod
    def initialize(cls):
        pass

    @classmethod
    def get_isntance(cls):
        return cls()
    
    def set_user_context(self, *args, **kwargs):
        try:

            if has_request_context():
                user = session.get('user', None) or g.get('user', {})
                user.update({k: v for k, v in kwargs})
                setattr(g, 'user', user)
                session['user'] = user

        except Exception:
            logging.error(f"Failed to update session and g context")

    def get(self, *args):
        try:
            if len(args) == 1:
                args = [args[0], None]
            elif len(args) > 2:
                args = args[:2]

            if has_request_context():
                return session.get('user', {}).get(args[0], args[1]) or g.get('user', {}).get(args[0], args[1])
        
        except Exception as e:
            logging.error(f"Failed to update session arguemnts.")

            return None

SESSION_MANAGER = SessionManager.get_isntance()