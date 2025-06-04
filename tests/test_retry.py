"""
Test module for retry utilities.

This module contains tests for the retry and retry_with_result decorators.
"""

import unittest
import time
from unittest.mock import Mock, patch

# Import retry utilities
from utils.retry import retry, retry_with_result, RetryError

class TestRetryDecorators(unittest.TestCase):
    """Test cases for retry decorators."""

    def test_retry_success(self):
        """Test that a function succeeds after retrying."""
        mock_func = Mock(side_effect=[ValueError("First failure"), ValueError("Second failure"), "success"])
        
        @retry(max_tries=3, delay=0.1, backoff=1.0, exceptions=ValueError)
        def test_func():
            return mock_func()
        
        result = test_func()
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 3)

    def test_retry_all_failures(self):
        """Test that RetryError is raised when all attempts fail."""
        mock_func = Mock(side_effect=ValueError("Consistent failure"))
        
        @retry(max_tries=3, delay=0.1, backoff=1.0, exceptions=ValueError)
        def test_func():
            return mock_func()
        
        with self.assertRaises(RetryError) as cm:
            test_func()
        self.assertIsInstance(cm.exception.last_exception, ValueError)
        self.assertEqual(mock_func.call_count, 3)

    def test_retry_with_result_success(self):
        """Test that retry_with_result returns when validator returns True."""
        mock_func = Mock(side_effect=[None, [], ["data"]])
        
        @retry_with_result(max_tries=3, delay=0.1, validator=lambda x: x and len(x) > 0)
        def test_func():
            return mock_func()
        
        result = test_func()
        self.assertEqual(result, ["data"])
        self.assertEqual(mock_func.call_count, 3)

    def test_retry_with_result_all_invalid(self):
        """Test that retry_with_result returns last result when all attempts return invalid results."""
        last_result = []
        mock_func = Mock(side_effect=[None, [], last_result])
        
        @retry_with_result(max_tries=3, delay=0.1, validator=lambda x: x and len(x) > 0)
        def test_func():
            return mock_func()
        
        result = test_func()
        self.assertEqual(result, last_result)
        self.assertEqual(mock_func.call_count, 3)

    def test_retry_with_jitter(self):
        """Test that retry with jitter works correctly."""
        mock_func = Mock(side_effect=[ValueError("First failure"), ValueError("Second failure"), "success"])
        mock_sleep = Mock()
        
        with patch('time.sleep', mock_sleep):
            @retry(max_tries=3, delay=1.0, backoff=2.0, exceptions=ValueError, jitter=True)
            def test_func():
                return mock_func()
            
            result = test_func()
        
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)  # Called twice for the two failures

if __name__ == '__main__':
    unittest.main()
