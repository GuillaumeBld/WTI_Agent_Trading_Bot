"""
Test module for file path improvements.

This module contains tests to verify that hardcoded file paths have been properly
replaced with relative paths using utility functions.
"""

import unittest
import os
import sys
import inspect

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the strategy module to test
from scripts.strategy.strategy import INDICATORS_DATA_PATH, DB_PATH
from utils import get_data_directory

class TestFilePaths(unittest.TestCase):
    """Test cases for file path improvements."""

    def test_indicators_data_path_is_relative(self):
        """Test that INDICATORS_DATA_PATH is using relative paths with utility functions."""
        # Check that the path is constructed using get_data_directory
        data_dir = get_data_directory()
        expected_path = os.path.join(data_dir, "crude_oil_with_indicators.csv")
        
        self.assertEqual(INDICATORS_DATA_PATH, expected_path)
        
        # Verify it's not a hardcoded absolute path with user-specific directories
        self.assertNotIn("/Users/guillaumebolivard", INDICATORS_DATA_PATH)

    def test_db_path_is_relative(self):
        """Test that DB_PATH is using relative paths with utility functions."""
        # Check that the path is constructed using get_data_directory
        data_dir = get_data_directory()
        expected_path = os.path.join(data_dir, "market_data.db")
        
        self.assertEqual(DB_PATH, expected_path)
        
        # Verify it's not a hardcoded absolute path with user-specific directories
        self.assertNotIn("/Users/guillaumebolivard", DB_PATH)

    def test_strategy_module_imports(self):
        """Test that the strategy module correctly imports utility functions."""
        # Import the strategy module
        import scripts.strategy.strategy as strategy
        
        # Check that the module imports the necessary utility functions
        module_source = inspect.getsource(strategy)
        self.assertIn("from utils import get_data_directory", module_source)

if __name__ == '__main__':
    unittest.main()
