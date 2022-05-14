import firebase_admin
from firebase_admin import auth


class FirebaseClient:
    def get_firebase_user(self, token): pass


class FirebaseClientImpl(FirebaseClient):
    def __init__(self):
        firebase_admin.initialize_app()

    def get_firebase_user(self, token):
        return auth.verify_id_token(token)
