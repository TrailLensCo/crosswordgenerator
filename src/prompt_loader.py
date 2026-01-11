# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.
# Unauthorized copying, distribution, or use of this file,
# via any medium, is strictly prohibited without the express
# written permission of TrailLensCo.

"""
Prompt loader module for crossword generator.

Loads and manages AI prompt templates from external YAML configuration,
supporting variable substitution and validation.
"""

import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List, Tuple


# Try to import yaml
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None


class PromptSchemaError(Exception):
    """Raised when prompt configuration schema is invalid."""
    pass


class PromptRenderError(Exception):
    """Raised when prompt variable substitution fails."""
    pass


@dataclass
class PromptTemplate:
    """
    A single prompt template with configuration.

    Attributes:
        name: Display name for the prompt
        description: What this prompt does
        max_calls: Maximum number of times this prompt can be called
        system: System prompt template
        user: User prompt template
        model: Optional model override for this prompt
        temperature: Temperature setting for this prompt
        max_tokens: Maximum tokens for response
        output_format: Expected output format specification
        validation: Validation rules for the response
    """
    name: str
    description: str
    max_calls: int
    system: str
    user: str
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    output_format: Dict[str, Any] = field(default_factory=dict)
    validation: Dict[str, Any] = field(default_factory=dict)

    # Pattern for variable substitution
    VARIABLE_PATTERN = re.compile(r'\{\{(\w+)\}\}')

    def render(self, **variables) -> Tuple[str, str]:
        """
        Render the prompt with variable substitution.

        Args:
            **variables: Variables to substitute into the template

        Returns:
            Tuple of (system_prompt, user_prompt)

        Raises:
            PromptRenderError: If required variables are missing
        """
        system_rendered = self._substitute(self.system, variables, 'system')
        user_rendered = self._substitute(self.user, variables, 'user')
        return system_rendered, user_rendered

    def _substitute(
        self,
        template: str,
        variables: Dict[str, Any],
        prompt_type: str
    ) -> str:
        """Substitute variables in template."""
        # Find all variables in template
        required_vars = set(self.VARIABLE_PATTERN.findall(template))

        # Check for missing required variables
        missing = required_vars - set(variables.keys())
        if missing:
            raise PromptRenderError(
                f"Missing required variables for {prompt_type} prompt: {missing}"
            )

        # Perform substitution
        result = template
        for var_name in required_vars:
            value = variables.get(var_name, '')
            if isinstance(value, list):
                value = '\n'.join(f'- {item}' for item in value)
            elif not isinstance(value, str):
                value = str(value)
            result = result.replace(f'{{{{{var_name}}}}}', value)

        return result

    def get_variables(self) -> Tuple[set, set]:
        """
        Get all variables used in this prompt.

        Returns:
            Tuple of (system_vars, user_vars) sets
        """
        system_vars = set(self.VARIABLE_PATTERN.findall(self.system))
        user_vars = set(self.VARIABLE_PATTERN.findall(self.user))
        return system_vars, user_vars


@dataclass
class ModelDefaults:
    """Default settings for prompts."""
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096


class PromptLoader:
    """
    Loads and manages prompt templates from YAML configuration.

    Usage:
        loader = PromptLoader('prompts.yaml')
        template = loader.get('themed_word_list')
        system, user = template.render(topic='Space', difficulty='medium')
    """

    def __init__(self, config_path: str):
        """
        Initialize the prompt loader.

        Args:
            config_path: Path to prompts.yaml configuration file

        Raises:
            PromptSchemaError: If configuration is invalid
        """
        if not HAS_YAML:
            raise PromptSchemaError(
                "PyYAML is required for prompt loading. "
                "Install with: pip install pyyaml"
            )

        self.config_path = Path(config_path)
        self.prompts: Dict[str, PromptTemplate] = {}
        self.defaults = ModelDefaults()
        self.version: str = "1.0"
        self._theme_type_definitions: Dict[str, str] = {}

        self._load()

    def _load(self):
        """Load and validate prompt configuration."""
        if not self.config_path.exists():
            raise PromptSchemaError(
                f"Prompt configuration file not found: {self.config_path}"
            )

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise PromptSchemaError(f"Invalid YAML in prompts config: {e}")

        if not isinstance(data, dict):
            raise PromptSchemaError("Prompts configuration must be a mapping")

        # Load version
        self.version = data.get('version', '1.0')

        # Load defaults
        if 'model_defaults' in data:
            defaults = data['model_defaults']
            self.defaults = ModelDefaults(
                model=defaults.get('model'),
                temperature=defaults.get('temperature', 0.7),
                max_tokens=defaults.get('max_tokens', 4096),
            )

        # Load prompts
        if 'prompts' not in data:
            raise PromptSchemaError("Missing 'prompts' section in configuration")

        for prompt_name, prompt_data in data['prompts'].items():
            self._load_prompt(prompt_name, prompt_data)

    def _load_prompt(self, name: str, data: Dict[str, Any]):
        """Load a single prompt template."""
        required_fields = ['name', 'system', 'user']
        for field_name in required_fields:
            if field_name not in data:
                raise PromptSchemaError(
                    f"Missing required field '{field_name}' in prompt '{name}'"
                )

        # Load theme type definitions if present
        if 'theme_type_definitions' in data:
            self._theme_type_definitions.update(data['theme_type_definitions'])

        self.prompts[name] = PromptTemplate(
            name=data['name'],
            description=data.get('description', ''),
            max_calls=data.get('max_calls', 100),
            system=data['system'],
            user=data['user'],
            model=data.get('model', self.defaults.model),
            temperature=data.get('temperature', self.defaults.temperature),
            max_tokens=data.get('max_tokens', self.defaults.max_tokens),
            output_format=data.get('output_format', {}),
            validation=data.get('validation', {}),
        )

    def get(self, prompt_name: str) -> PromptTemplate:
        """
        Get a prompt template by name.

        Args:
            prompt_name: Name of the prompt (e.g., 'themed_word_list')

        Returns:
            PromptTemplate instance

        Raises:
            KeyError: If prompt not found
        """
        if prompt_name not in self.prompts:
            raise KeyError(
                f"Unknown prompt '{prompt_name}'. "
                f"Available prompts: {list(self.prompts.keys())}"
            )
        return self.prompts[prompt_name]

    def get_theme_type_requirements(self, puzzle_type: str) -> str:
        """
        Get theme type requirements for a puzzle type.

        Args:
            puzzle_type: Type of puzzle (e.g., 'revealer', 'themeless')

        Returns:
            Theme type requirements string
        """
        return self._theme_type_definitions.get(
            puzzle_type,
            f"Create a puzzle with '{puzzle_type}' theme type."
        )

    def list_prompts(self) -> List[str]:
        """
        List all available prompt names.

        Returns:
            List of prompt names
        """
        return list(self.prompts.keys())

    def get_max_calls(self, prompt_name: str) -> int:
        """
        Get maximum allowed calls for a prompt.

        Args:
            prompt_name: Name of the prompt

        Returns:
            Maximum number of calls allowed
        """
        return self.get(prompt_name).max_calls

    def get_model_for_prompt(
        self,
        prompt_name: str,
        main_config_model: Optional[str] = None
    ) -> Optional[str]:
        """
        Get the model to use for a specific prompt.

        Resolution order:
        1. Prompt-specific model
        2. Model defaults
        3. Main config model

        Args:
            prompt_name: Name of the prompt
            main_config_model: Model from main configuration

        Returns:
            Model name or None to use default
        """
        prompt = self.get(prompt_name)

        # Priority 1: Prompt-specific
        if prompt.model:
            return prompt.model

        # Priority 2: Defaults
        if self.defaults.model:
            return self.defaults.model

        # Priority 3: Main config
        return main_config_model


def create_default_prompts_yaml() -> str:
    """
    Create default prompts.yaml content.

    Returns:
        YAML string with default prompts configuration
    """
    return '''# AI Prompt Configuration for Crossword Generator
# All prompts used by the system are defined here
# Variables in {{double_braces}} are substituted at runtime

version: "1.0"

# Default settings applied to all prompts unless overridden
model_defaults:
  model: null                    # Use main config default if null
  temperature: 0.7
  max_tokens: 4096

prompts:
  # ============================================================
  # THEMED WORD LIST GENERATION
  # Called at start to generate topic-specific vocabulary
  # ============================================================
  themed_word_list:
    name: "Generate Themed Word List"
    description: "Creates initial vocabulary list related to the puzzle topic"
    max_calls: 3

    model: null
    temperature: 0.7
    max_tokens: 4096

    system: |
      You are an expert crossword puzzle constructor with deep knowledge of
      {{topic}} and crossword conventions. Generate words that are:
      - Factually accurate and culturally respectful
      - Appropriate for crossword puzzles (no obscure abbreviations)
      - Varied in length to fit different grid positions
      - Interesting and educational for solvers

    user: |
      Generate a themed word list for a {{difficulty}} difficulty crossword
      puzzle about "{{topic}}".

      Requirements:
      - Puzzle type: {{puzzle_type}}
      - Grid size: {{size}}x{{size}}
      - Target word count: {{target_word_count}} words
      - Minimum word length: 3 letters
      - Maximum word length: {{max_word_length}} letters

      For each word, provide:
      1. The word (uppercase, no spaces)
      2. A {{difficulty}}-appropriate clue
      3. Word length
      4. Category (theme_entry, revealer, fill, or proper_noun)
      5. Difficulty score (1-5)

      Focus on these aspects of {{topic}}:
      {{topic_aspects}}

      IMPORTANT: Include 4-6 potential theme entries (longer answers, 7+ letters)
      that could serve as the puzzle's featured answers.

    output_format:
      type: yaml
      schema: |
        words:
          - word: "WORD"
            clue: "Clue text here"
            length: 4
            category: fill
            difficulty: 2

        suggested_theme_entries:
          - word: "LONGERWORD"
            clue: "Theme-related clue"
            theme_connection: "How it connects to theme"

    validation:
      min_words: 30
      max_words: 200
      required_fields: [word, clue, length, category]

  # ============================================================
  # PATTERN MATCHING WORD GENERATION
  # Called during CSP solving when domain is empty
  # ============================================================
  pattern_word_generation:
    name: "Generate Words Matching Pattern"
    description: "Finds words that match a specific letter pattern during grid filling"
    max_calls: 25

    model: "claude-haiku-4-5-20251001"
    temperature: 0.3
    max_tokens: 1024

    system: |
      You are a crossword puzzle word expert. Given a letter pattern,
      generate valid English words that match exactly. Focus on:
      - Common, well-known words preferred
      - Words appropriate for {{difficulty}} difficulty
      - If topic "{{topic}}" is relevant, prefer thematic words

    user: |
      Find words matching this pattern for a crossword puzzle:

      Pattern: {{pattern}}
      (where '.' represents unknown letters)

      Pattern length: {{length}} letters
      Topic context: {{topic}}
      Difficulty: {{difficulty}}

      Already used words (DO NOT repeat): {{used_words}}

      Provide {{count}} words that:
      1. Match the pattern EXACTLY
      2. Are real English words or well-known proper nouns
      3. Are appropriate for a {{difficulty}} crossword
      4. Are NOT in the already-used list

      Return words in order of preference (most common/appropriate first).

    output_format:
      type: yaml
      schema: |
        matching_words:
          - word: "MATCH"
            confidence: 0.95
            is_common: true

    validation:
      min_words: 1
      max_words: 20
      pattern_match_required: true

  # ============================================================
  # CLUE GENERATION
  # Called after grid is filled to generate clues for non-themed words
  # ============================================================
  clue_generation_batch:
    name: "Generate Clues for Words"
    description: "Creates crossword-style clues for a batch of words"
    max_calls: 5

    model: null
    temperature: 0.8
    max_tokens: 4096

    system: |
      You are an expert crossword clue writer for {{difficulty}} difficulty
      puzzles. Write clues that are:
      - Appropriate for the difficulty level
      - Clever but fair
      - Grammatically correct
      - Free of offensive content

      Difficulty guidelines:
      - Monday/Tuesday: Straightforward definitions
      - Wednesday: Some wordplay, specific knowledge
      - Thursday: Tricky, misdirection allowed
      - Friday/Saturday: Cryptic, requires lateral thinking
      - Sunday: Medium difficulty with playful theme

    user: |
      Generate clues for these crossword answers at {{difficulty}} difficulty:

      {{word_list}}

      Puzzle topic: {{topic}}

      For each word, provide:
      1. A primary clue appropriate for {{difficulty}} level
      2. An alternate clue (different angle)

      If a word relates to "{{topic}}", the clue MAY reference the theme
      but should not make it too obvious.

    output_format:
      type: yaml
      schema: |
        clues:
          WORD1:
            primary: "Primary clue text"
            alternate: "Alternate clue text"
          WORD2:
            primary: "Primary clue text"
            alternate: "Alternate clue text"

    validation:
      all_words_clued: true

  # ============================================================
  # THEME DEVELOPMENT
  # Called when puzzle_type requires theme construction
  # ============================================================
  theme_development:
    name: "Develop Puzzle Theme"
    description: "Creates cohesive theme with revealer and themed entries"
    max_calls: 2

    model: "claude-sonnet-4-20250514"
    temperature: 0.9
    max_tokens: 4096

    system: |
      You are a professional crossword constructor specializing in themed
      puzzles. Create themes that are:
      - Fresh and interesting
      - Consistently applied
      - Accessible to general solvers
      - Clever without being obscure

    user: |
      Develop a {{puzzle_type}} theme for a crossword about "{{topic}}".

      Grid size: {{size}}x{{size}}
      Difficulty: {{difficulty}}
      Maximum words: {{max_words}}

      Theme type requirements:
      {{theme_type_requirements}}

      Provide:
      1. Theme concept explanation
      2. Revealer answer and clue (if applicable)
      3. 3-5 theme entries with clues
      4. How the entries connect to the revealer
      5. Suggested placement (long entries typically span the grid)

    output_format:
      type: yaml
      schema: |
        theme:
          concept: "Brief theme explanation"
          revealer:
            answer: "REVEALER"
            clue: "Revealer clue"
            explanation: "How it ties entries together"
          entries:
            - answer: "THEMEENTRY1"
              clue: "Clue for entry"
              theme_connection: "How it connects"

    validation:
      has_revealer: true
      min_theme_entries: 3

    theme_type_definitions:
      revealer: |
        Create a themed puzzle with a REVEALER entry that explains the theme connection.
        - The revealer should be a phrase that ties all theme entries together
        - Theme entries should share a common characteristic revealed by the revealer
        - Example: If theme entries hide animals, revealer might be "HIDDEN CREATURES"
        - Revealer is typically placed as a long across entry

      themeless: |
        Create a themeless puzzle focusing on quality fill and clever cluing.
        - No theme entries or revealer required
        - Emphasize interesting vocabulary and wordplay
        - Lower word count (max 72 for 15x15)
        - Friday/Saturday difficulty expected

      phrase_transformation: |
        Modify common phrases by adding/changing/removing elements related to the topic.
        - Each theme entry transforms a well-known phrase
        - The transformation must be consistent across all entries
        - Include a revealer explaining the transformation
        - Example: Adding "JAVA" to phrases for coffee theme: "JAVA THE HUT"

      hidden_words: |
        Conceal theme-related words within longer answer phrases.
        - Hidden words appear consecutively within the answer
        - All hidden words should be the same category
        - Include a revealer hinting at what's hidden
        - Example: "OVERDRAWN" hides DRAW for an art theme

      rebus: |
        Some squares contain multiple letters or a symbol.
        - All theme entries must incorporate the rebus element
        - The rebus should relate to the topic
        - Clearly indicate which squares are rebus squares
        - Example: Squares containing "HEART" for Valentine's theme

      puns: |
        Theme answers are puns or wordplay on the topic.
        - Each theme entry should be a groan-worthy pun
        - Puns should be accessible and not too obscure
        - Include a revealer that hints at the punny nature
        - Clues should set up the pun without giving it away

      add_a_letter: |
        Add a specific letter to common phrases to create new phrases.
        - The same letter is added to each theme entry
        - Resulting phrases should be humorous or surprising
        - Include a revealer indicating which letter was added
        - Example: Adding "B" creates "BRAIN CHECK" from "rain check"

      quote: |
        A famous quotation or quip spans multiple theme entries.
        - The quote is split across 3-4 long theme entries
        - Entries should be placed symmetrically
        - Attribution can be a separate entry or part of the quote
        - Choose quotes that are well-known and puzzle-appropriate

  # ============================================================
  # PUZZLE VALIDATION ASSIST
  # Called to verify puzzle quality and solvability
  # ============================================================
  validation_check:
    name: "Validate Puzzle Quality"
    description: "Reviews completed puzzle for quality and solvability"
    max_calls: 1

    model: null
    temperature: 0.3
    max_tokens: 2048

    system: |
      You are a crossword puzzle editor reviewing submissions. Evaluate:
      - Clue quality and appropriateness
      - Theme consistency
      - Fill quality (crosswordese, obscure words)
      - Overall solving experience

    user: |
      Review this completed crossword puzzle:

      Topic: {{topic}}
      Difficulty: {{difficulty}}

      Grid:
      {{grid}}

      Clues:
      {{clues}}

      Theme entries:
      {{theme_entries}}

      Evaluate:
      1. Are all clues solvable at {{difficulty}} level?
      2. Is the theme consistent and well-executed?
      3. Are there any problematic fill words?
      4. Would you recommend any clue improvements?

    output_format:
      type: yaml
      schema: |
        validation:
          overall_quality: 8
          solvable: true
          theme_quality: "good"
          issues:
            - type: "clue_issue"
              location: "14 Across"
              problem: "Clue too obscure"
              suggestion: "Consider simpler angle"
          recommendations:
            - "Consider changing 23 Down clue"
'''
