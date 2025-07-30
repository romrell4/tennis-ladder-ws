import os
import unittest

import properties
from bl import ManagerImpl
from firebase_client import FirebaseClientImpl
from da import DaoImpl
from handler import Handler


# This test is not in our test suite, because you will need to have a valid token (obtained from the app) to run it.
# This should work as a system to test step through code as if we were really executing
class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "../src/firebase_creds.json"
        os.environ["DB_HOST"] = properties.db_host
        os.environ["DB_USERNAME"] = properties.db_username
        os.environ["DB_PASSWORD"] = properties.db_password
        os.environ["DB_DATABASE_NAME"] = properties.db_database_name
        cls.handler = Handler(ManagerImpl(FirebaseClientImpl(), DaoImpl()))

    def test(self):
        response = self.handler.handle({
            "resource": "/ladders/{ladder_id}/matches",
            "pathParameters": {
                "ladder_id": "24"
            },
            "httpMethod": "POST",
            "body": '{"ladder_id":24,"loser":{"borrowed_points":0,"earned_points":0,"ladder_id":24,"losses":0,"ranking":19,"score":0,"user":{"availability_text":"Never","email":"romrelltest1@gmail.com","name":"Test1 Romrell","phone_number":"555-555-5555","photo_url":"https://www.aceshowbiz.com/images/photo/roger_federer.jpg","user_id":"erwNxS1AGZVTIakvViXrmeRbasI3"},"wins":0},"loser_points":0,"loser_set1_score":1,"loser_set2_score":4,"match_date":"2025-07-30T12:46:30-07","match_id":0,"winner":{"borrowed_points":0,"earned_points":0,"ladder_id":24,"losses":0,"ranking":19,"score":0,"user":{"availability_text":"","email":"emromrell14@gmail.com","name":"Eric Romrell","phone_number":"503-679-0157","photo_url":"https://lh3.googleusercontent.com/-ysvBgveJOBk/AAAAAAAAAAI/AAAAAAAAAY8/az_oaaI-jYU/s96-c/photo.jpg","user_id":"MHaKAIbzhiWTVwihLeEgC9U2Jj73"},"wins":0},"winner_points":0,"winner_set1_score":6,"winner_set2_score":6}',
            "headers": {
                "X-Firebase-Token": properties.firebase_token
            }
        })
        print(response)
