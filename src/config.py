# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.
# Unauthorized copying, distribution, or use of this file,
# via any medium, is strictly prohibited without the express
# written permission of TrailLensCo.

"""
Configuration module for crossword generator.

Handles loading configuration from YAML files and command-line arguments,
with proper merging and validation.
"""

import os
import json
import argparse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any


# Try to import yaml, fallback to None
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None


# Default model for AI operations
DEFAULT_MODEL = "claude-sonnet-4-20250514"

# Valid configuration values
VALID_SIZES = [3, 5, 7, 9, 11, 13, 15, 21]  # 3 is minimum for testing
VALID_DIFFICULTIES = [
    "monday", "tuesday", "wednesday", "thursday",
    "friday", "saturday", "sunday", "easy", "medium", "hard"
]
VALID_PUZZLE_TYPES = [
    "revealer", "themeless", "phrase_transformation",
    "hidden_words", "rebus", "puns", "add_a_letter", "quote"
]
VALID_OUTPUT_FORMATS = [
    "svg_puzzle", "svg_clues", "svg_solution",
    "svg_answer_list", "html_complete", "yaml_intermediate"
]


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


@dataclass
class GenerationConfig:
    """Configuration for puzzle generation."""
    max_ai_callbacks: int = 50
    word_quality_threshold: float = 0.7
    enable_pattern_matching: bool = True
    fallback_to_base_words: bool = True
    max_retries_per_pattern: int = 3
    limits: Dict[str, int] = field(default_factory=lambda: {
        "themed_word_list": 3,
        "pattern_word_generation": 25,
        "clue_generation_batch": 5,
        "theme_development": 2,
        "validation_check": 1
    })
    on_limit_reached: str = "fallback"


@dataclass
class OutputConfig:
    """Configuration for output."""
    directory: str = "./output"
    formats: List[str] = field(default_factory=lambda: [
        "svg_puzzle", "svg_clues", "svg_solution",
        "html_complete", "yaml_intermediate"
    ])


@dataclass
class AIConfig:
    """Configuration for AI integration."""
    model: Optional[str] = None
    prompt_config: str = "./prompts.yaml"
    api_key: Optional[str] = None
    api_key_env: str = "ANTHROPIC_API_KEY"
    model_env: str = "ANTHROPIC_MODEL"


@dataclass
class ValidationConfig:
    """Configuration for puzzle validation."""
    enforce_nyt_rules: bool = True
    allow_unchecked_squares: bool = False
    min_word_length: int = 3
    max_black_square_ratio: float = 0.16
    require_connectivity: bool = True
    require_symmetry: bool = True


@dataclass
class PuzzleConfig:
    """Complete configuration for puzzle generation."""
    # Puzzle settings
    topic: str = "General Knowledge"
    size: int = 11
    difficulty: str = "wednesday"
    puzzle_type: str = "revealer"
    author: str = "AI Generator"
    topic_aspects: List[str] = field(default_factory=list)

    # Sub-configurations
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)

    def __post_init__(self):
        """Convert dicts to dataclass instances if needed."""
        if isinstance(self.generation, dict):
            self.generation = GenerationConfig(**self.generation)
        if isinstance(self.output, dict):
            self.output = OutputConfig(**self.output)
        if isinstance(self.ai, dict):
            self.ai = AIConfig(**self.ai)
        if isinstance(self.validation, dict):
            self.validation = ValidationConfig(**self.validation)

    @classmethod
    def from_yaml(cls, path: str) -> 'PuzzleConfig':
        """
        Load configuration from a YAML file.

        Args:
            path: Path to YAML configuration file

        Returns:
            PuzzleConfig instance

        Raises:
            ConfigValidationError: If file doesn't exist or is invalid
        """
        if not HAS_YAML:
            raise ConfigValidationError(
                "PyYAML is required for YAML configuration. "
                "Install with: pip install pyyaml"
            )

        path = Path(path)
        if not path.exists():
            raise ConfigValidationError(f"Configuration file not found: {path}")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigValidationError(f"Invalid YAML in {path}: {e}")

        if not isinstance(data, dict):
            raise ConfigValidationError(
                f"Configuration file must contain a YAML mapping, got {type(data)}"
            )

        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> 'PuzzleConfig':
        """Create PuzzleConfig from dictionary."""
        # Handle nested 'puzzle' key
        puzzle_data = data.get('puzzle', {})

        config = cls(
            topic=puzzle_data.get('topic', cls.topic),
            size=puzzle_data.get('size', cls.size),
            difficulty=puzzle_data.get('difficulty', cls.difficulty),
            puzzle_type=puzzle_data.get('puzzle_type', cls.puzzle_type),
            author=puzzle_data.get('author', cls.author),
            topic_aspects=puzzle_data.get('topic_aspects', []),
        )

        # Load sub-configurations
        if 'generation' in data:
            gen_data = data['generation']
            config.generation = GenerationConfig(
                max_ai_callbacks=gen_data.get(
                    'max_ai_callbacks', config.generation.max_ai_callbacks
                ),
                word_quality_threshold=gen_data.get(
                    'word_quality_threshold',
                    config.generation.word_quality_threshold
                ),
                enable_pattern_matching=gen_data.get(
                    'enable_pattern_matching',
                    config.generation.enable_pattern_matching
                ),
                fallback_to_base_words=gen_data.get(
                    'fallback_to_base_words',
                    config.generation.fallback_to_base_words
                ),
                max_retries_per_pattern=gen_data.get(
                    'max_retries_per_pattern',
                    config.generation.max_retries_per_pattern
                ),
                limits=gen_data.get('limits', config.generation.limits),
                on_limit_reached=gen_data.get(
                    'on_limit_reached',
                    config.generation.on_limit_reached
                ),
            )

        if 'output' in data:
            out_data = data['output']
            config.output = OutputConfig(
                directory=out_data.get('directory', config.output.directory),
                formats=out_data.get('formats', config.output.formats),
            )

        if 'ai' in data:
            ai_data = data['ai']
            config.ai = AIConfig(
                model=ai_data.get('model'),
                prompt_config=ai_data.get(
                    'prompt_config', config.ai.prompt_config
                ),
                api_key=ai_data.get('api_key'),
                api_key_env=ai_data.get('api_key_env', config.ai.api_key_env),
                model_env=ai_data.get('model_env', config.ai.model_env),
            )

        if 'validation' in data:
            val_data = data['validation']
            config.validation = ValidationConfig(
                enforce_nyt_rules=val_data.get(
                    'enforce_nyt_rules', config.validation.enforce_nyt_rules
                ),
                allow_unchecked_squares=val_data.get(
                    'allow_unchecked_squares',
                    config.validation.allow_unchecked_squares
                ),
                min_word_length=val_data.get(
                    'min_word_length', config.validation.min_word_length
                ),
                max_black_square_ratio=val_data.get(
                    'max_black_square_ratio',
                    config.validation.max_black_square_ratio
                ),
                require_connectivity=val_data.get(
                    'require_connectivity',
                    config.validation.require_connectivity
                ),
                require_symmetry=val_data.get(
                    'require_symmetry', config.validation.require_symmetry
                ),
            )

        return config

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> 'PuzzleConfig':
        """
        Create configuration from command-line arguments.

        Args:
            args: Parsed command-line arguments

        Returns:
            PuzzleConfig instance
        """
        config = cls()

        # Map CLI arguments to config
        if hasattr(args, 'topic') and args.topic:
            config.topic = args.topic
        if hasattr(args, 'size') and args.size:
            config.size = args.size
        if hasattr(args, 'difficulty') and args.difficulty:
            config.difficulty = args.difficulty
        if hasattr(args, 'puzzle_type') and args.puzzle_type:
            config.puzzle_type = args.puzzle_type
        if hasattr(args, 'author') and args.author:
            config.author = args.author
        if hasattr(args, 'output') and args.output:
            config.output.directory = args.output
        if hasattr(args, 'max_ai_callbacks') and args.max_ai_callbacks:
            config.generation.max_ai_callbacks = args.max_ai_callbacks
        if hasattr(args, 'prompt_config') and args.prompt_config:
            config.ai.prompt_config = args.prompt_config
        if hasattr(args, 'api_key') and args.api_key:
            config.ai.api_key = args.api_key
        if hasattr(args, 'model') and args.model:
            config.ai.model = args.model
        if hasattr(args, 'format') and args.format:
            config.output.formats = args.format.split(',')

        return config

    @classmethod
    def merge(
        cls,
        yaml_config: 'PuzzleConfig',
        cli_config: 'PuzzleConfig'
    ) -> 'PuzzleConfig':
        """
        Merge configurations with CLI taking precedence over YAML.

        Args:
            yaml_config: Configuration loaded from YAML file
            cli_config: Configuration from command-line arguments

        Returns:
            Merged PuzzleConfig instance
        """
        # Start with YAML config as base
        merged = PuzzleConfig(
            topic=yaml_config.topic,
            size=yaml_config.size,
            difficulty=yaml_config.difficulty,
            puzzle_type=yaml_config.puzzle_type,
            author=yaml_config.author,
            topic_aspects=yaml_config.topic_aspects,
            generation=yaml_config.generation,
            output=yaml_config.output,
            ai=yaml_config.ai,
            validation=yaml_config.validation,
        )

        # Override with CLI values (non-default values)
        default = cls()

        if cli_config.topic != default.topic:
            merged.topic = cli_config.topic
        if cli_config.size != default.size:
            merged.size = cli_config.size
        if cli_config.difficulty != default.difficulty:
            merged.difficulty = cli_config.difficulty
        if cli_config.puzzle_type != default.puzzle_type:
            merged.puzzle_type = cli_config.puzzle_type
        if cli_config.author != default.author:
            merged.author = cli_config.author
        if cli_config.output.directory != default.output.directory:
            merged.output.directory = cli_config.output.directory
        if (cli_config.generation.max_ai_callbacks !=
                default.generation.max_ai_callbacks):
            merged.generation.max_ai_callbacks = (
                cli_config.generation.max_ai_callbacks
            )
        if cli_config.ai.prompt_config != default.ai.prompt_config:
            merged.ai.prompt_config = cli_config.ai.prompt_config
        if cli_config.ai.api_key:
            merged.ai.api_key = cli_config.ai.api_key
        if cli_config.ai.model:
            merged.ai.model = cli_config.ai.model
        if cli_config.output.formats != default.output.formats:
            merged.output.formats = cli_config.output.formats

        return merged

    def validate(self) -> List[str]:
        """
        Validate configuration values.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Validate topic
        if not self.topic or not self.topic.strip():
            errors.append("Topic cannot be empty")

        # Validate size
        if self.size not in VALID_SIZES:
            errors.append(
                f"Invalid size {self.size}. Must be one of: {VALID_SIZES}"
            )

        # Validate difficulty
        if self.difficulty.lower() not in VALID_DIFFICULTIES:
            errors.append(
                f"Invalid difficulty '{self.difficulty}'. "
                f"Must be one of: {VALID_DIFFICULTIES}"
            )

        # Validate puzzle type
        if self.puzzle_type.lower() not in VALID_PUZZLE_TYPES:
            errors.append(
                f"Invalid puzzle type '{self.puzzle_type}'. "
                f"Must be one of: {VALID_PUZZLE_TYPES}"
            )

        # Validate max_ai_callbacks
        if self.generation.max_ai_callbacks < 0:
            errors.append("max_ai_callbacks must be non-negative")

        # Validate word_quality_threshold
        if not 0.0 <= self.generation.word_quality_threshold <= 1.0:
            errors.append("word_quality_threshold must be between 0.0 and 1.0")

        # Validate output formats
        for fmt in self.output.formats:
            if fmt not in VALID_OUTPUT_FORMATS:
                errors.append(
                    f"Invalid output format '{fmt}'. "
                    f"Must be one of: {VALID_OUTPUT_FORMATS}"
                )

        # Validate black square ratio
        if not 0.0 <= self.validation.max_black_square_ratio <= 1.0:
            errors.append("max_black_square_ratio must be between 0.0 and 1.0")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'puzzle': {
                'topic': self.topic,
                'size': self.size,
                'difficulty': self.difficulty,
                'puzzle_type': self.puzzle_type,
                'author': self.author,
                'topic_aspects': self.topic_aspects,
            },
            'generation': asdict(self.generation),
            'output': asdict(self.output),
            'ai': asdict(self.ai),
            'validation': asdict(self.validation),
        }


def discover_api_key(config: PuzzleConfig) -> Optional[str]:
    """
    Discover API key from multiple sources in priority order.

    Priority order:
    1. CLI argument (already in config if provided)
    2. Config file api_key field
    3. Environment variable (ANTHROPIC_API_KEY or custom)
    4. Claude config directory (~/.claude/credentials.json)
    5. Anthropic config file (~/.anthropic/api_key)
    6. Anthropic config JSON (~/.config/anthropic/config.json)

    Args:
        config: PuzzleConfig instance

    Returns:
        API key string or None if not found
    """
    # Priority 1-2: Already in config
    if config.ai.api_key and config.ai.api_key != "null":
        return config.ai.api_key

    # Priority 3: Environment variable
    env_var = config.ai.api_key_env or "ANTHROPIC_API_KEY"
    if os.environ.get(env_var):
        return os.environ[env_var]

    # Priority 4: Claude config directory
    claude_creds = Path.home() / ".claude" / "credentials.json"
    if claude_creds.exists():
        try:
            creds = json.loads(claude_creds.read_text())
            if creds.get("api_key"):
                return creds["api_key"]
        except (json.JSONDecodeError, KeyError):
            pass

    # Priority 5: Anthropic config file (plain text)
    anthropic_key_file = Path.home() / ".anthropic" / "api_key"
    if anthropic_key_file.exists():
        key = anthropic_key_file.read_text().strip()
        if key:
            return key

    # Priority 6: Anthropic config JSON
    anthropic_config = Path.home() / ".config" / "anthropic" / "config.json"
    if anthropic_config.exists():
        try:
            cfg = json.loads(anthropic_config.read_text())
            if cfg.get("api_key"):
                return cfg["api_key"]
        except (json.JSONDecodeError, KeyError):
            pass

    return None


def get_model(config: PuzzleConfig) -> str:
    """
    Get AI model from config with fallback chain.

    Priority order:
    1. Config ai.model field (from CLI or config file)
    2. Environment variable (ANTHROPIC_MODEL or custom)
    3. Default model

    Args:
        config: PuzzleConfig instance

    Returns:
        Model name string
    """
    # Priority 1: Config field
    if config.ai.model and config.ai.model != "null":
        return config.ai.model

    # Priority 2: Environment variable
    env_var = config.ai.model_env or "ANTHROPIC_MODEL"
    if os.environ.get(env_var):
        return os.environ[env_var]

    # Priority 3: Default
    return DEFAULT_MODEL


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create command-line argument parser.

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description="Generate AI-powered crossword puzzles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using command-line arguments
  python crossword_generator.py --topic "Space" --size 11

  # Using YAML configuration
  python crossword_generator.py --config puzzle_config.yaml

  # CLI arguments override YAML
  python crossword_generator.py --config puzzle.yaml --topic "Override"
"""
    )

    # Configuration file
    parser.add_argument(
        "--config", "-c",
        metavar="PATH",
        help="YAML configuration file"
    )

    # Puzzle settings
    parser.add_argument(
        "--topic", "-t",
        metavar="TEXT",
        help="Puzzle topic/theme"
    )
    parser.add_argument(
        "--size", "-s",
        type=int,
        choices=VALID_SIZES,
        help="Grid size (default: 11)"
    )
    parser.add_argument(
        "--difficulty", "-d",
        choices=VALID_DIFFICULTIES,
        help="Difficulty level"
    )
    parser.add_argument(
        "--puzzle-type",
        choices=VALID_PUZZLE_TYPES,
        help="Type of themed puzzle"
    )
    parser.add_argument(
        "--author", "-a",
        metavar="TEXT",
        help="Author name"
    )

    # Output settings
    parser.add_argument(
        "--output", "-o",
        metavar="PATH",
        help="Output directory"
    )
    parser.add_argument(
        "--format",
        metavar="FORMATS",
        help="Comma-separated output formats"
    )

    # AI settings
    parser.add_argument(
        "--max-ai-callbacks",
        type=int,
        metavar="INT",
        help="Maximum AI API calls allowed (default: 50)"
    )
    parser.add_argument(
        "--prompt-config",
        metavar="PATH",
        help="Path to prompts.yaml file"
    )
    parser.add_argument(
        "--api-key",
        metavar="KEY",
        help="Anthropic API key"
    )
    parser.add_argument(
        "--model",
        metavar="MODEL",
        help="AI model to use"
    )

    # Other options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate config without generating"
    )

    return parser


def load_config(args: Optional[argparse.Namespace] = None) -> PuzzleConfig:
    """
    Load configuration from command-line and/or YAML file.

    Args:
        args: Parsed command-line arguments (if None, parses sys.argv)

    Returns:
        Fully resolved PuzzleConfig

    Raises:
        ConfigValidationError: If configuration is invalid
    """
    if args is None:
        parser = create_argument_parser()
        args = parser.parse_args()

    # Load from YAML if specified
    yaml_config = None
    if hasattr(args, 'config') and args.config:
        yaml_config = PuzzleConfig.from_yaml(args.config)

    # Load from CLI
    cli_config = PuzzleConfig.from_args(args)

    # Merge configurations
    if yaml_config:
        config = PuzzleConfig.merge(yaml_config, cli_config)
    else:
        config = cli_config

    # Validate
    errors = config.validate()
    if errors:
        raise ConfigValidationError(
            "Configuration validation failed:\n" +
            "\n".join(f"  - {e}" for e in errors)
        )

    return config
