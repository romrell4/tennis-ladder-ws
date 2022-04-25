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
            "resource": "/users/{user_id}",
            "pathParameters": {
                "user_id": "erwNxS1AGZVTIakvViXrmeRbasI3"
            },
            "httpMethod": "PUT",
            "body": '{"user_id":"erwNxS1AGZVTIakvViXrmeRbasI3","name":"Test1 Romrell","photo_url":"https://www.aceshowbiz.com/images/photo/roger_federer.jpg","email":"romrelltest1@gmail.com"}',
            "headers": {
                "X-Firebase-Token": properties.firebase_token
            }
        })
        print(response)