import firebase_admin
from domain import ServiceException, User
from firebase_admin import auth

class Manager:
    def __init__(self, dao):
        firebase_admin.initialize_app()
        self.dao = dao
        self.user = None

    def validate_token(self, token):
        try:
            firebase_user = auth.verify_id_token(token)
            self.user = User(firebase_user["user_id"], firebase_user["name"], firebase_user["email"], firebase_user["picture"])
            if self.dao.get_user(self.user.user_id) is None:
                self.dao.create_user(self.user)
        except ValueError as e:
            raise ServiceException("Unauthorized. Provided authentication did not validate. Error: {}".format(e), 403)

    def get_ladders(self):
        return self.dao.get_ladders()

    def get_players(self, ladder_id):
        return self.dao.get_players(ladder_id)

    def get_matches(self, ladder_id, user_id):
        return self.dao.get_matches(ladder_id, user_id)

    def report_match(self, ladder_id, match):
        # TODO: Mark
        pass
