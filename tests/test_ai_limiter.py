# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.
# Unauthorized copying, distribution, or use of this file,
# via any medium, is strictly prohibited without the express
# written permission of TrailLensCo.

"""Unit tests for ai_limiter module."""

import os
import sys
import unittest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_limiter import AICallbackLimiter, AILimitError


class TestAICallbackLimiter(unittest.TestCase):
    """Tests for AICallbackLimiter class."""

    def test_default_limits(self):
        """Test default limiter limits."""
        limiter = AICallbackLimiter()

        self.assertEqual(limiter.max_total, 50)
        self.assertEqual(limiter.total_calls, 0)
        self.assertEqual(limiter.total_tokens, 0)

    def test_custom_limits(self):
        """Test limiter with custom limits."""
        limiter = AICallbackLimiter(
            max_total=100,
            limits={'pattern': 25, 'clue': 10}
        )

        self.assertEqual(limiter.max_total, 100)
        self.assertEqual(limiter.limits['pattern'], 25)
        self.assertEqual(limiter.limits['clue'], 10)

    def test_can_call_within_limit(self):
        """Test can_call returns True when within limits."""
        limiter = AICallbackLimiter(max_total=10)

        self.assertTrue(limiter.can_call('test'))

    def test_can_call_at_limit(self):
        """Test can_call returns False when at limit."""
        limiter = AICallbackLimiter(max_total=2)

        limiter.record_call('test')
        limiter.record_call('test')

        self.assertFalse(limiter.can_call('test'))

    def test_can_call_type_limit(self):
        """Test can_call respects type-specific limits."""
        limiter = AICallbackLimiter(
            max_total=100,
            limits={'pattern': 2}
        )

        limiter.record_call('pattern')
        limiter.record_call('pattern')

        self.assertFalse(limiter.can_call('pattern'))
        self.assertTrue(limiter.can_call('other'))

    def test_record_call(self):
        """Test recording calls updates counters."""
        limiter = AICallbackLimiter()

        limiter.record_call('test', tokens_used=100)
        limiter.record_call('test', tokens_used=150)

        self.assertEqual(limiter.total_calls, 2)
        self.assertEqual(limiter.total_tokens, 250)
        self.assertEqual(limiter.counts['test'], 2)

    def test_get_remaining(self):
        """Test getting remaining calls."""
        limiter = AICallbackLimiter(max_total=10)

        limiter.record_call('test')
        limiter.record_call('test')
        limiter.record_call('test')

        self.assertEqual(limiter.get_remaining(), 7)

    def test_get_remaining_type_specific(self):
        """Test getting remaining calls for specific type."""
        limiter = AICallbackLimiter(
            max_total=100,
            limits={'pattern': 5}
        )

        limiter.record_call('pattern')
        limiter.record_call('pattern')

        self.assertEqual(limiter.get_remaining('pattern'), 3)

    def test_get_stats(self):
        """Test getting statistics."""
        limiter = AICallbackLimiter(max_total=50)

        limiter.record_call('test1', tokens_used=100)
        limiter.record_call('test2', tokens_used=200)

        stats = limiter.get_stats()

        self.assertEqual(stats['total_calls'], 2)
        self.assertEqual(stats['total_tokens'], 300)
        self.assertEqual(stats['remaining_calls'], 48)
        self.assertEqual(stats['calls_by_type']['test1'], 1)
        self.assertEqual(stats['calls_by_type']['test2'], 1)

    def test_on_limit_reached_callback(self):
        """Test callback when limit is reached."""
        callback_called = []

        def callback(prompt_type):
            callback_called.append(prompt_type)

        limiter = AICallbackLimiter(max_total=1)
        limiter.on_limit_reached(callback)

        limiter.record_call('test')

        # This should trigger the callback
        limiter.can_call('test')

        self.assertEqual(callback_called, ['test'])

    def test_reset(self):
        """Test resetting the limiter."""
        limiter = AICallbackLimiter()

        limiter.record_call('test', tokens_used=100)
        limiter.record_call('test', tokens_used=100)

        limiter.reset()

        self.assertEqual(limiter.total_calls, 0)
        self.assertEqual(limiter.total_tokens, 0)
        self.assertEqual(len(limiter.call_history), 0)

    def test_is_exhausted(self):
        """Test checking if limiter is exhausted."""
        limiter = AICallbackLimiter(max_total=2)

        self.assertFalse(limiter.is_exhausted())

        limiter.record_call('test')
        limiter.record_call('test')

        self.assertTrue(limiter.is_exhausted())

    def test_get_type_usage(self):
        """Test getting usage for specific type."""
        limiter = AICallbackLimiter(
            max_total=100,
            limits={'pattern': 10}
        )

        limiter.record_call('pattern', tokens_used=50, success=True)
        limiter.record_call('pattern', tokens_used=30, success=True)
        limiter.record_call('pattern', tokens_used=20, success=False)

        usage = limiter.get_type_usage('pattern')

        self.assertEqual(usage['calls'], 3)
        self.assertEqual(usage['limit'], 10)
        self.assertEqual(usage['remaining'], 7)
        self.assertEqual(usage['tokens'], 100)
        self.assertEqual(usage['success_count'], 2)

    def test_success_rate(self):
        """Test success rate calculation."""
        limiter = AICallbackLimiter()

        limiter.record_call('test', success=True)
        limiter.record_call('test', success=True)
        limiter.record_call('test', success=False)

        stats = limiter.get_stats()

        self.assertAlmostEqual(stats['success_rate'], 2/3)

    def test_get_recent_calls(self):
        """Test getting recent call history."""
        limiter = AICallbackLimiter()

        limiter.record_call('test1')
        limiter.record_call('test2')
        limiter.record_call('test3')

        recent = limiter.get_recent_calls(2)

        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0]['prompt_type'], 'test2')
        self.assertEqual(recent[1]['prompt_type'], 'test3')

    def test_to_dict(self):
        """Test converting limiter state to dict."""
        limiter = AICallbackLimiter(max_total=50, limits={'test': 10})

        limiter.record_call('test', tokens_used=100)

        state = limiter.to_dict()

        self.assertEqual(state['max_total'], 50)
        self.assertEqual(state['limits']['test'], 10)
        self.assertEqual(state['total_calls'], 1)
        self.assertEqual(state['total_tokens'], 100)

    def test_from_config(self):
        """Test creating limiter from config dict."""
        config = {
            'max_ai_callbacks': 75,
            'limits': {
                'pattern_word_generation': 30,
                'clue_generation_batch': 5
            }
        }

        limiter = AICallbackLimiter.from_config(config)

        self.assertEqual(limiter.max_total, 75)
        self.assertEqual(limiter.limits['pattern_word_generation'], 30)


class TestAILimitError(unittest.TestCase):
    """Tests for AILimitError exception."""

    def test_error_message(self):
        """Test error message format."""
        error = AILimitError('pattern', 25)

        self.assertEqual(error.prompt_type, 'pattern')
        self.assertEqual(error.limit, 25)
        self.assertIn('pattern', str(error))
        self.assertIn('25', str(error))


if __name__ == '__main__':
    unittest.main()
