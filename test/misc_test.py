import os.path
import unittest


class Test(unittest.TestCase):
    def test_that_firebase_credentials_are_present(self):
        self.assertTrue(os.path.exists("../src/firebase_creds.json"))
