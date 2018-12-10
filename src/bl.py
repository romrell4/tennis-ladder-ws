import firebase_admin
from domain import ServiceException
from firebase_admin import auth

class Manager:
    def __init__(self, dao):
        firebase_admin.initialize_app()
        self.user = None
        self.dao = dao

    @staticmethod
    def validate_token(token):
        try:
            return auth.verify_id_token(token)
        except ValueError as e:
            raise ServiceException("Unauthorized. Provided authentication did not validate. Error: {}".format(e), 403)

    def login(self):
        # Look up the firebase_user in our da

        # If they exist, return the user

        # If they don't, create the user and return it
        pass

    def get_ladders(self):
        pass

    def get_players(self, ladder_id):
        pass

    def get_matches(self, ladder_id, user_id):
        pass

    def report_match(self, ladder_id, match):
        # TODO: Mark
        pass
