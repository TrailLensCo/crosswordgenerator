# AI-Powered Crossword Generator - Expanded Development Prompt

## Overview

This document provides a comprehensive prompt for expanding the crossword puzzle generator project. It combines the existing Python implementation with enhanced features including YAML-based configuration, externalized AI prompts, dynamic word generation with safety limits, and comprehensive testing requirements.

**Author:** Mark Buckaway
**Date:** January 2026
**Sample Topic:** Newfoundland culture
**Sample Grid Size:** 11×11

---

## Project Goals

Expand the existing Python crossword generator to:

1. **Replace Markdown intermediate format with YAML** - Structured, machine-readable puzzle representation
2. **Support dual input modes** - Command-line arguments OR YAML configuration file
3. **Externalize all AI prompts to YAML** - Configurable, versionable prompt templates
4. **Add AI callback limits** - Prevent runaway token usage with configurable hard limits
5. **Implement comprehensive testing** - Unit tests and functional tests for all components

## Related Documentation

| Document | Description |
|----------|-------------|
| [PLACEMENT_ALGORITHM.md](PLACEMENT_ALGORITHM.md) | **Detailed word placement algorithm specification** - CSP formulation, AC-3 algorithm, backtracking with MRV/LCV heuristics, exception handling, AI integration points |
| [DESIGN.md](DESIGN.md) | High-level architecture overview |
| [CLAUDE.md](CLAUDE.md) | Development instructions for Claude Code |

**IMPORTANT:** The word placement algorithm is fully specified in `PLACEMENT_ALGORITHM.md`. All implementations of the CSP solver must follow this specification, including:
- Constraint types and enforcement
- AC-3 arc consistency algorithm
- MRV and LCV heuristics
- Empty domain handling with AI fallback
- Exception handling and recovery strategies

---

## Configuration System

### Command-Line Interface

The generator must support all parameters via command-line arguments:

```bash
python3 crossword_generator.py \
    --topic "Newfoundland culture" \
    --size 11 \
    --difficulty wednesday \
    --puzzle-type revealer \
    --author "Mark Buckaway" \
    --output ./output \
    --max-ai-callbacks 50 \
    --prompt-config ./prompts.yaml \
    --api-key "$ANTHROPIC_API_KEY"
```

### YAML Configuration File Input

Alternatively, accept a YAML configuration file:

```bash
python3 crossword_generator.py --config puzzle_config.yaml
```

### Configuration Schema (`puzzle_config.yaml`)

```yaml
# Crossword Puzzle Configuration
# All parameters can be specified here instead of command-line

puzzle:
  topic: "Newfoundland culture"
  size: 11                          # Grid size (5, 7, 9, 11, 13, 15, 21)
  difficulty: wednesday             # monday, tuesday, wednesday, thursday, friday, saturday, sunday
  puzzle_type: revealer             # revealer, themeless, phrase_transformation, hidden_words, rebus, puns, add_a_letter, quote
  author: "Mark Buckaway"

generation:
  max_ai_callbacks: 50              # HARD LIMIT: Maximum AI calls for dynamic word generation
  word_quality_threshold: 0.7       # Minimum quality score for generated words
  enable_pattern_matching: true     # Allow AI to generate words matching patterns
  fallback_to_base_words: true      # Use base word list when AI unavailable
  max_retries_per_pattern: 3        # Retries for each pattern before giving up

output:
  directory: "./output"
  formats:
    - svg_puzzle                    # Empty puzzle grid
    - svg_clues                     # Clue sheet
    - svg_solution                  # Filled solution grid
    - svg_answer_list               # Clues with answers
    - html_complete                 # Combined printable HTML
    - yaml_intermediate             # Structured puzzle data (replaces markdown)

ai:
  model: "claude-sonnet-4-20250514"
  prompt_config: "./prompts.yaml"   # External prompt templates
  api_key_env: "ANTHROPIC_API_KEY"  # Environment variable name

validation:
  enforce_nyt_rules: true           # NYT crossword requirements
  allow_unchecked_squares: false    # Every letter in 2 words
  min_word_length: 3
  max_black_square_ratio: 0.16
  require_connectivity: true
  require_symmetry: true            # 180° rotational symmetry
```

### Priority Order

When both command-line and config file are provided:
1. Command-line arguments take precedence
2. Config file provides defaults
3. Built-in defaults as fallback

### Word Quality Threshold

The `word_quality_threshold` (0.0 to 1.0) determines minimum acceptable word quality based on:

1. **Common Usage Frequency (50% weight)**
   - Words appearing in top 10,000 most common English words score 1.0
   - Words in top 50,000 score 0.7
   - Words in top 100,000 score 0.4
   - Rarer words score 0.2

2. **Crossword-Friendliness (50% weight)**
   - No obscure abbreviations: +0.3
   - Contains common letter patterns (vowel-consonant mix): +0.3
   - Not crosswordese (ERNE, ESNE, ANOA, etc.): +0.2
   - Appears in major crossword dictionaries: +0.2

**Quality Score Calculation:**
```
quality = (frequency_score * 0.5) + (friendliness_score * 0.5)
```

**Threshold Guidelines:**
- `0.7` (default): Standard quality, allows moderately common words
- `0.8`: High quality, prefers well-known words
- `0.5`: Relaxed, allows more obscure fill when needed

### Base Word List Source

When AI limits are reached or AI is unavailable, the system falls back to a base word list:

**Source:** Downloaded/cached public dictionary

**Implementation:**
```yaml
base_word_list:
  source: "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt"
  cache_path: "./data/base_words.txt"
  cache_expiry_days: 30
  fallback_builtin: true  # Use hardcoded minimal list if download fails
```

**Word List Requirements:**
- Minimum 50,000 words
- Organized by length for efficient pattern matching
- Pre-filtered to remove offensive content
- Includes common crossword words and proper nouns

**Fallback Priority:**
1. Cached downloaded word list
2. Re-download from source
3. Built-in minimal word list (5,000 common words)

### SVG Output Requirements

All SVG outputs must be **one page per document** at 8.5" × 11" (612 × 792 pixels at 72 DPI):

| Output File | Description | Content |
|-------------|-------------|---------|
| `{name}_puzzle.svg` | Empty puzzle grid | Grid with numbered cells, black squares, no letters |
| `{name}_clues.svg` | Clue sheet | ACROSS and DOWN clues in two-column layout |
| `{name}_solution.svg` | Solved puzzle | Grid with all letters filled in |
| `{name}_answer_list.svg` | Answer list | Clues with answers (no grid) |

**Note:** The `html_complete` format combines all pages into a single printable HTML document, but each SVG remains a separate single-page file.

---

## YAML Intermediate Format

Replace the markdown intermediate file with structured YAML.

### Intermediate Puzzle Format (`{name}_puzzle.yaml`)

```yaml
# Crossword Puzzle Intermediate Format
# This file contains all puzzle data in structured YAML

metadata:
  title: "Newfoundland Culture"
  author: "Mark Buckaway"
  date: "2026-01-11"
  difficulty: wednesday
  puzzle_type: revealer
  size: 11
  word_count: 42
  theme_entry_count: 4
  generation_stats:
    total_ai_calls: 23
    pattern_match_calls: 12
    clue_generation_calls: 8
    word_list_calls: 3
    generation_time_seconds: 45.2

grid:
  dimensions:
    rows: 11
    columns: 11
  # Grid representation: '.' = white cell, '#' = black cell
  # Letters filled in solution
  pattern: |
    ..#.....#..
    ...........
    ..#.....#..
    ...........
    #.....#...#
    ...........
    #...#.....#
    ...........
    ..#.....#..
    ...........
    ..#.....#..

  solution: |
    CO#DIN#NER
    JIGSDINNERS
    IG#BYE#ERE
    #SCREECH#A
    TOUTONS123
    ...

  cells:
    - row: 0
      col: 0
      type: letter
      letter: "C"
      number: 1
      across_clue: 1
      down_clue: 1
    - row: 0
      col: 2
      type: block
    # ... complete cell definitions

word_slots:
  across:
    - number: 1
      row: 0
      col: 0
      length: 2
      answer: "CO"
      clue: "Newfoundland greeting (informal)"
      is_theme: false
    - number: 4
      row: 0
      col: 3
      length: 3
      answer: "DIN"
      clue: "Loud noise"
      is_theme: false
    # ... all across entries

  down:
    - number: 1
      row: 0
      col: 0
      length: 4
      answer: "CJIG"
      clue: "Type of traditional dance"
      is_theme: false
    # ... all down entries

theme:
  revealer:
    number: 25
    direction: across
    answer: "SCREECH IN"
    clue: "Newfoundland initiation ceremony involving cod and rum"

  entries:
    - number: 10
      direction: across
      answer: "TOUTONS"
      clue: "Fried dough breakfast treat from The Rock"
    - number: 18
      direction: down
      answer: "JIGGS DINNER"
      clue: "Traditional Sunday meal with salt beef"
    - number: 32
      direction: across
      answer: "MUMMERS"
      clue: "Christmas tradition participants in disguise"
    - number: 41
      direction: down
      answer: "SCREECH"
      clue: "Famous Newfoundland rum"

clues:
  across:
    1: "Newfoundland greeting (informal) (2)"
    4: "Loud noise (3)"
    # ... all across clues with letter counts

  down:
    1: "Type of traditional dance (4)"
    2: "Ocean vessel (4)"
    # ... all down clues with letter counts

validation:
  symmetry_check: passed
  connectivity_check: passed
  word_length_check: passed
  checked_squares_check: passed
  word_count_check: passed
  black_square_ratio: 0.14
  all_checks_passed: true
```

---

## AI Prompt Configuration System

All AI prompts must be externalized to a YAML configuration file, enabling versioning, customization, and A/B testing.

### Prompt Configuration File (`prompts.yaml`)

```yaml
# AI Prompt Configuration for Crossword Generator
# All prompts used by the system are defined here
# Variables in {{double_braces}} are substituted at runtime

version: "1.0"
model_defaults:
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
    max_calls: 3  # Maximum times this prompt can be called per puzzle

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
          # ... more words

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
    max_calls: 25  # Strict limit to prevent runaway token usage

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
          # ... more matches

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
    max_calls: 5  # Batch processing reduces calls needed

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
            # ... more entries

    validation:
      has_revealer: true
      min_theme_entries: 3

    # Theme type requirements (substituted into {{theme_type_requirements}})
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
          overall_quality: 8  # 1-10 scale
          solvable: true
          theme_quality: "good"
          issues:
            - type: "clue_issue"
              location: "14 Across"
              problem: "Clue too obscure"
              suggestion: "Consider simpler angle"
          recommendations:
            - "Consider changing 23 Down clue"
```

---

## AI Callback Limiting System

### Hard Limits Configuration

```yaml
# In puzzle_config.yaml or command-line

generation:
  # MASTER LIMIT: Absolute maximum AI calls allowed
  max_ai_callbacks: 50

  # Per-prompt-type limits (must sum to <= max_ai_callbacks)
  limits:
    themed_word_list: 3
    pattern_word_generation: 25
    clue_generation_batch: 5
    theme_development: 2
    validation_check: 1

  # Behavior when limit reached
  on_limit_reached: "fallback"  # Options: fallback, fail, warn

  # Fallback behavior
  fallback_strategy:
    pattern_matching: "use_base_word_list"
    clue_generation: "use_placeholder_clues"
    theme_development: "use_simple_theme"
```

### Implementation Requirements

```python
class AICallbackLimiter:
    """
    Tracks and enforces AI callback limits to prevent runaway token usage.

    CRITICAL: This must be checked BEFORE every AI call.
    """

    def __init__(self, config: dict):
        self.max_total = config.get('max_ai_callbacks', 50)
        self.limits = config.get('limits', {})
        self.counts = defaultdict(int)
        self.total_calls = 0

    def can_call(self, prompt_type: str) -> bool:
        """Check if an AI call is allowed."""
        if self.total_calls >= self.max_total:
            return False
        type_limit = self.limits.get(prompt_type, self.max_total)
        return self.counts[prompt_type] < type_limit

    def record_call(self, prompt_type: str) -> None:
        """Record that an AI call was made."""
        self.counts[prompt_type] += 1
        self.total_calls += 1

    def get_remaining(self, prompt_type: str = None) -> int:
        """Get remaining calls allowed."""
        if prompt_type:
            type_limit = self.limits.get(prompt_type, self.max_total)
            return type_limit - self.counts[prompt_type]
        return self.max_total - self.total_calls
```

---

## Updated Word Selection Prompts

The initial word selection must incorporate all new configuration options.

### Enhanced Word Selection Flow

```
1. Load Configuration
   ├─> Read puzzle_config.yaml OR command-line args
   ├─> Load prompts.yaml
   └─> Initialize AICallbackLimiter

2. Theme Development (if puzzle_type requires it)
   ├─> Check: limiter.can_call('theme_development')
   ├─> Call AI with theme_development prompt
   ├─> Receive: revealer + theme entries
   └─> Record: limiter.record_call('theme_development')

3. Themed Word List Generation
   ├─> Check: limiter.can_call('themed_word_list')
   ├─> Build prompt with ALL options:
   │   - topic: "Newfoundland culture"
   │   - difficulty: wednesday
   │   - puzzle_type: revealer
   │   - size: 11
   │   - topic_aspects: auto-generated or user-provided
   ├─> Call AI with themed_word_list prompt
   ├─> Receive: categorized word list with clues
   └─> Record: limiter.record_call('themed_word_list')

4. CSP Solving with Pattern Matching
   ├─> For each empty domain during solving:
   │   ├─> Check: limiter.can_call('pattern_word_generation')
   │   ├─> If allowed:
   │   │   ├─> Build pattern from grid state
   │   │   ├─> Call AI with pattern_word_generation prompt
   │   │   └─> Record call
   │   └─> If NOT allowed:
   │       └─> Use fallback (base word list or fail)
   └─> Continue until solved or limits exhausted

5. Clue Generation
   ├─> Batch words needing clues
   ├─> Check: limiter.can_call('clue_generation_batch')
   ├─> Call AI in batches to minimize calls
   └─> Use placeholder clues for remaining if limit reached
```

---

## Sample Configuration: Newfoundland Culture 11×11

### Complete Configuration File

```yaml
# newfoundland_puzzle.yaml
# Sample configuration for Newfoundland culture themed puzzle

puzzle:
  topic: "Newfoundland culture"
  size: 11
  difficulty: wednesday
  puzzle_type: revealer
  author: "Mark Buckaway"

  # Topic-specific aspects to emphasize
  topic_aspects:
    - Traditional foods (toutons, jiggs dinner, cod)
    - Music and dance (accordion, ugly stick, jigs)
    - Language and expressions (screech-in, b'y, where ya to)
    - Geography (The Rock, St. John's, Signal Hill)
    - Maritime traditions (fishing, sealing, boat building)
    - Festivals (George Street, Regatta Day, mummering)

generation:
  max_ai_callbacks: 50
  limits:
    themed_word_list: 3
    pattern_word_generation: 25
    clue_generation_batch: 5
    theme_development: 2
    validation_check: 1
  word_quality_threshold: 0.7
  enable_pattern_matching: true
  fallback_to_base_words: true
  max_retries_per_pattern: 3

output:
  directory: "./output/newfoundland"
  formats:
    - svg_puzzle
    - svg_clues
    - svg_solution
    - html_complete
    - yaml_intermediate

ai:
  model: "claude-sonnet-4-20250514"
  prompt_config: "./prompts.yaml"

validation:
  enforce_nyt_rules: true
  min_word_length: 3
  max_black_square_ratio: 0.16
```

### Expected Theme Entries

For an 11×11 Newfoundland culture puzzle, expected theme entries might include:

| Entry | Length | Clue | Theme Connection |
|-------|--------|------|------------------|
| SCREECHIN | 9 | Initiation ceremony for visitors | Revealer |
| TOUTONS | 7 | Fried dough breakfast | Traditional food |
| JIGGSDINNER | 11 | Sunday salt beef meal | Traditional food |
| MUMMERS | 7 | Christmas disguise tradition | Festival |
| GEORGEST | 8 | Famous St. John's pub street | Culture |

---

## Copyright Header Requirements

All new Python source files must include the TrailLensCo copyright header per `.github/CONSTITUTION-COPYRIGHT.md`:

```python
# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.
# Unauthorized copying, distribution, or use of this file,
# via any medium, is strictly prohibited without the express
# written permission of TrailLensCo.

"""Module docstring here."""
```

**Files Requiring Copyright Headers:**
- `src/config.py`
- `src/prompt_loader.py`
- `src/ai_limiter.py`
- `src/yaml_exporter.py`
- `src/yaml_importer.py`
- `src/yaml_schema.py`
- All test files in `tests/`

**Verification:** Pre-commit hooks should validate copyright headers are present.

---

## Detailed Implementation Task List

### Phase 1: Configuration System

#### Task 1.1: Create Configuration Module (`config.py`)

**File:** `src/config.py`

**Requirements:**
- [ ] Define `PuzzleConfig` dataclass with all configuration fields
- [ ] Implement YAML file loading with schema validation
- [ ] Implement command-line argument parsing with argparse
- [ ] Implement configuration merging (CLI overrides YAML)
- [ ] Add validation for all configuration values
- [ ] Support environment variable substitution for API keys

**Expected Implementation:**
```python
@dataclass
class PuzzleConfig:
    topic: str
    size: int
    difficulty: str
    puzzle_type: str
    author: str
    max_ai_callbacks: int
    output_dir: str
    prompt_config_path: str
    # ... all other fields

    @classmethod
    def from_yaml(cls, path: str) -> 'PuzzleConfig': ...

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> 'PuzzleConfig': ...

    @classmethod
    def merge(cls, yaml_config: 'PuzzleConfig', cli_config: 'PuzzleConfig') -> 'PuzzleConfig': ...
```

#### Task 1.2: Create Prompt Configuration Loader (`prompt_loader.py`)

**File:** `src/prompt_loader.py`

**Requirements:**
- [ ] Load and parse `prompts.yaml` file
- [ ] Define `PromptTemplate` dataclass with all fields
- [ ] Implement variable substitution (`{{variable}}` syntax)
- [ ] Validate prompt schema on load
- [ ] Cache loaded prompts for reuse
- [ ] Support prompt versioning

**Expected Implementation:**
```python
@dataclass
class PromptTemplate:
    name: str
    description: str
    max_calls: int
    system: str
    user: str
    output_format: dict
    validation: dict

    def render(self, **variables) -> tuple[str, str]:
        """Return (system_prompt, user_prompt) with variables substituted."""
        ...
```

#### Task 1.3: Implement AI Callback Limiter (`ai_limiter.py`)

**File:** `src/ai_limiter.py`

**Requirements:**
- [ ] Track total AI calls across all types
- [ ] Track per-prompt-type call counts
- [ ] Implement `can_call()` check
- [ ] Implement `record_call()` tracking
- [ ] Implement `get_remaining()` query
- [ ] Support callback for limit-reached events
- [ ] Log all AI calls with timestamps and token counts

**Expected Implementation:**
```python
class AICallbackLimiter:
    def __init__(self, max_total: int, limits: dict[str, int]):
        ...

    def can_call(self, prompt_type: str) -> bool: ...
    def record_call(self, prompt_type: str, tokens_used: int = 0) -> None: ...
    def get_remaining(self, prompt_type: str = None) -> int: ...
    def get_stats(self) -> dict: ...
    def on_limit_reached(self, callback: Callable) -> None: ...
```

---

### Phase 2: YAML Intermediate Format

#### Task 2.1: Define YAML Puzzle Schema (`yaml_schema.py`)

**File:** `src/yaml_schema.py`

**Requirements:**
- [ ] Define complete schema for intermediate YAML format
- [ ] Create dataclasses matching schema structure
- [ ] Implement schema validation
- [ ] Support versioning for forward compatibility

#### Task 2.2: Implement YAML Exporter (`yaml_exporter.py`)

**File:** `src/yaml_exporter.py`

**Requirements:**
- [ ] Export completed puzzle to YAML format
- [ ] Include all metadata (generation stats, validation results)
- [ ] Include complete grid representation
- [ ] Include all clues with formatting
- [ ] Include theme information
- [ ] Ensure human-readable output (proper indentation, comments)

**Expected Implementation:**
```python
class YAMLExporter:
    def export(self, puzzle: CrosswordData, stats: GenerationStats) -> str:
        """Export puzzle to YAML string."""
        ...

    def save(self, puzzle: CrosswordData, stats: GenerationStats, path: str) -> None:
        """Save puzzle to YAML file."""
        ...
```

#### Task 2.3: Implement YAML Importer (`yaml_importer.py`)

**File:** `src/yaml_importer.py`

**Requirements:**
- [ ] Load puzzle from YAML intermediate format
- [ ] Validate loaded data against schema
- [ ] Reconstruct `CrosswordData` object from YAML
- [ ] Support loading partial puzzles (for editing/resuming)

---

### Phase 3: Enhanced AI Integration

#### Task 3.1: Update AIWordGenerator (`ai_word_generator.py`)

**Modify:** `src/ai_word_generator.py`

**Requirements:**
- [ ] Integrate `AICallbackLimiter` - check before every API call
- [ ] Load prompts from external YAML via `PromptLoader`
- [ ] Update `generate_themed_words()` to use new prompt format
- [ ] Update `get_words_matching_pattern()` to use new prompt format
- [ ] Update `generate_clues_batch()` to use new prompt format
- [ ] Add `develop_theme()` method for theme construction
- [ ] Implement fallback behavior when limits reached
- [ ] Track and return token usage statistics

**Method Signatures:**
```python
class AIWordGenerator:
    def __init__(self, config: PuzzleConfig, limiter: AICallbackLimiter,
                 prompt_loader: PromptLoader):
        ...

    def generate_themed_words(self, topic: str, count: int,
                              topic_aspects: list[str] = None) -> list[ThemedWord]:
        """Generate topic-related words. Returns empty list if limit reached."""
        ...

    def get_words_matching_pattern(self, pattern: str, count: int,
                                   used_words: set[str]) -> list[str]:
        """Find words matching pattern. Returns empty list if limit reached."""
        ...

    def generate_clues_batch(self, words: list[str]) -> dict[str, str]:
        """Generate clues for word list. Returns partial dict if limit reached."""
        ...

    def develop_theme(self, topic: str, puzzle_type: str) -> ThemeData:
        """Develop theme with revealer and entries. Returns None if limit reached."""
        ...
```

#### Task 3.2: Update CSP Solver Integration (`csp_solver.py`)

**Modify:** `src/csp_solver.py`

**Reference:** See [PLACEMENT_ALGORITHM.md](PLACEMENT_ALGORITHM.md) for complete algorithm specification.

**Requirements:**
- [ ] Accept `AICallbackLimiter` in constructor
- [ ] Check limits before requesting pattern-matching words
- [ ] Implement graceful degradation when limits reached
- [ ] Track statistics on AI-assisted vs. base-word-list fills
- [ ] Implement exception handling per PLACEMENT_ALGORITHM.md Section 6
- [ ] Follow AC-3 algorithm specification in PLACEMENT_ALGORITHM.md Section 4.2
- [ ] Implement MRV/LCV heuristics per PLACEMENT_ALGORITHM.md Section 5.2-5.3

---

### Phase 4: Command-Line Interface

#### Task 4.1: Update Main Entry Point (`crossword_generator.py`)

**Modify:** `src/crossword_generator.py`

**Requirements:**
- [ ] Add `--config` argument for YAML file input
- [ ] Add all new command-line arguments
- [ ] Implement configuration loading and merging
- [ ] Initialize `AICallbackLimiter` with configured limits
- [ ] Initialize `PromptLoader` with prompt config path
- [ ] Update generation flow to use new components
- [ ] Output generation statistics including AI usage

**New Arguments:**
```
--config PATH           YAML configuration file
--topic TEXT            Puzzle topic/theme
--size INT              Grid size (5,7,9,11,13,15,21)
--difficulty LEVEL      monday/tuesday/wednesday/thursday/friday/saturday/sunday
--puzzle-type TYPE      revealer/themeless/phrase_transformation/hidden_words/rebus/puns/add_a_letter/quote
--author TEXT           Puzzle author name
--output PATH           Output directory
--max-ai-callbacks INT  Maximum AI API calls allowed (default: 50)
--prompt-config PATH    Path to prompts.yaml file
--api-key KEY           Anthropic API key (or use ANTHROPIC_API_KEY env var)
--format FORMAT         Output formats (comma-separated)
--verbose               Enable verbose logging
--dry-run               Validate config without generating
```

---

### Phase 5: Grid Generator Enhancement

#### Task 5.1: Verify 11×11 Grid Support (`grid_generator.py`)

**Modify:** `src/grid_generator.py`

**Requirements:**
- [ ] Verify predefined valid patterns for 11×11 grids exist and work correctly
- [ ] Ensure patterns meet NYT requirements
- [ ] Test connectivity and symmetry
- [ ] Add at least 3 pattern variations

---

## Testing Requirements

### Unit Tests

#### Test File: `tests/test_config.py`

```python
"""Unit tests for configuration module."""

class TestPuzzleConfig:
    def test_load_from_yaml(self):
        """Test loading configuration from YAML file."""
        config = PuzzleConfig.from_yaml('test_config.yaml')
        assert config.topic == "Test Topic"
        assert config.size == 11
        assert config.max_ai_callbacks == 50

    def test_load_from_args(self):
        """Test loading configuration from command-line arguments."""
        args = argparse.Namespace(topic="Test", size=11, ...)
        config = PuzzleConfig.from_args(args)
        assert config.topic == "Test"

    def test_merge_configs(self):
        """Test CLI overrides YAML configuration."""
        yaml_config = PuzzleConfig(topic="YAML Topic", size=11, ...)
        cli_config = PuzzleConfig(topic="CLI Topic", size=None, ...)
        merged = PuzzleConfig.merge(yaml_config, cli_config)
        assert merged.topic == "CLI Topic"  # CLI wins
        assert merged.size == 11  # YAML provides default

    def test_validation_errors(self):
        """Test configuration validation catches errors."""
        with pytest.raises(ConfigValidationError):
            PuzzleConfig(topic="", size=11, ...)  # Empty topic

        with pytest.raises(ConfigValidationError):
            PuzzleConfig(topic="Test", size=8, ...)  # Invalid size

    def test_env_var_substitution(self):
        """Test environment variable substitution for API key."""
        os.environ['TEST_API_KEY'] = 'test-key-123'
        config = PuzzleConfig.from_yaml('config_with_env.yaml')
        assert config.api_key == 'test-key-123'
```

#### Test File: `tests/test_prompt_loader.py`

```python
"""Unit tests for prompt loader module."""

class TestPromptLoader:
    def test_load_prompts(self):
        """Test loading prompts from YAML file."""
        loader = PromptLoader('prompts.yaml')
        assert 'themed_word_list' in loader.prompts
        assert 'pattern_word_generation' in loader.prompts

    def test_variable_substitution(self):
        """Test template variable substitution."""
        loader = PromptLoader('prompts.yaml')
        template = loader.get('themed_word_list')
        system, user = template.render(
            topic="Newfoundland culture",
            difficulty="wednesday",
            size=11
        )
        assert "Newfoundland culture" in user
        assert "wednesday" in system

    def test_missing_variable_error(self):
        """Test error on missing required variable."""
        loader = PromptLoader('prompts.yaml')
        template = loader.get('themed_word_list')
        with pytest.raises(PromptRenderError):
            template.render(topic="Test")  # Missing other required vars

    def test_prompt_validation(self):
        """Test prompt schema validation."""
        with pytest.raises(PromptSchemaError):
            PromptLoader('invalid_prompts.yaml')
```

#### Test File: `tests/test_ai_limiter.py`

```python
"""Unit tests for AI callback limiter."""

class TestAICallbackLimiter:
    def test_initial_state(self):
        """Test limiter starts with full capacity."""
        limiter = AICallbackLimiter(max_total=50, limits={'pattern': 25})
        assert limiter.can_call('pattern') is True
        assert limiter.get_remaining() == 50
        assert limiter.get_remaining('pattern') == 25

    def test_call_tracking(self):
        """Test calls are properly tracked."""
        limiter = AICallbackLimiter(max_total=50, limits={'pattern': 25})
        limiter.record_call('pattern')
        assert limiter.get_remaining() == 49
        assert limiter.get_remaining('pattern') == 24

    def test_type_limit_enforcement(self):
        """Test per-type limits are enforced."""
        limiter = AICallbackLimiter(max_total=50, limits={'pattern': 2})
        limiter.record_call('pattern')
        limiter.record_call('pattern')
        assert limiter.can_call('pattern') is False
        assert limiter.can_call('clue') is True  # Other types still allowed

    def test_total_limit_enforcement(self):
        """Test total limit is enforced."""
        limiter = AICallbackLimiter(max_total=3, limits={})
        limiter.record_call('a')
        limiter.record_call('b')
        limiter.record_call('c')
        assert limiter.can_call('d') is False

    def test_stats_reporting(self):
        """Test statistics are properly reported."""
        limiter = AICallbackLimiter(max_total=50, limits={'pattern': 25})
        limiter.record_call('pattern', tokens_used=100)
        limiter.record_call('pattern', tokens_used=150)
        stats = limiter.get_stats()
        assert stats['total_calls'] == 2
        assert stats['total_tokens'] == 250
        assert stats['calls_by_type']['pattern'] == 2
```

#### Test File: `tests/test_yaml_exporter.py`

```python
"""Unit tests for YAML exporter."""

class TestYAMLExporter:
    def test_export_complete_puzzle(self):
        """Test exporting a complete puzzle to YAML."""
        puzzle = create_test_puzzle()
        stats = create_test_stats()
        exporter = YAMLExporter()
        yaml_str = exporter.export(puzzle, stats)

        # Parse and verify structure
        data = yaml.safe_load(yaml_str)
        assert 'metadata' in data
        assert 'grid' in data
        assert 'word_slots' in data
        assert 'clues' in data

    def test_metadata_completeness(self):
        """Test all metadata fields are exported."""
        puzzle = create_test_puzzle(topic="Test", author="Tester")
        exporter = YAMLExporter()
        data = yaml.safe_load(exporter.export(puzzle, create_test_stats()))

        assert data['metadata']['title'] == "Test"
        assert data['metadata']['author'] == "Tester"
        assert 'generation_stats' in data['metadata']

    def test_grid_representation(self):
        """Test grid is properly represented in YAML."""
        puzzle = create_test_puzzle()
        exporter = YAMLExporter()
        data = yaml.safe_load(exporter.export(puzzle, create_test_stats()))

        assert data['grid']['dimensions']['rows'] == puzzle.grid.size
        assert 'pattern' in data['grid']
        assert 'cells' in data['grid']

    def test_round_trip(self):
        """Test export then import produces equivalent puzzle."""
        original = create_test_puzzle()
        exporter = YAMLExporter()
        importer = YAMLImporter()

        yaml_str = exporter.export(original, create_test_stats())
        loaded = importer.load(yaml_str)

        assert loaded.grid.size == original.grid.size
        assert loaded.clues == original.clues
```

### Functional Tests

#### Test File: `tests/functional/test_end_to_end.py`

```python
"""End-to-end functional tests for crossword generator."""

class TestEndToEnd:
    def test_generate_simple_puzzle_no_ai(self):
        """Test generating a simple puzzle without AI integration."""
        config = PuzzleConfig(
            topic="Animals",
            size=5,
            difficulty="monday",
            max_ai_callbacks=0,  # Disable AI
            ...
        )
        generator = CrosswordGenerator(config)
        result = generator.generate()

        assert result is not None
        assert result.grid.size == 5
        assert len(result.clues['across']) > 0
        assert len(result.clues['down']) > 0

    def test_generate_with_yaml_config(self):
        """Test generating puzzle from YAML configuration file."""
        result = subprocess.run([
            'python3', 'crossword_generator.py',
            '--config', 'tests/fixtures/test_config.yaml'
        ], capture_output=True)

        assert result.returncode == 0
        assert os.path.exists('tests/output/test_puzzle.yaml')

    def test_generate_with_cli_args(self):
        """Test generating puzzle from command-line arguments."""
        result = subprocess.run([
            'python3', 'crossword_generator.py',
            '--topic', 'Test Topic',
            '--size', '5',
            '--difficulty', 'monday',
            '--output', 'tests/output',
            '--max-ai-callbacks', '0'
        ], capture_output=True)

        assert result.returncode == 0

    def test_cli_overrides_yaml(self):
        """Test command-line arguments override YAML config."""
        result = subprocess.run([
            'python3', 'crossword_generator.py',
            '--config', 'tests/fixtures/test_config.yaml',
            '--topic', 'Override Topic',  # Should override YAML
            '--output', 'tests/output'
        ], capture_output=True)

        # Load generated puzzle and verify topic was overridden
        with open('tests/output/override_topic_puzzle.yaml') as f:
            data = yaml.safe_load(f)
        assert data['metadata']['title'] == 'Override Topic'

    @pytest.mark.integration
    def test_generate_with_ai(self):
        """Test generating puzzle with AI integration (requires API key)."""
        if not os.environ.get('ANTHROPIC_API_KEY'):
            pytest.skip("ANTHROPIC_API_KEY not set")

        config = PuzzleConfig(
            topic="Newfoundland culture",
            size=11,
            difficulty="wednesday",
            puzzle_type="revealer",
            max_ai_callbacks=50,
            ...
        )
        generator = CrosswordGenerator(config)
        result = generator.generate()

        assert result is not None
        assert result.grid.size == 10
        assert result.stats['ai_calls'] <= 50
        assert result.theme is not None

    def test_ai_limit_enforcement(self):
        """Test AI callback limits are enforced."""
        config = PuzzleConfig(
            topic="Test",
            size=5,
            max_ai_callbacks=5,
            ...
        )
        generator = CrosswordGenerator(config)
        result = generator.generate()

        assert result.stats['ai_calls'] <= 5

    def test_output_formats(self):
        """Test all output formats are generated correctly."""
        config = PuzzleConfig(
            topic="Test",
            size=5,
            output_formats=['svg_puzzle', 'svg_clues', 'svg_solution',
                          'html_complete', 'yaml_intermediate'],
            ...
        )
        generator = CrosswordGenerator(config)
        outputs = generator.generate()

        assert os.path.exists(outputs['svg_puzzle'])
        assert os.path.exists(outputs['svg_clues'])
        assert os.path.exists(outputs['svg_solution'])
        assert os.path.exists(outputs['html_complete'])
        assert os.path.exists(outputs['yaml_intermediate'])

    def test_yaml_intermediate_validity(self):
        """Test YAML intermediate file is valid and complete."""
        config = PuzzleConfig(topic="Test", size=5, ...)
        generator = CrosswordGenerator(config)
        outputs = generator.generate()

        with open(outputs['yaml_intermediate']) as f:
            data = yaml.safe_load(f)

        # Verify required sections
        assert 'metadata' in data
        assert 'grid' in data
        assert 'word_slots' in data
        assert 'clues' in data
        assert 'validation' in data

        # Verify grid can be reconstructed
        grid_pattern = data['grid']['pattern']
        assert len(grid_pattern.strip().split('\n')) == data['grid']['dimensions']['rows']
```

#### Test File: `tests/functional/test_validation.py`

```python
"""Functional tests for puzzle validation."""

class TestPuzzleValidation:
    def test_nyt_rules_enforced(self):
        """Test NYT crossword rules are enforced."""
        config = PuzzleConfig(
            topic="Test",
            size=11,
            enforce_nyt_rules=True,
            ...
        )
        generator = CrosswordGenerator(config)
        result = generator.generate()

        # All squares must be checked (in 2 words)
        for cell in result.grid.iterate_cells():
            if cell.type == CellType.LETTER:
                assert cell.across_word is not None or cell.down_word is not None

        # 180° symmetry
        assert result.validation['symmetry_check'] == 'passed'

        # Connectivity
        assert result.validation['connectivity_check'] == 'passed'

        # Word length >= 3
        for slot in result.word_slots:
            assert slot.length >= 3

        # Black square ratio
        black_count = sum(1 for c in result.grid.iterate_cells()
                        if c.type == CellType.BLOCK)
        ratio = black_count / (result.grid.size ** 2)
        assert ratio <= 0.16

    def test_puzzle_solvability(self):
        """Test generated puzzle is actually solvable."""
        config = PuzzleConfig(topic="Test", size=5, ...)
        generator = CrosswordGenerator(config)
        result = generator.generate()

        # Attempt to solve using only clues
        solver = PuzzleSolver(result.grid, result.clues)
        solution = solver.solve()

        assert solution is not None
        assert solution == result.solution
```

---

## File Structure After Implementation

```
crossword_generator/
├── src/
│   ├── __init__.py
│   ├── crossword_generator.py  # Main entry point (updated)
│   ├── config.py               # NEW: Configuration handling
│   ├── prompt_loader.py        # NEW: Prompt template loading
│   ├── ai_limiter.py           # NEW: AI callback limiting
│   ├── yaml_exporter.py        # NEW: YAML export
│   ├── yaml_importer.py        # NEW: YAML import
│   ├── yaml_schema.py          # NEW: Schema definitions
│   ├── models.py               # Data structures (unchanged)
│   ├── grid_generator.py       # Grid patterns (verify 11x11)
│   ├── csp_solver.py           # CSP solver (updated)
│   ├── ai_word_generator.py    # AI integration (updated)
│   ├── validator.py            # Validation (unchanged)
│   ├── svg_renderer.py         # SVG output (unchanged)
│   ├── page_renderer.py        # Page rendering (unchanged)
│   └── markdown_exporter.py    # Legacy (deprecated)
├── config/
│   ├── prompts.yaml            # NEW: AI prompt templates
│   ├── default_config.yaml     # NEW: Default configuration
│   └── sample_configs/         # NEW: Example configurations
│       └── newfoundland.yaml
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── test_config.py          # NEW
│   ├── test_prompt_loader.py   # NEW
│   ├── test_ai_limiter.py      # NEW
│   ├── test_yaml_exporter.py   # NEW
│   ├── test_yaml_importer.py   # NEW
│   ├── test_models.py          # Existing
│   ├── test_grid_generator.py  # Existing
│   ├── test_csp_solver.py      # Existing
│   └── functional/
│       ├── __init__.py
│       ├── test_end_to_end.py  # NEW
│       └── test_validation.py  # NEW
├── output/                     # Generated puzzles
├── EXPANDED_PROMPT.md          # This file
├── PROMPT.md                   # Original prompt
├── CLAUDE.md                   # Claude instructions
├── README.md                   # User documentation
└── requirements.txt            # Dependencies
```

---

## Dependencies

### Required (Python 3.8+)

```
# requirements.txt

# AI Integration (optional but recommended)
anthropic>=0.18.0

# YAML Processing
pyyaml>=6.0

# Testing
pytest>=7.0
pytest-cov>=4.0
pytest-mock>=3.0

# Type Checking (development)
mypy>=1.0

# Linting (development)
flake8>=6.0
black>=23.0
isort>=5.0
```

### Installation

```bash
# Production dependencies
pip install anthropic pyyaml

# Development dependencies (including testing)
pip install -r requirements-dev.txt
```

---

## Success Criteria

### Minimum Viable Implementation

- [ ] Configuration loads from YAML file
- [ ] Configuration loads from command-line arguments
- [ ] CLI arguments override YAML values
- [ ] AI prompts load from external YAML file
- [ ] AI callback limits are enforced
- [ ] YAML intermediate format replaces markdown
- [ ] 11×11 grid size supported
- [ ] All unit tests pass
- [ ] End-to-end test generates valid puzzle

### Full Implementation

- [ ] All prompt types externalized to YAML
- [ ] Theme development for all puzzle types
- [ ] Comprehensive validation reporting
- [ ] Token usage statistics tracking
- [ ] Graceful fallback when limits reached
- [ ] All functional tests pass
- [ ] Documentation updated
- [ ] Sample configuration for Newfoundland culture works

---

## Execution Command

To generate the sample Newfoundland culture puzzle:

```bash
# Using YAML configuration
python3 src/crossword_generator.py --config config/sample_configs/newfoundland.yaml

# Using command-line arguments
python3 src/crossword_generator.py \
    --topic "Newfoundland culture" \
    --size 11 \
    --difficulty wednesday \
    --puzzle-type revealer \
    --author "Mark Buckaway" \
    --max-ai-callbacks 50 \
    --prompt-config config/prompts.yaml \
    --output ./output/newfoundland

# Running tests
pytest tests/ -v --cov=src
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-11 | Mark Buckaway | Initial expanded prompt |
| 1.1 | 2026-01-11 | Mark Buckaway | Changed grid size from 10×10 to 11×11 |
| 1.2 | 2026-01-11 | Mark Buckaway | Resolved ambiguities: added theme type requirements, word quality criteria, base word list source (downloaded/cached), copyright header requirements, SVG output clarifications (one page per doc), fixed test assertion |
| 1.3 | 2026-01-11 | Mark Buckaway | Added reference to PLACEMENT_ALGORITHM.md for detailed word placement algorithm specification; updated CSP Solver task requirements |

---

*End of Expanded Development Prompt*
