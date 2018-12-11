import os
import unittest

import properties
from bl import Manager
from da import Dao
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
        cls.handler = Handler(Manager(Dao()))

    def test_handle(self):
        response = self.handler.handle({
            "resource": "/users",
            "httpMethod": "POST",
            "headers": {
                "X-Firebase-Token": properties.firebase_token
            }
        })
        print(response)