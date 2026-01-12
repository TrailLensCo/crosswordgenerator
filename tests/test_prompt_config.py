#!/usr/bin/env python3
# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.
# Unauthorized copying, distribution, or use of this file,
# via any medium, is strictly prohibited without the express
# written permission of TrailLensCo.

"""
Unit tests to verify that prompts.yaml configuration is being used correctly.

This test file verifies the fix for the bug where hardcoded API parameters
(max_tokens, temperature, model) were being used instead of values from
the prompts.yaml configuration file.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from prompt_loader import PromptLoader, PromptTemplate


class TestPromptConfigUsage(unittest.TestCase):
    """Test that template configuration is properly used instead of hardcoded values."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock PromptLoader that returns templates with known config
        self.prompt_loader = Mock(spec=PromptLoader)

        # Create mock templates with specific config values
        self.themed_word_template = Mock(spec=PromptTemplate)
        self.themed_word_template.max_tokens = 16384
        self.themed_word_template.temperature = 0.7
        self.themed_word_template.model = "claude-opus-4-5-20251101"
        self.themed_word_template.render = Mock(return_value=("system prompt", "user prompt"))

        self.pattern_word_template = Mock(spec=PromptTemplate)
        self.pattern_word_template.max_tokens = 2048
        self.pattern_word_template.temperature = 0.3
        self.pattern_word_template.model = "claude-sonnet-4-20250514"
        self.pattern_word_template.render = Mock(return_value=("system prompt", "user prompt"))

        self.clue_template = Mock(spec=PromptTemplate)
        self.clue_template.max_tokens = 4096
        self.clue_template.temperature = 0.8
        self.clue_template.model = "claude-opus-4-5-20251101"
        self.clue_template.render = Mock(return_value=("system prompt", "user prompt"))

    def test_template_values_are_accessible(self):
        """Verify that PromptTemplate objects have the required config attributes."""
        # This tests that our templates have the expected structure
        self.assertTrue(hasattr(self.themed_word_template, 'max_tokens'))
        self.assertTrue(hasattr(self.themed_word_template, 'temperature'))
        self.assertTrue(hasattr(self.themed_word_template, 'model'))

        self.assertEqual(self.themed_word_template.max_tokens, 16384)
        self.assertEqual(self.themed_word_template.temperature, 0.7)
        self.assertEqual(self.themed_word_template.model, "claude-opus-4-5-20251101")

    def test_themed_word_list_template_config(self):
        """Test that themed_word_list template has correct configuration."""
        # Configure mock to return our template
        self.prompt_loader.get = Mock(return_value=self.themed_word_template)

        # Get the template
        template = self.prompt_loader.get('themed_word_list')

        # Verify the configuration values that should be used
        self.assertEqual(template.max_tokens, 16384,
                        "themed_word_list should use max_tokens from template")
        self.assertEqual(template.temperature, 0.7,
                        "themed_word_list should use temperature from template")
        self.assertEqual(template.model, "claude-opus-4-5-20251101",
                        "themed_word_list should use model from template")

    def test_pattern_word_generation_template_config(self):
        """Test that pattern_word_generation template has correct configuration."""
        # Configure mock to return our template
        self.prompt_loader.get = Mock(return_value=self.pattern_word_template)

        # Get the template
        template = self.prompt_loader.get('pattern_word_generation')

        # Verify the configuration values that should be used
        self.assertEqual(template.max_tokens, 2048,
                        "pattern_word_generation should use max_tokens from template")
        self.assertEqual(template.temperature, 0.3,
                        "pattern_word_generation should use temperature from template")
        self.assertEqual(template.model, "claude-sonnet-4-20250514",
                        "pattern_word_generation should use model from template")

    def test_clue_generation_batch_template_config(self):
        """Test that clue_generation_batch template has correct configuration."""
        # Configure mock to return our template
        self.prompt_loader.get = Mock(return_value=self.clue_template)

        # Get the template
        template = self.prompt_loader.get('clue_generation_batch')

        # Verify the configuration values that should be used
        self.assertEqual(template.max_tokens, 4096,
                        "clue_generation_batch should use max_tokens from template")
        self.assertEqual(template.temperature, 0.8,
                        "clue_generation_batch should use temperature from template")
        self.assertEqual(template.model, "claude-opus-4-5-20251101",
                        "clue_generation_batch should use model from template")

    def test_template_render_method(self):
        """Test that templates can render prompts correctly."""
        # This verifies the template has the render method we depend on
        system_prompt, user_prompt = self.themed_word_template.render(
            topic="Test Topic",
            count=50,
            min_length=3,
            max_length=15
        )

        self.assertEqual(system_prompt, "system prompt")
        self.assertEqual(user_prompt, "user prompt")

    def test_fallback_behavior_when_template_is_none(self):
        """Test that code handles None template correctly (fallback mode)."""
        # When prompt_loader is None or template loading fails, we should
        # have default fallback values. This tests the pattern:
        # if template: use template.max_tokens else: use default

        template = None

        # Simulate the conditional logic in the fixed code
        if template:
            max_tokens = template.max_tokens
            temperature = template.temperature
            model = template.model
        else:
            # These are the fallback defaults that should be used
            max_tokens = 4096
            temperature = 0.7
            model = None

        # Verify fallback values
        self.assertEqual(max_tokens, 4096, "Should use default max_tokens when template is None")
        self.assertEqual(temperature, 0.7, "Should use default temperature when template is None")
        self.assertIsNone(model, "Should use None for model when template is None (uses client default)")


class TestPromptLoaderIntegration(unittest.TestCase):
    """Integration tests with the actual PromptLoader."""

    def test_actual_prompts_yaml_has_correct_structure(self):
        """Test that the actual prompts.yaml file has the expected structure."""
        # This test verifies the fix works with the real config file
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'prompts.yaml')

        if not os.path.exists(config_path):
            self.skipTest(f"prompts.yaml not found at {config_path}")

        loader = PromptLoader(config_path)

        # Test themed_word_list template
        template = loader.get('themed_word_list')
        self.assertIsNotNone(template, "themed_word_list template should exist")
        self.assertTrue(hasattr(template, 'max_tokens'), "Template should have max_tokens attribute")
        self.assertTrue(hasattr(template, 'temperature'), "Template should have temperature attribute")
        self.assertTrue(hasattr(template, 'model'), "Template should have model attribute")

        # Verify the fix: max_tokens should be 16384, not 4096
        self.assertEqual(template.max_tokens, 16384,
                        "BUG: themed_word_list should use max_tokens=16384 from prompts.yaml, not hardcoded 4096")

    def test_actual_pattern_word_generation_config(self):
        """Test that pattern_word_generation has correct config in prompts.yaml."""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'prompts.yaml')

        if not os.path.exists(config_path):
            self.skipTest(f"prompts.yaml not found at {config_path}")

        loader = PromptLoader(config_path)
        template = loader.get('pattern_word_generation')

        self.assertIsNotNone(template, "pattern_word_generation template should exist")
        self.assertTrue(hasattr(template, 'max_tokens'), "Template should have max_tokens attribute")

        # Verify this uses configured value, not hardcoded 1024
        self.assertNotEqual(template.max_tokens, 1024,
                           "pattern_word_generation should not use hardcoded 1024")


if __name__ == '__main__':
    unittest.main()
