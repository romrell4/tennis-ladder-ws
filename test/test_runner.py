# These lines allow us to import the src module
import sys
import os

sys.path.append(os.path.abspath(__file__ + "/../../"))
sys.path.append(os.path.abspath(__file__ + "/../../src/"))

import unittest

import handler_unit_test
import bl_unit_test
import bl_integration_test
import da_integration_test
import domain_unit_test

loader = unittest.TestLoader()
suite = unittest.TestSuite()

suite.addTests(loader.loadTestsFromTestCase(handler_unit_test.Test))
suite.addTests(loader.loadTestsFromTestCase(bl_unit_test.Test))
suite.addTests(loader.loadTestsFromTestCase(bl_integration_test.Test))
suite.addTests(loader.loadTestsFromTestCase(da_integration_test.Test))
suite.addTests(loader.loadTestsFromTestCase(domain_unit_test.Test))

result = unittest.TextTestRunner(verbosity=3).run(suite)
exit(0 if result.wasSuccessful() else 1)
