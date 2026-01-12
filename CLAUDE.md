# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Standards

**IMPORTANT**: Before making changes to this codebase, review:
- [.github/CONSTITUTION-PYTHON.md](.github/CONSTITUTION-PYTHON.md) - Python coding standards and conventions
- [.github/CONSTITUTION-COPYRIGHT.md](.github/CONSTITUTION-COPYRIGHT.md) - Copyright header requirements for all source files

## Commands

### Running the Generator

```bash
# From repository root
cd src

# Basic usage (no AI features)
python3 crossword_generator.py --topic "Animals" --size 5

# With AI features (requires API key)
export ANTHROPIC_API_KEY='your-key-here'
python3 crossword_generator.py --topic "Space Exploration" --size 7 --difficulty medium

# All options
python3 crossword_generator.py \
    --topic "Classic Movies" \
    --size 15 \
    --difficulty hard \
    --author "Your Name" \
    --output ./output
```

### Installation

```bash
# Optional: Install AI features
pip install anthropic

# The codebase has no other dependencies - it uses only Python standard library
```

### Testing

There are no automated tests in this repository. When making changes, manually test by:
1. Generating a small puzzle (size 5) without AI to verify basic functionality
2. Generating with AI enabled to test AI integration
3. Checking output files in `./output/` directory

## Architecture Overview

This is an AI-powered crossword puzzle generator that creates NYT-style crosswords using constraint satisfaction and optional AI assistance.

### Core Components and Data Flow

```
1. CrosswordGenerator (crossword_generator.py)
   └─> Orchestrates entire generation pipeline

2. Word List Building
   └─> AIWordGenerator.generate_themed_words() → themed words with clues
   └─> _get_base_word_list() → fallback vocabulary

3. Grid Creation
   └─> GridGenerator.generate() → valid NYT-style grid pattern
   └─> Enforces: symmetry, connectivity, block ratio

4. CSP Solving (csp_solver.py)
   └─> CrosswordCSP.solve()
       ├─> AC-3 algorithm for arc consistency
       ├─> Backtracking with MRV/LCV heuristics
       └─> Calls word_generator() when stuck (AI pattern matching)

5. Validation
   └─> validator.validate_puzzle() → ensures solvability

6. Clue Generation
   └─> AIWordGenerator.generate_clues_batch() → AI-generated clues
   └─> Falls back to themed_words or placeholders

7. Rendering
   └─> CrosswordPageRenderer.render_all_pages()
       └─> Outputs: puzzle.svg, clues.svg, solution.svg, complete.html
```

### Key Implementation Details

#### CSP Solver with Dynamic AI Word Requests

The CSP solver ([csp_solver.py:14-100](src/csp_solver.py#L14-L100)) is the core algorithm:
- **Variables**: WordSlots (positions where words go)
- **Domains**: Sets of possible words for each slot
- **Constraints**: Overlapping letters must match, no duplicate words

**Critical feature**: When AC-3 + backtracking gets stuck (empty domain), the solver can request words from AI matching a specific pattern (e.g., "S_A_E" for 5-letter word). See `word_generator` callback in CrosswordCSP.__init__.

#### Grid Generator Pattern System

[grid_generator.py](src/grid_generator.py) uses **predefined valid patterns** rather than generating random grids:
- Patterns are pre-validated for NYT requirements
- Ensures 180° rotational symmetry by construction
- For non-standard sizes, falls back to symmetric random generation
- Call `list_available_patterns()` to see how many patterns exist for a size

#### Two-Phase AI Integration

The AIWordGenerator ([ai_word_generator.py](src/ai_word_generator.py)) is used twice:

1. **Pre-filling phase** (before CSP):
   - `generate_themed_words(topic, count)` → generates theme-relevant vocabulary
   - These words get priority in CSP solver domains

2. **On-demand phase** (during CSP):
   - `create_pattern_word_generator()` → returns function for CSP solver
   - Called when solver encounters empty domain
   - Example: "Need 7-letter word matching 'S__R__T' about Space Exploration"

#### Multi-Page Rendering System

[page_renderer.py](src/page_renderer.py) generates **4 separate files**:
- `{name}_puzzle.svg` - Empty grid with clue numbers
- `{name}_clues.svg` - Formatted clue lists
- `{name}_solution.svg` - Filled grid
- `{name}_complete.html` - All pages combined for printing

All rendering goes through CrosswordData dataclass to decouple data from presentation.

### Data Models ([models.py](src/models.py))

Key classes to understand:

- **Grid**: The crossword grid structure
  - `set_block(row, col)` automatically maintains 180° symmetry
  - `find_word_slots()` identifies all Across/Down positions and assigns clue numbers
  - `is_connected()` uses BFS to verify all white cells are reachable

- **WordSlot**: Represents a single word position
  - `get_pattern(grid)` returns current letters + wildcards (e.g., "A.P.E")
  - `overlaps_with(other)` returns tuple of indices where two slots intersect
  - **Important**: WordSlots are hashable and used as dict keys in CSP solver

- **ThemedWord**: Word + clue + metadata
  - `__post_init__` automatically uppercases and removes spaces
  - Store these in CrosswordGenerator.themed_words dict for clue lookup

### NYT Crossword Requirements

The validator ([validator.py](src/validator.py)) enforces these rules:
- ✅ 180° rotational symmetry (enforced at grid creation)
- ✅ Full connectivity (no isolated white regions)
- ✅ All words ≥ 3 letters
- ✅ Every letter appears in both Across and Down word ("fully checked")
- ✅ Black squares ≤ 16% of total grid
- ✅ Word count ≤ 78 (for themed puzzles)

## Important Patterns

### Adding AI Features

When adding new AI capabilities:
1. Add method to AIWordGenerator class
2. Check `is_available()` before calling AI methods
3. Implement graceful fallback for non-AI mode
4. Update `stats` dict for tracking API usage

Example:
```python
if self.ai.is_available():
    result = self.ai.new_feature()
else:
    result = fallback_implementation()
```

### Grid Modifications

When modifying Grid:
- Always use `set_block()` instead of directly modifying `cells[row][col]`
- This ensures symmetry is maintained automatically
- After any structural change, call `find_word_slots()` to update slot numbering

### CSP Solver Extensions

The solver supports custom heuristics via:
- `select_unassigned_variable()` - Variable ordering (currently uses MRV)
- `order_domain_values()` - Value ordering (currently uses LCV)
- Modify these in [csp_solver.py](src/csp_solver.py) for experimentation

### Output Filename Pattern

All output follows the pattern: `{theme}__{size}x{size}_{type}.{ext}`
- Theme is sanitized (lowercased, spaces→underscores, max 20 chars)
- Types: puzzle, clues, solution, complete
- Change in `CrosswordGenerator._render_output()` if needed

## File Organization

```
src/
├── crossword_generator.py   # Main entry point & orchestration
├── main.py                   # Alternative entry point (legacy)
├── models.py                 # Core data structures
├── grid_generator.py         # Grid pattern creation
├── csp_solver.py            # AC-3 + backtracking solver
├── ai_word_generator.py     # Claude API integration
├── validator.py             # NYT requirements validation
├── svg_renderer.py          # SVG generation (low-level)
├── page_renderer.py         # Multi-page output (high-level)
└── markdown_exporter.py     # Legacy markdown export (unused)
```

## Common Development Scenarios

### Adding a New Grid Size

1. Add size to `choices` in [crossword_generator.py:589](src/crossword_generator.py#L589)
2. Add predefined pattern in [grid_generator.py](src/grid_generator.py)
3. Test that NYT requirements still pass validation

### Modifying Clue Generation

Clue generation happens in `CrosswordGenerator._generate_clues()`:
- Prioritizes themed_words (already have clues from AI)
- Batch-generates remaining clues via AI
- Falls back to placeholder format

### Improving CSP Performance

Key optimization points:
1. `enforce_node_consistency()` - prunes domains based on existing letters
2. `ac3()` - reduces domains before backtracking starts
3. Variable/value ordering heuristics in backtracking
4. Consider caching in `word_generator` callback

### Changing Output Format

To add new output formats:
1. Create new renderer class (see [svg_renderer.py](src/svg_renderer.py) as example)
2. Take CrosswordData as input for consistency
3. Call from `CrosswordGenerator._render_output()`
4. Add to returned dict of output files

## Logging

The codebase uses Python's built-in `logging` module with dual handlers (console + file) for comprehensive diagnostics.

### Log Configuration

Log settings are controlled via [config.py](src/config.py) OutputConfig:

- `log_level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `log_file_prefix`: Prefix for log filename (default: crossword_generator)
- `enable_console_logging`: Enable/disable console output (default: True)
- `analyze_log`: Generate AI analysis report after completion (default: False)

### CLI Arguments

```bash
# Set log level
python crossword_generator.py --topic "Space" --log-level DEBUG

# Disable console logging (file only)
python crossword_generator.py --topic "Space" --no-console-log

# Generate AI analysis report
python crossword_generator.py --topic "Space" --analyze-log

# Verbose mode (sets DEBUG level)
python crossword_generator.py --topic "Space" --verbose
```

### Log File Location

Logs are saved to the output directory with timestamp:

```
./output/crossword_generator_20260111_142345.log
```

### Log Levels

**INFO level** (~100-200 lines per run):

- Generation steps (1-7)
- Word list stats
- Grid selection
- CSP solver progress (every 2 seconds)
- AI API calls
- Validation results
- Output file paths

**DEBUG level** (~1000-2000 lines per run):

- All of INFO, plus:
- Word-by-word additions
- Grid pattern validation details
- AC-3 arc consistency operations
- Every CSP backtrack
- Domain size changes
- AI prompt/response details
- Token usage per call

### Log Analysis Reports

When `--analyze-log` is enabled, an AI-powered analysis report is generated after puzzle completion:

```bash
python crossword_generator.py --config config.yaml --analyze-log
```

The report (`generation_report_YYYYMMDD_HHMMSS.md`) includes:

- **Summary**: 2-3 paragraph narrative of the generation process
- **Performance Metrics**: Runtime, API calls, token usage, backtracks
- **Key Events**: Chronological timeline with timestamps
- **Issues Encountered**: Warnings and errors with severity levels
- **Recommendations**: Actionable improvements for future runs

### Analyzing Logs

Common analysis patterns:

```bash
# Find CSP failures
grep "Could not fill grid" output/crossword_generator_*.log

# Count AI API calls
grep -c "API call:" output/crossword_generator_*.log

# View backtrack history
grep "Backtrack" output/crossword_generator_*.log

# Check word length distribution
grep "letters:" output/crossword_generator_*.log

# Find performance bottlenecks
grep "elapsed" output/crossword_generator_*.log
```

### Implementation Details

- **Logging initialization**: [logging_config.py](src/logging_config.py) configures dual handlers in `setup_logging()`
- **Log rotation**: RotatingFileHandler with 10MB max size, 5 backups
- **Format**: `%(asctime)s - %(levelname)-8s - %(name)s:%(lineno)d - %(funcName)s - %(message)s`
- **Analysis**: [log_analyzer.py](src/log_analyzer.py) parses logs and uses Claude Sonnet 4.5 for report generation
