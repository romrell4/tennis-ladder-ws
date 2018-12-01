import unittest

from bl import Manager

class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = Manager()