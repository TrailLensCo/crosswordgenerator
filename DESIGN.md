# AI-Powered Crossword Generator

## Project Overview

A Python-based crossword puzzle generator that:
1. Uses AI (Claude API) to generate themed word lists dynamically
2. Generates puzzles following NYT submission guidelines
3. Outputs to Markdown format
4. Converts Markdown to SVG for rendering

## NYT Crossword Requirements

### Grid Specifications

| Attribute | Daily (Mon-Sat) | Sunday |
|-----------|-----------------|--------|
| Grid Size | 15×15 | 21×21 |
| Max Words | 78 (themed) / 72 (themeless) | 140 |
| Min Word Length | 3 letters | 3 letters |
| Black Squares | ~15-16% max (~36 squares) | Similar ratio |
| Symmetry | 180° rotational | 180° rotational |

### Construction Rules

1. **Rotational Symmetry**: Grid must look the same when rotated 180°
2. **Fully Interlocking**: Every white square must be part of both an Across AND Down word
3. **No Unchecked Letters**: No letter appears in only one word
4. **Connectivity**: All white areas must be connected (no isolated sections)
5. **No Two-Letter Words**: Minimum 3 letters per answer
6. **No Duplicate Answers**: Same word cannot appear twice
7. **Theme Entries**: Longest entries, follow consistent pattern (Mon-Thu, Sun)

### Quality Guidelines

- Avoid "crosswordese" (obscure words like ETUI, ESNE)
- Prefer common, lively words
- Avoid large clumps of black squares
- Minimize 3-letter words
- Theme entries should be interesting and consistent

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      CROSSWORD GENERATOR                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   AI Word    │───▶│    CSP       │───▶│   Markdown   │      │
│  │   Generator  │◀───│   Solver     │    │   Exporter   │      │
│  │   (Claude)   │    │   (AC-3)     │    │              │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
│         ▼                   ▼                   ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  Word List   │    │    Grid      │    │     SVG      │      │
│  │  + Clues     │    │   Layout     │    │   Renderer   │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. AI Word Generator (`word_generator.py`)

Interfaces with Claude API to:
- Generate themed word lists based on a topic
- Provide clues for each word
- **Dynamic refinement**: Request words that match specific patterns
  (e.g., "5-letter word starting with 'A' and ending with 'E' related to astronomy")

```python
class AIWordGenerator:
    def generate_theme_words(topic: str, count: int) -> List[ThemedWord]
    def generate_fill_words(pattern: str, constraints: dict) -> List[str]
    def generate_clue(word: str, difficulty: str) -> str
    def refine_word_list(current_words: List, needed_patterns: List[str]) -> List[str]
```

### 2. Grid Generator (`grid_generator.py`)

Creates valid crossword grid layouts:
- Enforces 180° rotational symmetry
- Manages black square placement
- Ensures connectivity
- Validates word count limits

```python
class GridGenerator:
    def create_grid(size: int, theme_entries: List[str]) -> Grid
    def place_theme_entries(grid: Grid, entries: List[str]) -> Grid
    def add_black_squares(grid: Grid) -> Grid
    def validate_grid(grid: Grid) -> ValidationResult
```

### 3. CSP Solver (`csp_solver.py`)

Fills the grid using Constraint Satisfaction:
- AC-3 algorithm for arc consistency
- Backtracking with MRV and LCV heuristics
- **Dynamic word requests**: When stuck, requests AI for specific patterns

```python
class CrosswordCSP:
    def __init__(grid: Grid, word_list: WordList)
    def enforce_node_consistency()
    def ac3() -> bool
    def backtrack(assignment: dict) -> Optional[dict]
    def request_words_for_pattern(pattern: str) -> List[str]
```

### 4. Markdown Exporter (`markdown_exporter.py`)

Exports puzzle to structured Markdown:

```markdown
# Crossword Puzzle: [Theme]

## Metadata
- **Date**: 2026-01-10
- **Author**: AI Generator
- **Difficulty**: Wednesday
- **Size**: 15×15
- **Word Count**: 76

## Grid

| | 1 | 2 | 3 | 4 | 5 | ... |
|---|---|---|---|---|---|---|
| 1 | A | B | C | ■ | D | ... |
| 2 | E | ■ | F | G | H | ... |
...

## Clues

### Across
1. First clue here (5)
4. Second clue here (7)
...

### Down
1. Down clue here (4)
2. Another down clue (6)
...

## Solution
[Grid with answers filled in]
```

### 5. SVG Renderer (`svg_renderer.py`)

Converts Markdown to SVG:
- Parses Markdown structure
- Generates scalable vector graphics
- Supports both empty grid and solution views
- Configurable styling (colors, fonts, cell size)

```python
class SVGRenderer:
    def render_grid(markdown: str, show_solution: bool = False) -> str
    def render_clues(markdown: str) -> str
    def render_full_puzzle(markdown: str) -> str
```

## Dynamic Word Generation Flow

```
1. User provides TOPIC (e.g., "Space Exploration")
                    │
                    ▼
2. AI generates THEME ENTRIES (long answers)
   - "APOLLOELEVEN" (12 letters)
   - "MOONLANDING" (11 letters)
   - "ASTRONAUT" (9 letters)
                    │
                    ▼
3. Grid Generator places theme entries
   Creates initial grid structure
                    │
                    ▼
4. CSP Solver begins filling
   ┌─────────────────────────────┐
   │  For each empty slot:       │
   │  1. Check word list         │
   │  2. If no matches found:    │◀──┐
   │     → Request AI for word   │   │
   │       matching pattern      │   │
   │  3. Apply AC-3              │   │
   │  4. Backtrack if needed     │───┘
   └─────────────────────────────┘
                    │
                    ▼
5. Complete puzzle exported to Markdown
                    │
                    ▼
6. SVG Renderer creates visual output
```

## File Structure

```
crossword_generator/
├── README.md
├── DESIGN.md
├── requirements.txt
├── config.yaml
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── word_generator.py      # AI interface
│   ├── grid_generator.py      # Grid layout
│   ├── csp_solver.py          # CSP with AC-3
│   ├── markdown_exporter.py   # MD output
│   ├── svg_renderer.py        # SVG conversion
│   └── models.py              # Data classes
├── data/
│   ├── word_lists/            # Base word lists
│   └── templates/             # SVG templates
├── output/
│   ├── puzzles/               # Generated .md files
│   └── svg/                   # Rendered .svg files
└── tests/
    └── ...
```

## Configuration

```yaml
# config.yaml
puzzle:
  size: 15
  max_words: 78
  min_word_length: 3
  max_black_square_ratio: 0.16
  symmetry: rotational_180

ai:
  model: claude-sonnet-4-20250514
  max_retries: 3
  word_quality_threshold: 0.7

output:
  markdown_dir: output/puzzles
  svg_dir: output/svg
  
svg:
  cell_size: 40
  font_family: "Arial"
  grid_color: "#000000"
  block_color: "#000000"
  number_size: 10
  letter_size: 20
```

## Usage Example

```python
from crossword_generator import CrosswordGenerator

# Initialize generator
generator = CrosswordGenerator(
    api_key="your-claude-api-key",
    config="config.yaml"
)

# Generate puzzle
puzzle = generator.generate(
    topic="Classic Movies",
    difficulty="wednesday",
    size=15
)

# Export to Markdown
md_path = puzzle.export_markdown("classic_movies_puzzle.md")

# Render to SVG
svg_path = puzzle.render_svg("classic_movies_puzzle.svg")

# Also generate solution SVG
solution_svg = puzzle.render_svg("classic_movies_solution.svg", show_solution=True)
```

## Next Steps

1. Implement core data models (`models.py`)
2. Build grid generator with symmetry enforcement
3. Implement CSP solver with AC-3
4. Create AI word generator interface
5. Build Markdown exporter
6. Create SVG renderer
7. Integration and testing
