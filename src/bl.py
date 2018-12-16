from domain import User

class Manager:
    def __init__(self, firebase_client, dao):
        self.firebase_client = firebase_client
        self.dao = dao
        self.user = None

    def validate_token(self, token):
        if token is None: return

        try:
            firebase_user = self.firebase_client.get_firebase_user(token)
            self.user = User(firebase_user["user_id"], firebase_user["name"], firebase_user["email"], firebase_user["picture"])
            if self.dao.get_user(self.user.user_id) is None:
                self.dao.create_user(self.user)
        except (KeyError, ValueError):
            pass

    def get_ladders(self):
        return self.dao.get_ladders()

    def get_players(self, ladder_id):
        # The database handles all the sorting and derived fields
        return self.dao.get_players(ladder_id)

    def get_matches(self, ladder_id, user_id):
        return self.dao.get_matches(ladder_id, user_id)

    def report_match(self, ladder_id, match):
        # TODO: Mark
        # TODO: Authorize the logged in user
        pass
