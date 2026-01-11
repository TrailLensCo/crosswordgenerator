# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.
# Unauthorized copying, distribution, or use of this file,
# via any medium, is strictly prohibited without the express
# written permission of TrailLensCo.

"""
AI Callback Limiter module for crossword generator.

Tracks and enforces AI callback limits to prevent runaway token usage.
Provides detailed statistics on AI usage.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Optional, Callable, List, Any


@dataclass
class CallRecord:
    """Record of a single AI call."""
    prompt_type: str
    timestamp: float
    tokens_used: int = 0
    success: bool = True
    pattern: Optional[str] = None  # For pattern matching calls


@dataclass
class AICallbackLimiter:
    """
    Tracks and enforces AI callback limits to prevent runaway token usage.

    CRITICAL: This must be checked BEFORE every AI call.

    Attributes:
        max_total: Maximum total AI calls allowed
        limits: Per-prompt-type call limits
        on_limit_reached_handler: Optional callback when limit is reached

    Usage:
        limiter = AICallbackLimiter(max_total=50, limits={'pattern': 25})

        if limiter.can_call('pattern'):
            result = call_ai_for_pattern(pattern)
            limiter.record_call('pattern', tokens_used=100)
        else:
            result = use_fallback(pattern)
    """
    max_total: int = 50
    limits: Dict[str, int] = field(default_factory=dict)
    counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    total_calls: int = 0
    total_tokens: int = 0
    call_history: List[CallRecord] = field(default_factory=list)
    on_limit_reached_handler: Optional[Callable[[str], None]] = None
    start_time: float = field(default_factory=time.time)

    def can_call(self, prompt_type: str) -> bool:
        """
        Check if an AI call is allowed.

        Args:
            prompt_type: Type of prompt (e.g., 'pattern_word_generation')

        Returns:
            True if call is allowed, False if limit reached
        """
        # Check total limit
        if self.total_calls >= self.max_total:
            if self.on_limit_reached_handler:
                self.on_limit_reached_handler(prompt_type)
            return False

        # Check per-type limit
        type_limit = self.limits.get(prompt_type, self.max_total)
        if self.counts[prompt_type] >= type_limit:
            if self.on_limit_reached_handler:
                self.on_limit_reached_handler(prompt_type)
            return False

        return True

    def record_call(
        self,
        prompt_type: str,
        tokens_used: int = 0,
        success: bool = True,
        pattern: Optional[str] = None
    ) -> None:
        """
        Record that an AI call was made.

        Args:
            prompt_type: Type of prompt that was called
            tokens_used: Number of tokens used in the call
            success: Whether the call succeeded
            pattern: Optional pattern (for pattern matching calls)
        """
        self.counts[prompt_type] += 1
        self.total_calls += 1
        self.total_tokens += tokens_used

        # Record in history
        self.call_history.append(CallRecord(
            prompt_type=prompt_type,
            timestamp=time.time(),
            tokens_used=tokens_used,
            success=success,
            pattern=pattern,
        ))

    def get_remaining(self, prompt_type: Optional[str] = None) -> int:
        """
        Get remaining calls allowed.

        Args:
            prompt_type: Optional specific prompt type to check

        Returns:
            Number of remaining calls allowed
        """
        if prompt_type:
            type_limit = self.limits.get(prompt_type, self.max_total)
            type_remaining = type_limit - self.counts[prompt_type]
            total_remaining = self.max_total - self.total_calls
            return min(type_remaining, total_remaining)
        return self.max_total - self.total_calls

    def get_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics.

        Returns:
            Dictionary with detailed statistics
        """
        elapsed = time.time() - self.start_time

        return {
            'total_calls': self.total_calls,
            'total_tokens': self.total_tokens,
            'remaining_calls': self.get_remaining(),
            'calls_by_type': dict(self.counts),
            'elapsed_seconds': elapsed,
            'calls_per_second': (
                self.total_calls / elapsed if elapsed > 0 else 0
            ),
            'tokens_per_call': (
                self.total_tokens / self.total_calls
                if self.total_calls > 0 else 0
            ),
            'success_rate': self._calculate_success_rate(),
            'limits': {
                'total': self.max_total,
                'by_type': self.limits,
            },
        }

    def _calculate_success_rate(self) -> float:
        """Calculate success rate of calls."""
        if not self.call_history:
            return 1.0
        successful = sum(1 for c in self.call_history if c.success)
        return successful / len(self.call_history)

    def on_limit_reached(
        self,
        callback: Callable[[str], None]
    ) -> 'AICallbackLimiter':
        """
        Set callback for when limit is reached.

        Args:
            callback: Function to call when limit is reached

        Returns:
            Self for chaining
        """
        self.on_limit_reached_handler = callback
        return self

    def reset(self) -> None:
        """Reset all counters and history."""
        self.counts = defaultdict(int)
        self.total_calls = 0
        self.total_tokens = 0
        self.call_history = []
        self.start_time = time.time()

    def is_exhausted(self) -> bool:
        """Check if total limit has been exhausted."""
        return self.total_calls >= self.max_total

    def get_type_usage(self, prompt_type: str) -> Dict[str, Any]:
        """
        Get detailed usage for a specific prompt type.

        Args:
            prompt_type: Type of prompt to check

        Returns:
            Dictionary with type-specific statistics
        """
        type_limit = self.limits.get(prompt_type, self.max_total)
        type_calls = self.counts.get(prompt_type, 0)
        type_history = [c for c in self.call_history if c.prompt_type == prompt_type]

        type_tokens = sum(c.tokens_used for c in type_history)
        type_success = sum(1 for c in type_history if c.success)

        return {
            'calls': type_calls,
            'limit': type_limit,
            'remaining': type_limit - type_calls,
            'tokens': type_tokens,
            'success_count': type_success,
            'success_rate': type_success / type_calls if type_calls > 0 else 1.0,
            'utilization': type_calls / type_limit if type_limit > 0 else 0.0,
        }

    def get_recent_calls(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent call history.

        Args:
            count: Number of recent calls to return

        Returns:
            List of call records as dictionaries
        """
        recent = self.call_history[-count:]
        return [
            {
                'prompt_type': c.prompt_type,
                'timestamp': c.timestamp,
                'tokens_used': c.tokens_used,
                'success': c.success,
                'pattern': c.pattern,
            }
            for c in recent
        ]

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert limiter state to dictionary.

        Returns:
            Dictionary representation of limiter state
        """
        return {
            'max_total': self.max_total,
            'limits': self.limits,
            'counts': dict(self.counts),
            'total_calls': self.total_calls,
            'total_tokens': self.total_tokens,
            'call_history_length': len(self.call_history),
        }

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> 'AICallbackLimiter':
        """
        Create limiter from configuration dictionary.

        Args:
            config: Configuration dictionary with limits

        Returns:
            AICallbackLimiter instance
        """
        return cls(
            max_total=config.get('max_ai_callbacks', 50),
            limits=config.get('limits', {}),
        )


class AILimitError(Exception):
    """Raised when AI callback limit is reached."""

    def __init__(self, prompt_type: str, limit: int):
        self.prompt_type = prompt_type
        self.limit = limit
        super().__init__(
            f"AI limit reached for '{prompt_type}': {limit} calls"
        )
