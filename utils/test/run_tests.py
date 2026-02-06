#!/usr/bin/env python
"""
Test runner for version range logic tests.

This script runs the comprehensive test suite for the version range logic
in generate_dependency_table.py.
"""

import sys
import os
import unittest

# Add the utils directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_tests():
    """Run all version range tests."""
    print("Running version range logic tests...")
    print("=" * 50)
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Load lean tests aligned with current implementation.
    suite = unittest.TestSuite()
    suite.addTests(loader.discover(start_dir, pattern='test_version_ranges.py'))
    suite.addTests(loader.discover(start_dir, pattern='test_uv_tree_parser.py'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("=" * 50)
    if result.wasSuccessful():
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed!")
        return 1

if __name__ == '__main__':
    sys.exit(run_tests())
