#!/usr/bin/env python
"""
Test runner for pydocass components.
Run this script from the backend directory to execute all tests.
"""
import unittest
import sys


if __name__ == "__main__":
    # Automatically discover and run all tests
    test_suite = unittest.defaultTestLoader.discover('tests')
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Return proper exit code based on test results
    sys.exit(not result.wasSuccessful()) 