# Crossword Puzzle Generator Prompt

## Instructions for Use

Replace `[TOPIC]` with your desired theme (e.g., "Hawaiian culture", "Space exploration", "1990s music", "Italian cuisine"). You may leave this as `[TOPIC]` and the AI will ask you to specify.

Optionally replace `[GRID_SIZE]` with either:
- `15x15` for a daily-style puzzle (Monday-Saturday)
- `21x21` for a Sunday-style puzzle
- Or leave as `[GRID_SIZE]` to be asked

Optionally replace `[DIFFICULTY]` with one of:
- `Monday` (easiest - straightforward clues)
- `Tuesday` (easy-medium)
- `Wednesday` (medium)
- `Thursday` (medium-hard, often tricky themes)
- `Saturday` (hardest - themeless, cryptic clues)
- `Sunday` (medium difficulty, larger grid, playful theme)
- Or leave as `[DIFFICULTY]` to be asked

Optionally replace `[PUZZLE_TYPE]` with one of:
- `Revealer` (themed puzzle with a special entry that explains the theme connection - most common type)
- `Themeless` (no theme, focuses entirely on quality fill and clever cluing - typical for Friday/Saturday)
- `Phrase Transformation` (common phrases are modified by adding/changing/removing words related to the topic)
- `Hidden Words` (theme-related words are hidden within longer answer phrases)
- `Rebus` (some squares contain multiple letters, typically related to the theme - advanced puzzle type)
- `Puns/Wordplay` (theme answers are puns or wordplay on the topic)
- `Add-a-Letter` (theme answers add a specific letter to common phrases)
- `Quote/Quip` (a famous quote or quip spans multiple theme entries)
- Or leave as `[PUZZLE_TYPE]` to be asked

## Topic, Grid Size, Difficulty, and Puzzle Type

**Topic:** [TOPIC]

**Grid Size:** [GRID_SIZE]

**Difficulty:** [DIFFICULTY]

**Puzzle Type:** [PUZZLE_TYPE]

---

## The Prompt

```
Create a crossword puzzle based on [TOPIC] following New York Times crossword submission guidelines.

### IMPORTANT: Clarification Process

Before beginning construction, use the AskUserQuestion tool to resolve any ambiguities or missing information. Specifically:

1. **If [TOPIC] is not specified or unclear**: Ask the user to specify the topic/theme for the crossword puzzle. Provide examples like regional culture, hobbies, historical events, pop culture, etc.

2. **If [GRID_SIZE] is not specified**: Ask the user which grid size they prefer:
   - 15x15 (daily-style, 78 words max, good for focused themes)
   - 21x21 (Sunday-style, 140 words max, allows for richer themes)

3. **If [DIFFICULTY] is not specified**: Ask the user which difficulty level they prefer:
   - Monday/Tuesday (easy - straightforward clues, common words)
   - Wednesday/Thursday (medium - more wordplay, specific knowledge)
   - Friday/Saturday (hard - themeless, cryptic misdirection)
   - Sunday (medium difficulty but larger grid with playful theme)

4. **If [PUZZLE_TYPE] is not specified**: Ask the user which puzzle type they prefer:
   - **Revealer**: A themed puzzle where one answer explicitly reveals or explains how the other theme entries connect (e.g., if theme entries hide animal names, the revealer might be "SOMETHING'S HIDING"). This is the most traditional themed crossword format.
   - **Themeless**: No theme - the puzzle focuses on interesting vocabulary and clever cluing throughout. Typically used for Friday and Saturday puzzles. Usually has fewer words (72 max for 15x15).
   - **Phrase Transformation**: Common phrases are modified in a consistent way related to the topic (e.g., adding "JAVA" to phrases for a coffee theme: "JAVA THE HUT" for "Jabba the Hutt").
   - **Hidden Words**: Theme-related words are concealed within longer answer phrases, usually consecutively (e.g., "OVERDRAWN" contains DRAW for an art-themed puzzle).
   - **Rebus**: Some squares contain multiple letters or a symbol instead of a single letter. All theme entries incorporate the rebus element (e.g., squares containing "HEART" in a Valentine's theme).
   - **Puns/Wordplay**: Theme answers are puns or plays on words related to the topic (e.g., "FIDEL CASTRO" → "FIDDLER ON THE ROOF" for a music theme).
   - **Add-a-Letter**: A specific letter is added to common phrases to create wacky new phrases (e.g., adding "B" to create "BRAIN CHECK" from "rain check").
   - **Quote/Quip**: A famous quotation or joke spans multiple long theme entries across the grid.

5. **Any other ambiguities**: If the topic could be interpreted multiple ways, or if there are regional/cultural variations to consider, ask for clarification.

Only proceed with puzzle construction after all necessary clarifications have been gathered.

### Grid and Output Requirements:
- Grid size: [GRID_SIZE]
- Difficulty level: [DIFFICULTY]
- Puzzle type: [PUZZLE_TYPE]
- Generate the following SVG files (8.5" x 11" / 612x792 pixels at 72 DPI):
  1. Empty puzzle grid with numbered cells
  2. Clue sheet (Across and Down)
  3. Answer key with filled grid
  4. Answer list without grid (clues with answers filled in)
- You may create an intermediate markdown file to organize the puzzle before generating SVGs

### New York Times Crossword Requirements (Official Guidelines)

#### What NYT Looks For:
- Intelligent, literate, entertaining and well-crafted crosswords
- Lively fill with words, phrases and names that solvers know or can infer from crossings
- Original, on-target clues pitched at the puzzle's intended difficulty level
- Variety of cultural reference points
- Playful themes rather than straightforward subjects

#### Theme Requirements:
- Themes should be fresh, interesting, narrowly defined and consistently applied
- If theme includes a particular kind of pun, all puns should be of that kind
- Themes and theme entries should be accessible to everyone
- Include a "revealer" - a phrase that relates to the themed entries
- Thursday and Sunday puzzles benefit from creative themes (but not always rebus)

#### Fill Requirements:
- Emphasize lively words, well-known names and fresh phrases
- Use common words that lend themselves to interesting cluing angles
- Include diversity in cultural references (age, gender, ethnicity, etc.)
- Avoid offensive language and words that might impact solvers negatively
- Non-English words allowed if familiar or inferable to non-speakers
- Avoid uncommon abbreviations
- Avoid partial phrases longer than 5 letters (e.g., "So ___" for BE IT is OK, but "So ___" for IT GOES is not)
- Minimize crosswordese (ERNE, ASTA, ARETE, YSER, etc.)
- Difficult words are fine if they're interesting knowledge or useful vocabulary
- NEVER let two obscure words or names cross
- **Word lists should be treated as dynamic and expandable** - when construction requires a word not in the base dictionary, add appropriate topic-related vocabulary as needed

#### Technical Specifications (MUST FOLLOW):
- 180-degree rotational symmetry (black squares)
- All-over interlock (grid must be fully connected)
- No unchecked squares (all letters must appear in both Across and Down answers)
- All answers must be at least 3 letters long
- Black squares used in moderation
- **Every clue MUST correspond to an actual entry in the grid** - you cannot write a clue without having that numbered entry present in the puzzle

#### CRITICAL: No Orphan Squares Rule
- EVERY white square in the grid MUST be part of both an Across answer AND a Down answer
- Every white square MUST be reachable by following a numbered clue
- There must be NO white squares that are disconnected from clues
- If a square cannot be part of a valid 3+ letter word in both directions, it MUST be a black square
- Before finalizing the grid, verify that every white cell belongs to exactly one Across entry and exactly one Down entry
- This is a hard requirement - puzzles with orphan/unchecked squares are invalid

#### Maximum Word Counts:
- 15x15 themed puzzle: 78 words maximum
- 15x15 themeless puzzle: 72 words maximum
- 21x21 Sunday puzzle: 140 words maximum

#### Clue Difficulty Guidelines:
Clues should reflect the day's difficulty. Example for the answer STRAP:
- Monday clue: "Subway rider's handhold" (straightforward definition)
- Wednesday clue: "Part of a bike helmet" (slightly more specific)
- Saturday clue: "What might keep a watch on you" (wordplay/misdirection)

#### Difficulty Progression:
- Monday: Easiest - direct clues, common words
- Tuesday: Easy-medium
- Wednesday: Medium
- Thursday: Medium-hard, often features tricky/gimmick themes
- Friday: Hard, typically themeless
- Saturday: Hardest, themeless, requires imaginative thinking
- Sunday: Medium (like Wed/Thu), larger grid with playful theme

### SVG File Specifications:

#### Page Setup (all files):
- Dimensions: 612 x 792 pixels (8.5" x 11" at 72 DPI)
- Margins: ~40px on sides

#### Puzzle Grid SVG:
- Cell size: 25px for 21x21, 30px for 15x15
- Black cells: filled black (#000000)
- White cells: white fill with black border
- Cell numbers: top-left corner, small font (8-9px)
- Grid centered on page
- Title at top

#### Clue Sheet SVG:
- Two-column layout for space efficiency
- Section headers: "ACROSS" and "DOWN" in bold
- Clue format: "1. Clue text here (letter count)"
- Theme clues marked with [THEME] or [REVEALER]
- Font: Georgia for headers, Arial for clues
- Font size: 9-10px for clues to fit all content

#### Answer Grid SVG:
- Same grid layout as puzzle
- Letters filled in each white cell (centered, ~12px font)
- Theme answers highlighted (dark red #8B0000 or similar)

#### Answer List SVG:
- Two-column layout
- Format: "1. Clue text — ANSWER"
- Theme answers in distinct color (dark red #8B0000)
- All answers in uppercase bold

### Construction Process:

1. **Theme Development**
   - Choose 3-5 theme entries that connect to [TOPIC] based on [PUZZLE_TYPE]
   - If using Revealer type: create a revealer that explains the theme connection
   - If using Themeless type: skip this step and focus on quality fill throughout
   - Ensure theme entries are evenly distributed and symmetrical (if applicable)

2. **Grid Construction & Dynamic Word List Management**
   - Place theme entries first (typically longest answers)
   - Maintain 180-degree rotational symmetry
   - Begin filling remaining grid with quality entries
   - Verify all crossings are valid words
   - Check word count limits
   
   **CRITICAL - Dynamic Word List Protocol:**
   - **Word lists are DYNAMIC and should be expanded as needed during puzzle construction**
   - When a slot cannot be filled with available dictionary words:
     1. Identify the unfillable pattern (e.g., `......SBN...` for 12 letters)
     2. Generate topic-appropriate words that match the pattern
     3. Add these words to the working word list
     4. Continue filling the puzzle
   - **Multiple iterations of word list updates are EXPECTED and ALLOWED**
   - For topic-specific puzzles (e.g., sourdough bread), prioritize adding:
     - Technical terminology related to the topic
     - Common phrases and compound words
     - Proper nouns if appropriate for difficulty level
     - Cross-domain vocabulary that intersects with the topic
   - Document added words for clue-writing reference
   - Quality threshold: added words must be:
     - Real words or legitimate phrases
     - Clueable at the target difficulty level
     - Not offensive or problematic
   - **Do NOT abandon fill attempts due to dictionary gaps** - expand the word list instead

3. **Clue Writing**
   - Write clues appropriate to [DIFFICULTY] level
   - Include cultural diversity in references
   - Add wordplay and humor where appropriate
   - Ensure theme clues hint at the connection
   - For dynamically-added words, craft clues that make them accessible to solvers

4. **Quality Checks**
   - Verify rotational symmetry
   - Confirm no unchecked squares
   - Validate all words are 3+ letters
   - Check that obscure words don't cross
   - Review for offensive content
   - Verify all dynamically-added words are legitimate and clueable
   - **CRITICAL**: Verify every white square is part of both an Across AND Down answer
   - **CRITICAL**: Ensure no orphan squares exist - every cell must connect to a clue
   - **CRITICAL**: Verify every clue corresponds to an actual numbered entry in the grid - no clue should exist without its corresponding grid entry

5. **Puzzle Validation Through Solving**
   - **REQUIRED**: You MUST manually validate the completed puzzle by attempting to solve it yourself
   - **Manual validation process (NOT programmatic)**:
     1. Start with the empty grid (black squares visible, clue numbers shown)
     2. Read through each clue as a solver would
     3. Attempt to fill in answers based on clues alone
     4. Use crossing letters to confirm or deduce difficult answers
     5. Work through the puzzle systematically until completion
   - Check for solvability issues during manual solving:
     - Ambiguous clues that could fit multiple valid words
     - Clues that are too obscure for the target difficulty level
     - Missing or incorrect crossing constraints that break the solve path
     - Clues that contain factual errors or misleading information
     - Over-constrained or under-constrained regions
   - Test the solving experience manually:
     - Can you solve the puzzle using only the clues and crossings?
     - Are there sufficient entry points (easy answers) to get started?
     - Do the crossings provide fair assistance for challenging answers?
     - Does the difficulty feel appropriate for [DIFFICULTY] level?
   - **If issues are found during manual validation, FIX them immediately**:
     - Revise ambiguous or incorrect clues
     - Replace problematic fill words if necessary
     - Adjust difficulty-inappropriate clues
     - Fix any unsolvable or broken crossing patterns
     - Re-test manually after each fix
   - Document any major changes made during validation
   - Only proceed to SVG generation after successful manual solve validation
   - **Note**: This manual validation ensures the puzzle is actually solvable and enjoyable for human solvers, not just theoretically correct

6. **SVG Generation**
   - Create all four SVG files
   - Verify printability at 8.5" x 11"
   - Ensure readability of all text

### Example Theme Approaches:

For a topic like "Coffee Culture":
- Theme type: Phrase transformation (adding JAVA, BREW, BEAN to phrases)
- Revealer: COFFEE BREAK or WAKE UP CALL
- Theme entries: JAVA THE HUT, BREW ORLEANS, BEAN COUNTER

For a topic like "Ocean Life":
- Theme type: Hidden words (sea creatures hidden in phrases)
- Revealer: SOMETHING FISHY
- Theme entries: Phrases containing hidden CRAB, SHARK, WHALE, etc.

Now create the crossword puzzle for [TOPIC] following all guidelines above.
```

---

## Quick Reference Card

| Setting | 15x15 Daily | 21x21 Sunday |
|---------|-------------|--------------|
| Max Words | 78 (themed) / 72 (themeless) | 140 |
| Cell Size (SVG) | 30px | 25px |
| Theme Entries | 3-4 | 4-6 |
| Difficulty | Varies by day | Wednesday/Thursday |
| Symmetry | 180-degree rotational | 180-degree rotational |

## Example Usage

To generate a puzzle about "Texas BBQ culture":

```
Create a crossword puzzle based on Texas BBQ culture following New York Times crossword submission guidelines.

### Grid and Output Requirements:
- Grid size: 21x21
- Difficulty level: Sunday
...
[rest of prompt]
```

---

## Source

These guidelines are based on the official New York Times Crossword Submission Guidelines from:
https://www.nytimes.com/puzzles/submissions/crossword (January 2026)
