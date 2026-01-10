# AI-Powered Crossword Generator

Generate NYT-style crossword puzzles with AI-assisted theming and clue generation.

## Features

- **NYT-Style Grids**: Symmetric, fully connected, properly checked squares
- **AI Theme Integration**: Generate themed word lists using Claude API
- **Smart Filling**: CSP solver with AC-3 algorithm + AI word requests
- **Validation**: Ensures every puzzle is completeable before output
- **Multi-Page Output**: SVG puzzle, clues, solution + combined HTML

## Quick Start

```bash
cd src

# Generate a simple puzzle (no API key required)
python3 crossword_generator.py --topic "Animals" --size 5

# With AI features (better themes and clues)
export ANTHROPIC_API_KEY='your-key'
python3 crossword_generator.py --topic "Space Exploration" --size 7
```

## Installation

```bash
# Clone or copy the project
git clone <repo-url>
cd crossword_generator

# Install AI features (optional)
pip install anthropic
```

## Usage

### Command Line

```bash
python3 src/crossword_generator.py [options]

Options:
  --topic, -t    Theme for the puzzle (default: "General Knowledge")
  --size, -s     Grid size: 3,5,7,9,11,13,15 (default: 5)
  --difficulty   easy, medium, hard (default: medium)
  --author, -a   Author name (default: "AI Generator")
  --output, -o   Output directory (default: ./output)
  --api-key      Anthropic API key (or set ANTHROPIC_API_KEY env var)
```

### Examples

```bash
# Mini 5x5 puzzle
python3 src/crossword_generator.py --topic "Food" --size 5

# Standard 15x15 puzzle
python3 src/crossword_generator.py --topic "Classic Movies" --size 15

# Hard difficulty with custom author
python3 src/crossword_generator.py \
    --topic "Science" \
    --size 7 \
    --difficulty hard \
    --author "Jane Doe"
```

### Python API

```python
from crossword_generator import CrosswordGenerator, GeneratorConfig

config = GeneratorConfig(
    size=5,
    theme="Animals",
    difficulty="medium",
    api_key="sk-..."  # Optional
)

generator = CrosswordGenerator(config)
files = generator.generate()
# Returns: {'puzzle': 'path.svg', 'solution': 'path.svg', ...}
```

## Output Files

Each puzzle generates:

| File | Description |
|------|-------------|
| `{name}_puzzle.svg` | Empty grid with numbers |
| `{name}_clues.svg` | Formatted clue lists |
| `{name}_solution.svg` | Filled solution grid |
| `{name}_complete.html` | All pages combined, printable |
| `{name}.md` | Markdown source |

## How It Works

### 1. Word List Generation
- Loads base crossword vocabulary (~1000 words)
- If API key provided, generates themed words with clues

### 2. Grid Creation
- Selects from predefined valid patterns
- Ensures NYT requirements (symmetry, connectivity)

### 3. Grid Filling (CSP Solver)
- **Variables**: Word slots in the grid
- **Domains**: Possible words for each slot
- **Constraints**: Overlapping letters must match

Uses **AC-3 algorithm** to reduce possibilities, then **backtracking search** to find solution. If stuck, requests words from AI matching the required pattern.

### 4. Validation
- Verifies structure meets NYT standards
- Confirms puzzle is solvable

### 5. Clue Generation
- Uses AI to generate engaging clues
- Falls back to placeholder clues without API

## Grid Requirements

The generator enforces NYT crossword standards:

- ✅ 180° rotational symmetry
- ✅ Full connectivity (no isolated sections)
- ✅ All words ≥ 3 letters
- ✅ All squares "checked" (crossed by 2 words)
- ✅ Black squares ≤ ~16% of grid

## Supported Sizes

| Size | Type | Notes |
|------|------|-------|
| 3×3 | Micro | Testing only |
| 5×5 | Mini | NYT Mini style |
| 7×7 | Small | Quick solve |
| 9×9 | Medium | ~5-10 min solve |
| 11×11 | Large | ~15 min solve |
| 13×13 | Standard- | Approaching daily |
| 15×15 | Standard | NYT Daily size |

## AI Features

With an Anthropic API key, the generator:

1. **Themed Words**: Generates vocabulary related to your topic
2. **Pattern Matching**: When solver needs a word like `S_A_E`, asks AI
3. **Smart Clues**: Creates engaging, difficulty-appropriate clues

Without an API key, the generator still works using:
- Built-in word list
- Placeholder clues

## Troubleshooting

### "Could not fill grid"
- Try a smaller size first
- Some themes may lack words at certain lengths
- Generator will retry with different patterns

### "No solution found"
- Word list may lack required words
- Try broader theme or add API key

### Slow generation
- 15×15 grids can take 30+ seconds
- AC-3 reduces search space significantly

## License

MIT License - Feel free to use and modify.

## Credits

- CSP algorithms based on Russell & Norvig's "AI: A Modern Approach"
- AI integration via Anthropic Claude API
