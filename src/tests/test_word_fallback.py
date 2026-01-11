# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.
# Unauthorized copying, distribution, or use of this file,
# via any medium, is strictly prohibited without the express
# written permission of TrailLensCo.

"""
Tests for word list fallback functionality.

These tests verify that:
1. Words load correctly from words_dictionary.json when available
2. The hardcoded fallback list is used when JSON is not available
3. Word generation works without an API key
"""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import PuzzleConfig


class TestWordsFallback(unittest.TestCase):
    """Test word list loading and fallback functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.src_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
        self.json_path = os.path.join(
            self.src_dir, "data", "words_dictionary.json"
        )

    def test_json_file_exists(self):
        """Verify words_dictionary.json exists in src/data."""
        self.assertTrue(
            os.path.exists(self.json_path),
            f"words_dictionary.json not found at {self.json_path}"
        )

    def test_json_file_valid_format(self):
        """Verify words_dictionary.json is valid JSON with expected format."""
        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Should be a dictionary
        self.assertIsInstance(data, dict)

        # Should have many words (at least 300k)
        self.assertGreater(
            len(data), 300000,
            "words_dictionary.json should have 300k+ words"
        )

        # All keys should be strings
        for key in list(data.keys())[:100]:
            self.assertIsInstance(key, str)

    def test_json_contains_common_words(self):
        """Verify JSON contains common crossword words."""
        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        common_words = [
            "the", "and", "are", "for", "not", "you", "all",
            "can", "had", "her", "was", "one", "our", "out",
            "area", "star", "time", "name", "east", "west",
            "ocean", "river", "trail", "point", "coast",
        ]

        for word in common_words:
            self.assertIn(
                word, data,
                f"Common word '{word}' not found in dictionary"
            )

    def test_load_words_from_json(self):
        """Test _load_words_from_json returns uppercase words."""
        from crossword_generator import CrosswordGenerator

        # Create minimal config
        config = PuzzleConfig(topic="Test", size=5)
        generator = CrosswordGenerator(config)

        words = generator._load_words_from_json()

        # Should return words
        self.assertIsNotNone(words)
        self.assertGreater(len(words), 300000)

        # All words should be uppercase
        for word in words[:1000]:
            self.assertEqual(
                word, word.upper(),
                f"Word '{word}' should be uppercase"
            )

        # All words should be alphabetic
        for word in words[:1000]:
            self.assertTrue(
                word.isalpha(),
                f"Word '{word}' should be alphabetic only"
            )

        # All words should be 3+ letters
        for word in words:
            self.assertGreaterEqual(
                len(word), 3,
                f"Word '{word}' should be at least 3 letters"
            )

    def test_load_words_from_json_returns_sorted_by_length(self):
        """Test that words are sorted by length (longest first)."""
        from crossword_generator import CrosswordGenerator

        config = PuzzleConfig(topic="Test", size=5)
        generator = CrosswordGenerator(config)

        words = generator._load_words_from_json()

        # Verify sorted by length descending
        for i in range(len(words) - 1):
            self.assertGreaterEqual(
                len(words[i]), len(words[i + 1]),
                f"Words should be sorted by length descending"
            )

    def test_hardcoded_fallback_available(self):
        """Test hardcoded fallback list exists and has words."""
        from crossword_generator import CrosswordGenerator

        config = PuzzleConfig(topic="Test", size=5)
        generator = CrosswordGenerator(config)

        words = generator._get_hardcoded_word_list()

        # Should have words
        self.assertIsInstance(words, list)
        self.assertGreater(len(words), 500)

        # Should include 3, 4, and 5 letter words
        word_lengths = set(len(w) for w in words)
        self.assertIn(3, word_lengths)
        self.assertIn(4, word_lengths)
        self.assertIn(5, word_lengths)

    def test_fallback_used_when_json_missing(self):
        """Test hardcoded list is used when JSON file is missing."""
        from crossword_generator import CrosswordGenerator

        config = PuzzleConfig(topic="Test", size=5)
        generator = CrosswordGenerator(config)

        # Mock _load_words_from_json to return None (simulating missing file)
        with patch.object(
            generator, '_load_words_from_json', return_value=None
        ):
            words = generator._get_base_word_list()

        # Should get hardcoded words
        hardcoded = generator._get_hardcoded_word_list()
        self.assertEqual(words, hardcoded)

    def test_json_used_when_available(self):
        """Test JSON words are used when file is available."""
        from crossword_generator import CrosswordGenerator

        config = PuzzleConfig(topic="Test", size=5)
        generator = CrosswordGenerator(config)

        words = generator._get_base_word_list()

        # Should have many more words than hardcoded list
        hardcoded = generator._get_hardcoded_word_list()
        self.assertGreater(
            len(words), len(hardcoded),
            "JSON word list should be larger than hardcoded fallback"
        )


class TestGeneratorWithoutApiKey(unittest.TestCase):
    """Test crossword generation without an API key."""

    def test_generator_works_without_api_key(self):
        """Test that generator initializes and builds word list without API."""
        from crossword_generator import CrosswordGenerator

        # Ensure no API key is set
        with patch.dict(os.environ, {}, clear=True):
            if "ANTHROPIC_API_KEY" in os.environ:
                del os.environ["ANTHROPIC_API_KEY"]

            config = PuzzleConfig(topic="Animals", size=5)
            generator = CrosswordGenerator(config)

            # AI should not be available
            self.assertFalse(generator.ai.is_available())

            # Build word list should work
            generator._build_word_list()

            # Should have words from JSON or fallback
            self.assertGreater(len(generator.word_list), 100)

    def test_word_list_built_without_ai(self):
        """Test word list is built correctly without AI assistance."""
        from crossword_generator import CrosswordGenerator

        with patch.dict(os.environ, {}, clear=True):
            config = PuzzleConfig(topic="Test Topic", size=7)
            generator = CrosswordGenerator(config)

            generator._build_word_list()

            # Word list should be populated
            self.assertIsInstance(generator.word_list, list)
            self.assertGreater(len(generator.word_list), 0)

            # All words should be uppercase
            for word in generator.word_list[:100]:
                self.assertEqual(word, word.upper())

            # All words should fit puzzle constraints
            for word in generator.word_list:
                self.assertGreaterEqual(len(word), 3)
                self.assertLessEqual(len(word), 7)  # size=7


class TestWordFilteringAndDeduplication(unittest.TestCase):
    """Test word filtering and deduplication in word list building."""

    def test_words_filtered_by_size(self):
        """Test words are filtered to puzzle size."""
        from crossword_generator import CrosswordGenerator

        config = PuzzleConfig(topic="Test", size=5)
        generator = CrosswordGenerator(config)

        generator._build_word_list()

        # All words should be <= size
        for word in generator.word_list:
            self.assertLessEqual(
                len(word), 5,
                f"Word '{word}' exceeds puzzle size 5"
            )

    def test_words_minimum_length(self):
        """Test all words are at least 3 letters."""
        from crossword_generator import CrosswordGenerator

        config = PuzzleConfig(topic="Test", size=10)
        generator = CrosswordGenerator(config)

        generator._build_word_list()

        for word in generator.word_list:
            self.assertGreaterEqual(
                len(word), 3,
                f"Word '{word}' is too short (min 3 letters)"
            )

    def test_no_duplicate_words(self):
        """Test word list has no duplicates."""
        from crossword_generator import CrosswordGenerator

        config = PuzzleConfig(topic="Test", size=10)
        generator = CrosswordGenerator(config)

        generator._build_word_list()

        # Check for duplicates
        word_set = set(generator.word_list)
        self.assertEqual(
            len(generator.word_list), len(word_set),
            "Word list should not contain duplicates"
        )

    def test_only_alphabetic_words(self):
        """Test only alphabetic words are included."""
        from crossword_generator import CrosswordGenerator

        config = PuzzleConfig(topic="Test", size=15)
        generator = CrosswordGenerator(config)

        generator._build_word_list()

        for word in generator.word_list:
            self.assertTrue(
                word.isalpha(),
                f"Word '{word}' contains non-alphabetic characters"
            )


if __name__ == "__main__":
    unittest.main()
