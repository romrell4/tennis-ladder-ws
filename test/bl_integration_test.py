import os
import unittest

import properties
from firebase_client import FirebaseClientImpl
from bl import ManagerImpl
from da import DaoImpl


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "../src/firebase_creds.json"
        os.environ["DB_HOST"] = properties.db_host
        os.environ["DB_USERNAME"] = properties.db_username
        os.environ["DB_PASSWORD"] = properties.db_password
        os.environ["DB_DATABASE_NAME"] = properties.db_database_name
        cls.manager = ManagerImpl(FirebaseClientImpl(), DaoImpl())

    def test_validate_token(self):
        # Test null token
        self.manager.validate_token(None)
        self.assertIsNone(self.manager.user)

        # Test empty token
        self.manager.validate_token("")
        self.assertIsNone(self.manager.user)

        # Test partially correct format
        self.manager.validate_token("a.bad.token")
        self.assertIsNone(self.manager.user)

        # In order to run this test, you'll have to generate a new valid token and place it in the properties file
        # self.manager.validate_token(properties.firebase_token)
        # self.assertIsNotNone(self.manager.user)
