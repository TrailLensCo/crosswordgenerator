# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.
# Unauthorized copying, distribution, or use of this file,
# via any medium, is strictly prohibited without the express
# written permission of TrailLensCo.

"""Unit tests for config module."""

import os
import sys
import tempfile
import unittest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config import (
    PuzzleConfig, GenerationConfig, OutputConfig, AIConfig, ValidationConfig,
    ConfigValidationError, VALID_SIZES, VALID_DIFFICULTIES, VALID_PUZZLE_TYPES
)


class TestPuzzleConfig(unittest.TestCase):
    """Tests for PuzzleConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = PuzzleConfig()

        self.assertEqual(config.topic, "General Knowledge")
        self.assertEqual(config.size, 11)
        self.assertEqual(config.difficulty, "wednesday")
        self.assertEqual(config.puzzle_type, "revealer")
        self.assertEqual(config.author, "AI Generator")
        self.assertEqual(config.topic_aspects, [])

    def test_config_with_values(self):
        """Test configuration with custom values."""
        config = PuzzleConfig(
            topic="Space",
            size=15,
            difficulty="friday",
            puzzle_type="themeless",
            author="Test Author"
        )

        self.assertEqual(config.topic, "Space")
        self.assertEqual(config.size, 15)
        self.assertEqual(config.difficulty, "friday")
        self.assertEqual(config.puzzle_type, "themeless")
        self.assertEqual(config.author, "Test Author")

    def test_nested_config_from_dict(self):
        """Test creating config with nested dict values."""
        config = PuzzleConfig(
            topic="Test",
            generation={'max_ai_callbacks': 100},
            output={'directory': './test_output'}
        )

        self.assertEqual(config.generation.max_ai_callbacks, 100)
        self.assertEqual(config.output.directory, './test_output')

    def test_validation_valid_config(self):
        """Test validation of valid configuration."""
        config = PuzzleConfig(
            topic="Test Topic",
            size=11,
            difficulty="wednesday",
            puzzle_type="revealer"
        )

        errors = config.validate()
        self.assertEqual(errors, [])

    def test_validation_invalid_size(self):
        """Test validation catches invalid size."""
        config = PuzzleConfig(topic="Test", size=8)

        errors = config.validate()
        self.assertTrue(any("size" in e.lower() for e in errors))

    def test_validation_invalid_difficulty(self):
        """Test validation catches invalid difficulty."""
        config = PuzzleConfig(topic="Test", difficulty="impossible")

        errors = config.validate()
        self.assertTrue(any("difficulty" in e.lower() for e in errors))

    def test_validation_empty_topic(self):
        """Test validation catches empty topic."""
        config = PuzzleConfig(topic="")

        errors = config.validate()
        self.assertTrue(any("topic" in e.lower() for e in errors))

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = PuzzleConfig(topic="Test", size=11)

        result = config.to_dict()

        self.assertIn('puzzle', result)
        self.assertEqual(result['puzzle']['topic'], "Test")
        self.assertEqual(result['puzzle']['size'], 11)


class TestGenerationConfig(unittest.TestCase):
    """Tests for GenerationConfig class."""

    def test_default_values(self):
        """Test default generation config values."""
        config = GenerationConfig()

        self.assertEqual(config.max_ai_callbacks, 50)
        self.assertEqual(config.word_quality_threshold, 0.7)
        self.assertTrue(config.enable_pattern_matching)
        self.assertTrue(config.fallback_to_base_words)
        self.assertEqual(config.max_retries_per_pattern, 3)
        self.assertEqual(config.on_limit_reached, "fallback")

    def test_custom_limits(self):
        """Test custom limits configuration."""
        config = GenerationConfig(
            limits={'themed_word_list': 5, 'pattern_word_generation': 30}
        )

        self.assertEqual(config.limits['themed_word_list'], 5)
        self.assertEqual(config.limits['pattern_word_generation'], 30)


class TestOutputConfig(unittest.TestCase):
    """Tests for OutputConfig class."""

    def test_default_values(self):
        """Test default output config values."""
        config = OutputConfig()

        self.assertEqual(config.directory, "./output")
        self.assertIn("svg_puzzle", config.formats)
        self.assertIn("html_complete", config.formats)

    def test_custom_formats(self):
        """Test custom output formats."""
        config = OutputConfig(formats=["svg_puzzle", "yaml_intermediate"])

        self.assertEqual(len(config.formats), 2)
        self.assertIn("yaml_intermediate", config.formats)


class TestAIConfig(unittest.TestCase):
    """Tests for AIConfig class."""

    def test_default_values(self):
        """Test default AI config values."""
        config = AIConfig()

        self.assertIsNone(config.model)
        self.assertEqual(config.prompt_config, "./prompts.yaml")
        self.assertIsNone(config.api_key)
        self.assertEqual(config.api_key_env, "ANTHROPIC_API_KEY")
        self.assertEqual(config.model_env, "ANTHROPIC_MODEL")


class TestValidationConfig(unittest.TestCase):
    """Tests for ValidationConfig class."""

    def test_default_values(self):
        """Test default validation config values."""
        config = ValidationConfig()

        self.assertTrue(config.enforce_nyt_rules)
        self.assertFalse(config.allow_unchecked_squares)
        self.assertEqual(config.min_word_length, 3)
        self.assertEqual(config.max_black_square_ratio, 0.16)
        self.assertTrue(config.require_connectivity)
        self.assertTrue(config.require_symmetry)


class TestYAMLLoading(unittest.TestCase):
    """Tests for YAML configuration loading."""

    def setUp(self):
        """Create a temporary YAML file for testing."""
        self.temp_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False
        )
        self.temp_file.write('''
puzzle:
  topic: "Test Topic"
  size: 11
  difficulty: wednesday
  puzzle_type: revealer
  author: "Test Author"

generation:
  max_ai_callbacks: 30

output:
  directory: "./test_output"
''')
        self.temp_file.close()

    def tearDown(self):
        """Clean up temporary file."""
        os.unlink(self.temp_file.name)

    def test_load_from_yaml(self):
        """Test loading configuration from YAML file."""
        try:
            config = PuzzleConfig.from_yaml(self.temp_file.name)

            self.assertEqual(config.topic, "Test Topic")
            self.assertEqual(config.size, 11)
            self.assertEqual(config.difficulty, "wednesday")
            self.assertEqual(config.author, "Test Author")
            self.assertEqual(config.generation.max_ai_callbacks, 30)
            self.assertEqual(config.output.directory, "./test_output")
        except ConfigValidationError as e:
            if "PyYAML" in str(e):
                self.skipTest("PyYAML not installed")
            raise

    def test_load_nonexistent_file(self):
        """Test error when loading non-existent file."""
        try:
            with self.assertRaises(ConfigValidationError):
                PuzzleConfig.from_yaml("/nonexistent/path.yaml")
        except ConfigValidationError as e:
            if "PyYAML" in str(e):
                self.skipTest("PyYAML not installed")


class TestConfigMerge(unittest.TestCase):
    """Tests for configuration merging."""

    def test_merge_prefers_cli(self):
        """Test that CLI config takes precedence over YAML."""
        yaml_config = PuzzleConfig(topic="YAML Topic", size=11)
        cli_config = PuzzleConfig(topic="CLI Topic", size=11)

        merged = PuzzleConfig.merge(yaml_config, cli_config)

        self.assertEqual(merged.topic, "CLI Topic")

    def test_merge_keeps_yaml_when_cli_default(self):
        """Test that YAML values are kept when CLI uses defaults."""
        yaml_config = PuzzleConfig(
            topic="YAML Topic",
            size=15,
            difficulty="friday"
        )
        cli_config = PuzzleConfig()  # All defaults

        merged = PuzzleConfig.merge(yaml_config, cli_config)

        self.assertEqual(merged.topic, "YAML Topic")
        self.assertEqual(merged.size, 15)
        self.assertEqual(merged.difficulty, "friday")


if __name__ == '__main__':
    unittest.main()
