# AI-Powered Crossword Generator - Development Prompt

## Overview

This document contains the complete prompt and development process for creating an AI-powered crossword puzzle generator. Use this to recreate or extend the project.

---

## Original Task Prompt

```
Create an AI-powered crossword puzzle generator with the following requirements:

1. **Grid Generation**: Create valid NYT-style crossword grids with:
   - 180° rotational symmetry
   - Full connectivity (no isolated sections)
   - No words shorter than 3 letters
   - Appropriate black square ratio (~16% or less)
   - All squares "checked" (crossed by two words)

2. **CSP Solver**: Implement a Constraint Satisfaction Problem solver using:
   - AC-3 (Arc Consistency 3) algorithm for domain reduction
   - Backtracking search with inference
   - MRV (Minimum Remaining Values) heuristic for variable ordering
   - Integration with AI for dynamic word requests when stuck

3. **AI Integration**: Interface with Claude API to:
   - Generate themed word lists with clues
   - Request words matching specific letter patterns (e.g., "A..LE" → "APPLE")
   - Generate clues for solved words
   - Support batch operations to minimize API calls

4. **Validation**: Validate puzzles for:
   - Structural validity (NYT requirements)
   - Fillability (CSP can find at least one valid solution)

5. **Output**: Generate multi-page output:
   - Page 1: Empty puzzle grid (SVG)
   - Page 2: Clues list (SVG)
   - Page 3: Solution grid (SVG)
   - Combined HTML with print functionality
   - Markdown source file
```

---

## Development Steps

### Step 1: Data Models (`models.py`)

Created core data structures:

```python
# Key classes:
- CellType (Enum): EMPTY, BLOCK, LETTER
- Cell: Individual grid cell with letter, number, type
- Direction (Enum): ACROSS, DOWN
- WordSlot: Represents a word position (start, direction, length, cells)
- Grid: Complete crossword grid with methods for:
  - set_block() - places black squares with automatic symmetry
  - find_word_slots() - identifies all word positions
  - is_connected() - BFS connectivity check
  - assign_numbers() - assigns clue numbers
```

**Testing performed:**
```bash
python3 models.py
# Verified: Grid creation, block placement with symmetry, slot finding, connectivity check
```

### Step 2: CSP Solver (`csp_solver.py`)

Implemented constraint satisfaction solver:

```python
# Key components:
- CrosswordCSP class with:
  - variables: WordSlots
  - domains: Set of possible words per slot
  - constraints: Overlapping letters must match, all words unique
  
- AC-3 Algorithm:
  - Enforces arc consistency
  - Reduces domains by eliminating impossible words
  - Requests words from AI when domain becomes empty
  
- Backtracking Search:
  - MRV heuristic (select slot with fewest options)
  - Inference via AC-3 after each assignment
  - Maintains domain copies for backtracking
```

**Testing performed:**
```bash
python3 csp_solver.py
# Test 1: 3x3 grid - PASSED (found solution: SOD/PAY/ARE)
# Test 2: 5x5 grid - PASSED with sufficient word list
# Verified: AC-3 reduces domains correctly, backtracking works
```

**Key debugging session:**
- Initial 5x5 test failed - AC-3 reduced domains to 2 words for corner slot
- Root cause: Word list lacked diversity for 5-letter words
- Solution: Expanded base word list + AI word generation

### Step 3: Grid Generator (`grid_generator.py`)

Created valid grid patterns:

```python
# Predefined patterns for sizes: 5, 7, 9, 11, 13, 15, 21
# Each pattern stored as list of (row, col) for black squares
# Only stores upper-left quadrant; symmetry applied automatically

# Pattern requirements validated:
- 180° rotational symmetry
- Connectivity
- No short words
- All squares checked (crossed by 2 words)
```

**Testing performed:**
```bash
python3 grid_generator.py
# Tested 5x5, 7x7, 15x15 patterns
# Initial 15x15 pattern had 2 unchecked squares - fixed pattern
```

### Step 4: Validator (`validator.py`)

Implemented two-phase validation:

```python
# Phase 1: Structure Validation
- Check symmetry
- Check connectivity
- Check black square ratio
- Check word lengths (>= 3)
- Check all squares are checked (crossed by 2 words)
- Count word slots

# Phase 2: Fillability Check
- Run CSP solver
- Verify at least one solution exists
- Report solve time and statistics
```

**Testing performed:**
```bash
python3 validator.py
# Test 1: Valid 3x3 - Structure ✅, Fillable ✅
# Test 2: Asymmetric grid - Structure ❌ (caught asymmetry)
# Test 3: Disconnected grid - Structure ❌ (caught isolation)
# Test 4: Valid 7x7 - Structure ✅, Fillable depends on word list
```

**Key insight:** Validator checks structure first (fast) before attempting fill (slow).

### Step 5: Page Renderer (`page_renderer.py`)

Created multi-page SVG output:

```python
# CrosswordPageRenderer generates:
1. puzzle.svg - Empty grid with numbers
2. clues.svg - Formatted clue lists
3. solution.svg - Filled grid
4. complete.html - All pages with print button
5. puzzle.md - Markdown source

# SVG features:
- Configurable dimensions
- Proper grid numbering
- Black square rendering
- Print-friendly layout
```

**Testing performed:**
```bash
python3 page_renderer.py
# Generated test files, opened in browser
# Verified: Grid renders correctly, clues formatted, print works
```

### Step 6: AI Word Generator (`ai_word_generator.py`)

Integrated Claude API:

```python
# AIWordGenerator class provides:
1. generate_themed_words(theme, count) → List[WordWithClue]
   - Calls Claude to generate themed vocabulary
   - Returns words with crossword-style clues
   
2. get_words_matching_pattern(pattern, count) → List[str]
   - Pattern like "A..LE" matches "APPLE", "ADDLE"
   - Used by CSP when domain is empty
   
3. generate_clue(word) → str
   - Generates single clue for a word
   
4. generate_clues_batch(words) → Dict[str, str]
   - Efficient batch clue generation

# Caching:
- Caches patterns, words, and clues
- Reduces API calls on repeated requests
```

**Testing performed:**
```bash
python3 ai_word_generator.py
# Without API key: Falls back to hardcoded words
# With API key: Successfully generated themed words and clues
```

### Step 7: Main Generator (`crossword_generator.py`)

Integrated all components:

```python
# CrosswordGenerator orchestrates:
1. Build word list (AI themed + base words)
2. Create grid pattern
3. Validate structure
4. Fill grid with CSP (AI assists when stuck)
5. Validate solution
6. Generate clues (AI)
7. Render output

# Command-line interface:
--topic "Theme"     # Puzzle theme
--size N            # Grid size (3,5,7,9,11,13,15)
--difficulty LEVEL  # easy/medium/hard
--output DIR        # Output directory
--api-key KEY       # Anthropic API key
```

**Testing performed:**
```bash
# Test without API key (fallback mode)
python3 crossword_generator.py --topic "Space" --size 3 --output /tmp/test
# Result: Successfully generated 3x3 puzzle with placeholder clues

# Test with API key
export ANTHROPIC_API_KEY='sk-...'
python3 crossword_generator.py --topic "Space Exploration" --size 5
# Result: Generated themed puzzle with AI-generated clues
```

---

## Testing Summary

### Unit Tests Performed

| Component | Test | Result |
|-----------|------|--------|
| Grid | Block placement with symmetry | ✅ Pass |
| Grid | Connectivity check (BFS) | ✅ Pass |
| Grid | Word slot finding | ✅ Pass |
| CSP | AC-3 domain reduction | ✅ Pass |
| CSP | Backtracking search | ✅ Pass |
| CSP | MRV heuristic | ✅ Pass |
| Validator | Symmetry detection | ✅ Pass |
| Validator | Connectivity detection | ✅ Pass |
| Validator | Unchecked square detection | ✅ Pass |
| Validator | Fillability check | ✅ Pass |
| Renderer | SVG generation | ✅ Pass |
| Renderer | HTML combination | ✅ Pass |
| AI | Themed word generation | ✅ Pass (with API) |
| AI | Pattern matching | ✅ Pass (with API) |
| AI | Clue generation | ✅ Pass (with API) |
| AI | Fallback mode | ✅ Pass (without API) |

### Integration Tests

| Test | Command | Result |
|------|---------|--------|
| 3x3 no API | `python3 crossword_generator.py --topic "Test" --size 3` | ✅ Generated puzzle |
| 5x5 no API | `python3 crossword_generator.py --topic "Test" --size 5` | ✅ Generated puzzle |
| 3x3 with API | `python3 crossword_generator.py --topic "Space" --size 3` | ✅ Themed puzzle |

### Debugging Sessions

1. **Empty domain issue (5x5 grid)**
   - Symptom: CSP returned no solution immediately
   - Debug: Added logging to show domain sizes after AC-3
   - Finding: Only 2 words fit corner slot after constraint propagation
   - Fix: Expanded word list from ~100 to ~1000+ words

2. **Unchecked squares in patterns**
   - Symptom: 15x15 pattern failed structure validation
   - Debug: Validator reported 2 unchecked squares
   - Finding: Pattern had cells only crossed by one word
   - Fix: Adjusted pattern coordinates

3. **AC-3 + AI integration**
   - Symptom: AI words weren't being used
   - Debug: Added stats tracking for AI calls
   - Finding: AI was called but words were duplicates of used words
   - Fix: Filter AI words against `used_words` set

---

## File Structure

```
crossword_generator/
├── src/
│   ├── models.py              # Data structures (Grid, Cell, WordSlot)
│   ├── csp_solver.py          # CSP solver with AC-3
│   ├── grid_generator.py      # Valid grid pattern generation
│   ├── validator.py           # Structure and fillability validation
│   ├── page_renderer.py       # Multi-page SVG/HTML output
│   ├── ai_word_generator.py   # Claude API integration
│   └── crossword_generator.py # Main entry point
├── output/                    # Generated puzzles (gitignored)
├── PROMPT.md                  # This file
└── README.md                  # User documentation
```

---

## Usage Examples

### Basic Usage (No API Key)

```bash
cd crossword_generator/src
python3 crossword_generator.py --topic "Animals" --size 5
```

### With AI Integration

```bash
export ANTHROPIC_API_KEY='your-key-here'
python3 crossword_generator.py \
    --topic "Classic Movies" \
    --size 7 \
    --difficulty hard \
    --author "Your Name" \
    --output ./my_puzzles
```

### Programmatic Usage

```python
from crossword_generator import CrosswordGenerator, GeneratorConfig

config = GeneratorConfig(
    size=5,
    theme="Space Exploration",
    difficulty="medium",
    author="AI Generator",
    api_key="your-key-here",  # Optional
    output_dir="./output"
)

generator = CrosswordGenerator(config)
output_files = generator.generate()

if output_files:
    print(f"Puzzle: {output_files['puzzle']}")
    print(f"Solution: {output_files['solution']}")
```

---

## Future Enhancements

Potential improvements not implemented:

1. **Difficulty scoring** - Analyze clue/word difficulty
2. **Theme density** - Ensure themed words appear prominently
3. **Interactive solver** - Web UI for solving puzzles
4. **PDF export** - Direct PDF generation
5. **Puzzle database** - Store and retrieve generated puzzles
6. **Word list management** - Import/export custom word lists
7. **Clue editing** - Post-generation clue refinement

---

## Dependencies

```
Python 3.8+
anthropic (optional, for AI features)
```

Install:
```bash
pip install anthropic --break-system-packages
```

---

## Recreating This Project

To recreate from scratch, follow these steps in order:

1. Create `models.py` - Run tests to verify grid operations
2. Create `csp_solver.py` - Test with 3x3 grid first
3. Create `grid_generator.py` - Test pattern validity
4. Create `validator.py` - Test with valid and invalid grids
5. Create `page_renderer.py` - Test SVG output
6. Create `ai_word_generator.py` - Test with and without API key
7. Create `crossword_generator.py` - Integration testing

Each step should be tested before proceeding to the next.

---

## Contact / Attribution

Generated by Claude (Anthropic) as a demonstration of:
- Constraint Satisfaction Problems (CSP)
- Arc Consistency (AC-3) algorithms
- AI-assisted content generation
- Multi-format document generation
