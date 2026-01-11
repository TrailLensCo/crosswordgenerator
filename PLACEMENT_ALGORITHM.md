# Crossword Puzzle Word Placement Algorithm - Detailed Design

## Overview

This document provides a comprehensive specification of the word placement algorithm used in the crossword puzzle generator. The algorithm uses **Constraint Satisfaction Problem (CSP)** techniques with **AC-3 arc consistency** and **backtracking search** enhanced with **MRV** and **LCV** heuristics.

**References:**
- [AC-3 Algorithm - Wikipedia](https://en.wikipedia.org/wiki/AC-3_algorithm)
- [CSP in Artificial Intelligence - GeeksforGeeks](https://www.geeksforgeeks.org/artificial-intelligence/constraint-satisfaction-problems-csp-in-artificial-intelligence/)
- [Crossword Puzzles as CSPs - Columbia University](http://www.cs.columbia.edu/~evs/ais/finalprojs/steinthal/)
- [Backtracking and Crossword Puzzles - Medium](https://medium.com/@vanacorec/backtracking-and-crossword-puzzles-4abe195166f9)

---

## 1. Problem Formulation

### 1.1 CSP Components

| Component | Definition | Example |
|-----------|------------|---------|
| **Variables** | Word slots in the grid | `X1` = 1-Across (5 letters), `X2` = 1-Down (7 letters) |
| **Domains** | Possible words for each slot | `D(X1)` = {APPLE, ARISE, ARGUE, ...} |
| **Constraints** | Rules that must be satisfied | Intersection letters must match |

### 1.2 Constraint Types

#### C1: Length Constraint
```
For each variable Xi:
  len(word) == slot.length
```
**Enforcement:** Pre-filter domains by length during initialization.

#### C2: Intersection Constraint (Binary)
```
For overlapping slots Xi and Xj at positions (pi, pj):
  word_i[pi] == word_j[pj]
```
**Example:**
```
1-Across: A P P L E
          |
1-Down:   A
          R
          R
          O
          W
```
Position 0 of 1-Across must equal position 0 of 1-Down.

#### C3: Uniqueness Constraint (Global)
```
For all variables Xi, Xj where i ≠ j:
  word_i ≠ word_j
```
**Enforcement:** Track used words globally; exclude from all domains.

#### C4: Pattern Constraint (Unary)
```
For variable Xi with existing letters in grid:
  matches_pattern(word, pattern)
```
**Example:** Pattern `A..LE` matches `APPLE`, `AXLE` but not `ARISE`.

---

## 2. Algorithm Phases

### 2.1 Phase Overview

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: INITIALIZATION                                    │
│  - Parse grid structure                                     │
│  - Identify all word slots                                  │
│  - Build initial domains from word list                     │
│  - Construct constraint graph                               │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 2: CONSTRAINT PROPAGATION                            │
│  - Enforce node consistency (pattern matching)              │
│  - Run AC-3 for arc consistency                             │
│  - Detect early failures (empty domains)                    │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 3: BACKTRACKING SEARCH                               │
│  - Select variable (MRV + Degree heuristic)                 │
│  - Order values (LCV heuristic)                             │
│  - Assign and propagate (MAC - Maintaining Arc Consistency) │
│  - Backtrack on failure                                     │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 4: SOLUTION APPLICATION                              │
│  - Write words to grid                                      │
│  - Validate final state                                     │
│  - Generate clue assignments                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Phase 1: Initialization

### 3.1 Grid Parsing

**Input:** Grid object with black squares placed

**Process:**
```python
def find_word_slots(grid) -> List[WordSlot]:
    slots = []
    clue_number = 1

    for row in range(grid.size):
        for col in range(grid.size):
            if is_white_cell(row, col):
                starts_across = (col == 0 or is_black(row, col-1)) and
                               (col + 1 < grid.size and is_white(row, col+1))
                starts_down = (row == 0 or is_black(row-1, col)) and
                             (row + 1 < grid.size and is_white(row+1, col))

                if starts_across:
                    slots.append(create_across_slot(row, col, clue_number))
                if starts_down:
                    slots.append(create_down_slot(row, col, clue_number))

                if starts_across or starts_down:
                    clue_number += 1

    return slots
```

**Output:** List of `WordSlot` objects with:
- Position (row, col)
- Direction (ACROSS/DOWN)
- Length
- Clue number
- Cell coordinates

### 3.2 Domain Initialization

**Process:**
```python
def initialize_domains(slots, word_list) -> Dict[WordSlot, Set[str]]:
    # Group words by length
    words_by_length = defaultdict(set)
    for word in word_list:
        word = word.upper().strip()
        if len(word) >= 3:  # NYT minimum
            words_by_length[len(word)].add(word)

    # Assign domains
    domains = {}
    for slot in slots:
        domains[slot] = set(words_by_length[slot.length])

    return domains
```

**Edge Cases:**
| Case | Handling |
|------|----------|
| No words of required length | Domain is empty set; will trigger AI word generation |
| Very large domain (>10000 words) | Apply quality threshold filter |
| Slot length < 3 | Invalid grid; reject during validation |

### 3.3 Constraint Graph Construction

**Process:**
```python
def build_constraint_graph(slots) -> Dict[WordSlot, List[Tuple]]:
    neighbors = defaultdict(list)

    for i, slot1 in enumerate(slots):
        for slot2 in slots[i+1:]:
            overlap = find_overlap(slot1, slot2)
            if overlap:
                idx1, idx2 = overlap
                neighbors[slot1].append((slot2, idx1, idx2))
                neighbors[slot2].append((slot1, idx2, idx1))

    return neighbors

def find_overlap(slot1, slot2) -> Optional[Tuple[int, int]]:
    """Find intersection point between two slots."""
    cells1 = set(slot1.cells)
    cells2 = set(slot2.cells)
    intersection = cells1 & cells2

    if len(intersection) == 1:
        cell = intersection.pop()
        idx1 = slot1.cells.index(cell)
        idx2 = slot2.cells.index(cell)
        return (idx1, idx2)

    return None
```

**Overlap Combinations:**

| Slot 1 Direction | Slot 2 Direction | Can Overlap? | Max Overlaps |
|------------------|------------------|--------------|--------------|
| ACROSS | ACROSS | No (parallel) | 0 |
| DOWN | DOWN | No (parallel) | 0 |
| ACROSS | DOWN | Yes (perpendicular) | 1 |
| DOWN | ACROSS | Yes (perpendicular) | 1 |

---

## 4. Phase 2: Constraint Propagation

### 4.1 Node Consistency

**Purpose:** Remove values that violate unary constraints (pattern matching).

**Algorithm:**
```python
def enforce_node_consistency(grid, domains):
    for slot in domains:
        pattern = slot.get_pattern(grid)  # e.g., "A..LE"

        if '.' not in pattern:
            # Slot already filled
            domains[slot] = {pattern}
        else:
            # Filter by pattern
            domains[slot] = {
                word for word in domains[slot]
                if matches_pattern(word, pattern)
            }

def matches_pattern(word, pattern) -> bool:
    if len(word) != len(pattern):
        return False
    for w_char, p_char in zip(word, pattern):
        if p_char != '.' and w_char != p_char:
            return False
    return True
```

**Pattern Matching Cases:**

| Pattern | Word | Match? | Reason |
|---------|------|--------|--------|
| `A..LE` | APPLE | Yes | All fixed positions match |
| `A..LE` | AXLE | No | Length mismatch (4 vs 5) |
| `A..LE` | ARISE | No | Position 4 mismatch (S vs L) |
| `.....` | APPLE | Yes | All wildcards |
| `APPLE` | APPLE | Yes | Exact match |

### 4.2 AC-3 Algorithm

**Purpose:** Enforce arc consistency - ensure every value in a domain has a supporting value in neighboring domains.

**Algorithm:**
```python
def ac3(domains, neighbors, arcs=None) -> bool:
    """
    Returns True if arc consistency achieved.
    Returns False if any domain becomes empty (no solution).
    """
    if arcs is None:
        # Initialize with all arcs
        queue = []
        for slot in domains:
            for neighbor, _, _ in neighbors[slot]:
                queue.append((slot, neighbor))
    else:
        queue = list(arcs)

    while queue:
        slot_x, slot_y = queue.pop(0)

        if revise(domains, slot_x, slot_y, neighbors):
            if len(domains[slot_x]) == 0:
                # FAILURE: Empty domain
                return handle_empty_domain(slot_x, domains, neighbors)

            # Add affected arcs back to queue
            for neighbor, _, _ in neighbors[slot_x]:
                if neighbor != slot_y:
                    queue.append((neighbor, slot_x))

    return True

def revise(domains, slot_x, slot_y, neighbors) -> bool:
    """Remove inconsistent values from slot_x's domain."""
    revised = False
    overlap = find_overlap_indices(slot_x, slot_y, neighbors)

    if not overlap:
        return False

    idx_x, idx_y = overlap
    words_to_remove = set()

    for word_x in domains[slot_x]:
        char_needed = word_x[idx_x]

        # Check if any word in slot_y provides support
        has_support = any(
            word_y[idx_y] == char_needed and word_y != word_x
            for word_y in domains[slot_y]
        )

        if not has_support:
            words_to_remove.add(word_x)
            revised = True

    domains[slot_x] -= words_to_remove
    return revised
```

**AC-3 Revision Examples:**

```
Slot X (5 letters): {APPLE, ARISE, ARGUE}
Slot Y (4 letters): {AREA, ARCH, APEX}
Overlap: X[0] must equal Y[0]

Step 1: Check APPLE
  - Need Y word starting with 'A'
  - AREA[0]='A' ✓ → APPLE has support

Step 2: Check ARISE
  - Need Y word starting with 'A'
  - AREA[0]='A' ✓ → ARISE has support

Step 3: Check ARGUE
  - Need Y word starting with 'A'
  - AREA[0]='A' ✓ → ARGUE has support

Result: No revision needed (all have support)
```

```
Slot X (5 letters): {APPLE, XENON}
Slot Y (4 letters): {AREA, ARCH}
Overlap: X[0] must equal Y[0]

Step 1: Check APPLE
  - Need Y word starting with 'A'
  - AREA[0]='A' ✓ → APPLE has support

Step 2: Check XENON
  - Need Y word starting with 'X'
  - No Y word starts with 'X' ✗ → Remove XENON

Result: domains[X] = {APPLE}
```

### 4.3 Empty Domain Handling

**When a domain becomes empty, the algorithm must recover:**

```python
def handle_empty_domain(slot, domains, neighbors) -> bool:
    """
    Handle case where AC-3 empties a domain.
    Returns True if recovery successful, False otherwise.
    """
    # Strategy 1: Request AI-generated words
    if ai_word_generator and limiter.can_call('pattern_word_generation'):
        pattern = slot.get_pattern(grid)
        new_words = ai_word_generator.get_words_matching_pattern(
            pattern=pattern,
            count=20,
            used_words=used_words
        )

        if new_words:
            valid_new = [w for w in new_words if w not in used_words]
            if valid_new:
                domains[slot] = set(valid_new)
                words_by_length[slot.length].update(valid_new)
                return True

    # Strategy 2: Relax quality threshold
    if quality_threshold > 0.5:
        relaxed_words = get_words_with_lower_threshold(
            slot.length,
            quality_threshold - 0.2
        )
        pattern = slot.get_pattern(grid)
        matching = [w for w in relaxed_words if matches_pattern(w, pattern)]
        if matching:
            domains[slot] = set(matching)
            return True

    # Strategy 3: Signal backtrack needed
    return False
```

**Recovery Strategy Priority:**

| Priority | Strategy | Condition | Action |
|----------|----------|-----------|--------|
| 1 | AI word generation | AI available, within limits | Request pattern-matching words |
| 2 | Quality relaxation | Threshold > 0.5 | Lower quality threshold by 0.2 |
| 3 | Backtrack | During search | Undo last assignment, try next value |
| 4 | Fail | Pre-search | Report unsolvable grid |

---

## 5. Phase 3: Backtracking Search

### 5.1 Main Backtracking Algorithm

```python
def backtrack(assignment, domains, neighbors) -> Optional[Dict]:
    """
    Backtracking search with MAC (Maintaining Arc Consistency).

    Returns: Complete assignment or None if no solution.
    """
    # Base case: all variables assigned
    if len(assignment) == len(variables):
        return assignment

    # Select next variable (MRV + Degree)
    slot = select_unassigned_variable(assignment, domains, neighbors)
    if slot is None:
        return assignment

    # Try each value in order (LCV)
    for word in order_domain_values(slot, domains, neighbors, assignment):
        if is_consistent(slot, word, assignment, neighbors):
            # Make assignment
            assignment[slot] = word
            used_words.add(word)

            # Save state for backtracking
            saved_domains = deep_copy(domains)

            # Apply inference (MAC)
            domains[slot] = {word}
            inference_ok = ac3(
                domains,
                neighbors,
                arcs=[(neighbor, slot) for neighbor, _, _ in neighbors[slot]]
            )

            if inference_ok:
                result = backtrack(assignment, domains, neighbors)
                if result is not None:
                    return result

            # Backtrack
            del assignment[slot]
            used_words.remove(word)
            domains = saved_domains
            stats['backtracks'] += 1

    return None
```

### 5.2 Variable Selection: MRV + Degree Heuristic

**MRV (Minimum Remaining Values):** Choose the variable with the smallest domain.

**Degree Heuristic (tie-breaker):** Among variables with equal domain size, choose the one with the most constraints (neighbors).

```python
def select_unassigned_variable(assignment, domains, neighbors) -> Optional[WordSlot]:
    """
    Select next variable using MRV, then Degree heuristic.

    Rationale:
    - MRV: Variables with fewer options are more likely to cause failure.
           Trying them first detects failures earlier (fail-fast).
    - Degree: Variables with more constraints affect more other variables.
              Assigning them first provides more constraint propagation.
    """
    unassigned = [v for v in variables if v not in assignment]

    if not unassigned:
        return None

    return min(
        unassigned,
        key=lambda v: (
            len(domains[v]),        # Primary: smallest domain (MRV)
            -len(neighbors[v])      # Secondary: most neighbors (Degree)
        )
    )
```

**MRV Example:**

```
Unassigned slots:
  X1: domain size = 5, neighbors = 2
  X2: domain size = 3, neighbors = 4
  X3: domain size = 3, neighbors = 2
  X4: domain size = 8, neighbors = 1

Selection order:
  1. X2 (size=3, neighbors=4) - smallest domain, most neighbors
  2. X3 (size=3, neighbors=2) - smallest domain, fewer neighbors
  3. X1 (size=5, neighbors=2)
  4. X4 (size=8, neighbors=1)
```

### 5.3 Value Ordering: LCV Heuristic

**LCV (Least Constraining Value):** Try values that eliminate the fewest options from neighboring domains.

```python
def order_domain_values(slot, domains, neighbors, assignment) -> List[str]:
    """
    Order domain values using Least Constraining Value heuristic.

    Rationale:
    - Trying values that leave more options for neighbors
      increases the chance of finding a solution.
    """
    def count_eliminated(word):
        eliminated = 0
        for neighbor, idx_self, idx_neighbor in neighbors[slot]:
            if neighbor in assignment:
                continue  # Already assigned

            char = word[idx_self]
            for neighbor_word in domains[neighbor]:
                if neighbor_word[idx_neighbor] != char:
                    eliminated += 1

        return eliminated

    return sorted(domains[slot], key=count_eliminated)
```

**LCV Example:**

```
Slot X with domain {APPLE, AROMA, AZURE}
Neighbor Y with domain {ALTAR, AXLE, APEX, AZURE}
Overlap: X[0] == Y[0] (both start with same letter)

Count eliminated for each X value:
  APPLE (A): Y words not starting with A = 0
             → eliminates 0 options

  AROMA (A): Y words not starting with A = 0
             → eliminates 0 options

  AZURE (A): Y words not starting with A = 0
             → eliminates 0 options
             (but also removes AZURE from Y due to uniqueness)
             → eliminates 1 option

Order: [APPLE, AROMA, AZURE]
```

### 5.4 Consistency Checking

```python
def is_consistent(slot, word, assignment, neighbors) -> bool:
    """
    Check if assigning word to slot is consistent with current assignment.

    Checks:
    1. Word not already used (uniqueness)
    2. Overlapping letters match with assigned neighbors
    """
    # Check uniqueness
    if word in assignment.values():
        return False

    # Check overlap constraints with assigned neighbors
    for neighbor, idx_self, idx_neighbor in neighbors[slot]:
        if neighbor in assignment:
            neighbor_word = assignment[neighbor]
            if word[idx_self] != neighbor_word[idx_neighbor]:
                return False

    return True
```

**Consistency Check Matrix:**

| Constraint | Check | Failure Condition |
|------------|-------|-------------------|
| Uniqueness | `word in assignment.values()` | Word already used |
| Overlap | `word[idx_self] == neighbor_word[idx_neighbor]` | Letters don't match |

---

## 6. Exception Handling and Edge Cases

### 6.1 Grid-Level Exceptions

| Exception | Cause | Detection | Handling |
|-----------|-------|-----------|----------|
| **No valid grid pattern** | All pattern generations failed | Grid generator returns None | Report error, suggest different size |
| **Disconnected regions** | Black squares split grid | BFS connectivity check | Reject grid, regenerate |
| **Invalid slot length** | Slot < 3 letters | Slot finding phase | Reject grid, regenerate |
| **Too many black squares** | Ratio > 16% | Validation phase | Reject grid, regenerate |
| **Symmetry violation** | Non-180° symmetric | Validation phase | Reject grid, regenerate |

### 6.2 Domain-Level Exceptions

| Exception | Cause | Detection | Handling |
|-----------|-------|-----------|----------|
| **Empty initial domain** | No words of required length | Initialization | Request AI words or fail |
| **Domain exhausted by AC-3** | No consistent values | AC-3 revision | AI request → backtrack → fail |
| **All values eliminated** | Uniqueness + overlaps | Consistency check | Backtrack |
| **AI limit reached** | Max callbacks exceeded | Limiter check | Use base word list fallback |

### 6.3 Search-Level Exceptions

| Exception | Cause | Detection | Handling |
|-----------|-------|-----------|----------|
| **Excessive backtracks** | Hard puzzle or bad grid | Counter > threshold | Restart with different seed |
| **Search timeout** | Complexity too high | Timer | Return partial or fail |
| **No solution exists** | Impossible constraints | Backtrack returns None | Report unsolvable |
| **Memory exhaustion** | Too many saved states | Memory monitor | Reduce inference depth |

### 6.4 Exception Handling Code

```python
class PlacementError(Exception):
    """Base class for placement algorithm errors."""
    pass

class EmptyDomainError(PlacementError):
    """Raised when a domain becomes empty with no recovery possible."""
    def __init__(self, slot, pattern):
        self.slot = slot
        self.pattern = pattern
        super().__init__(f"No words available for {slot} with pattern '{pattern}'")

class BacktrackLimitError(PlacementError):
    """Raised when backtrack limit exceeded."""
    def __init__(self, count, limit):
        self.count = count
        self.limit = limit
        super().__init__(f"Backtrack limit exceeded: {count} > {limit}")

class AILimitError(PlacementError):
    """Raised when AI callback limit reached."""
    def __init__(self, prompt_type, limit):
        self.prompt_type = prompt_type
        self.limit = limit
        super().__init__(f"AI limit reached for {prompt_type}: {limit} calls")

def solve_with_recovery(grid, word_list, config) -> Optional[Dict]:
    """
    Solve with comprehensive exception handling and recovery.
    """
    max_attempts = config.get('max_solve_attempts', 3)
    backtrack_limit = config.get('backtrack_limit', 10000)

    for attempt in range(max_attempts):
        try:
            solver = CrosswordCSP(grid, word_list, config)
            solver.backtrack_limit = backtrack_limit

            solution = solver.solve()

            if solution:
                return solution
            else:
                # No solution found - try with different random seed
                random.seed(attempt * 42)
                continue

        except EmptyDomainError as e:
            logger.warning(f"Attempt {attempt}: {e}")
            # Try requesting more AI words for this pattern
            if ai_available and limiter.can_call('pattern_word_generation'):
                new_words = request_ai_words(e.pattern)
                word_list.extend(new_words)
            continue

        except BacktrackLimitError as e:
            logger.warning(f"Attempt {attempt}: {e}")
            # Try with increased limit or different approach
            backtrack_limit *= 2
            continue

        except AILimitError as e:
            logger.warning(f"Attempt {attempt}: {e}")
            # Continue without AI assistance
            break

    return None
```

---

## 7. AI Integration Points

### 7.1 Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CSP SOLVER                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ AC-3        │───▶│ Empty       │───▶│ AI Word     │     │
│  │ Revision    │    │ Domain?     │    │ Generator   │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                  │                  │             │
│         │                  │ No               │ Yes         │
│         ▼                  ▼                  ▼             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ Continue    │    │ Continue    │    │ Check       │     │
│  │ Propagation │    │ Search      │    │ AI Limiter  │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                                               │             │
│                                    ┌──────────┴──────────┐ │
│                                    │                     │ │
│                                    ▼                     ▼ │
│                            ┌─────────────┐    ┌─────────────┐
│                            │ Within      │    │ Limit       │
│                            │ Limit       │    │ Exceeded    │
│                            └─────────────┘    └─────────────┘
│                                    │                     │ │
│                                    ▼                     ▼ │
│                            ┌─────────────┐    ┌─────────────┐
│                            │ Call AI     │    │ Use Base    │
│                            │ API         │    │ Word List   │
│                            └─────────────┘    └─────────────┘
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Word Generator Callback

```python
def create_ai_word_generator(ai_client, limiter, config):
    """
    Create word generator callback for CSP solver.

    This function is called when AC-3 empties a domain and
    new words are needed to continue solving.
    """
    def word_generator(pattern: str, count: int) -> List[str]:
        # Check limiter
        if not limiter.can_call('pattern_word_generation'):
            logger.warning("AI pattern generation limit reached")
            return fallback_pattern_search(pattern, count)

        # Build prompt
        prompt = f"""
        Find {count} English words matching this crossword pattern:

        Pattern: {pattern}
        (where '.' represents unknown letters)

        Requirements:
        - Words must be real English words
        - Common words preferred over obscure ones
        - No abbreviations or acronyms
        - Words should be crossword-appropriate

        Topic context: {config.get('topic', 'general')}
        """

        try:
            response = ai_client.generate(prompt)
            words = parse_word_list(response)
            limiter.record_call('pattern_word_generation')

            # Validate words
            valid_words = [
                w for w in words
                if matches_pattern(w.upper(), pattern)
                and is_valid_crossword_word(w)
            ]

            return valid_words

        except Exception as e:
            logger.error(f"AI word generation failed: {e}")
            return fallback_pattern_search(pattern, count)

    return word_generator

def fallback_pattern_search(pattern: str, count: int) -> List[str]:
    """Search base word list for pattern matches."""
    length = len(pattern)
    candidates = base_words_by_length.get(length, [])

    matches = [
        word for word in candidates
        if matches_pattern(word, pattern)
    ]

    return matches[:count]
```

### 7.3 AI Call Scenarios

| Scenario | Trigger | AI Prompt Type | Fallback |
|----------|---------|----------------|----------|
| Initial word list | Start of generation | `themed_word_list` | Base word list |
| Pattern matching | AC-3 empties domain | `pattern_word_generation` | Base word list search |
| Clue generation | After puzzle filled | `clue_generation_batch` | Placeholder clues |
| Theme development | Before word list | `theme_development` | Simple theme |
| Validation | After completion | `validation_check` | Skip validation |

---

## 8. Performance Optimization

### 8.1 Complexity Analysis

| Operation | Time Complexity | Space Complexity |
|-----------|-----------------|------------------|
| Initialization | O(n × w) | O(n × w) |
| AC-3 | O(n² × d³) | O(n²) |
| Backtracking (worst) | O(d^n) | O(n × d) |
| MRV Selection | O(n) | O(1) |
| LCV Ordering | O(d × m) | O(d) |

Where:
- n = number of word slots
- d = average domain size
- w = total words in word list
- m = average number of neighbors

### 8.2 Optimization Techniques

**1. Domain Preprocessing**
```python
# Pre-filter by quality before solving
domains = {
    slot: {w for w in domain if word_quality(w) >= threshold}
    for slot, domain in domains.items()
}
```

**2. Constraint Ordering**
```python
# Process most constrained arcs first in AC-3
arcs.sort(key=lambda arc: len(domains[arc[0]]))
```

**3. Incremental Domain Updates**
```python
# Only recompute affected domains after assignment
affected_slots = {neighbor for neighbor, _, _ in neighbors[assigned_slot]}
for slot in affected_slots:
    update_domain(slot)
```

**4. Caching**
```python
# Cache pattern matching results
@lru_cache(maxsize=10000)
def matches_pattern(word: str, pattern: str) -> bool:
    ...
```

### 8.3 Performance Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Backtracks | > 1000 | > 5000 | Restart with different seed |
| AC-3 revisions | > 5000 | > 10000 | Consider simpler grid |
| Domain size | > 5000 | > 10000 | Apply quality filter |
| AI calls | > 30 | > 50 | Switch to base word list |
| Solve time | > 30s | > 60s | Timeout and report |

---

## 9. Algorithm Validation

### 9.1 Correctness Properties

**Soundness:** Any solution returned satisfies all constraints.
```
∀ solution S returned by algorithm:
  ∀ slot Xi, Xj in S where Xi and Xj overlap:
    S[Xi][overlap_idx_i] == S[Xj][overlap_idx_j]
  AND
  ∀ slot Xi, Xj in S where i ≠ j:
    S[Xi] ≠ S[Xj]
```

**Completeness:** If a solution exists, the algorithm will find it.
```
∀ grid G with valid word assignment:
  algorithm(G) returns valid solution
```

### 9.2 Test Cases

**Test 1: Simple 5×5 Grid**
```
Input:
  .....
  .#.#.
  .....
  .#.#.
  .....

Expected:
  - 6 word slots identified
  - Solution found in < 100 backtracks
  - All intersection constraints satisfied
```

**Test 2: Constrained Pattern**
```
Input:
  Slot X: length 5, pattern "A..LE"
  Domain: {APPLE, AGILE, ANKLE}

Expected:
  - Domain reduced to {APPLE, AGILE, ANKLE}
  - All match pattern
```

**Test 3: Arc Consistency**
```
Input:
  Slot X: {APPLE, XENON}
  Slot Y: {AREA, ARCH}
  Overlap: X[0] == Y[0]

Expected:
  - XENON removed from X's domain
  - Revision returns True
```

**Test 4: Backtracking Recovery**
```
Input:
  Grid with single solution
  Initial wrong assignment

Expected:
  - Backtrack triggered
  - Correct solution eventually found
```

---

## 10. Integration with EXPANDED_PROMPT.md

This document is referenced from `EXPANDED_PROMPT.md` for:

1. **Task 3.2** - CSP Solver Integration updates
2. **Testing Requirements** - Algorithm validation tests
3. **AI Integration** - Word generator callback specification

**Implementation files:**
- `src/csp_solver.py` - Main algorithm implementation
- `src/models.py` - WordSlot, Grid data structures
- `src/ai_word_generator.py` - AI callback implementation

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-11 | Claude | Initial detailed design |

---

## References

1. [AC-3 Algorithm - Wikipedia](https://en.wikipedia.org/wiki/AC-3_algorithm)
2. [Constraint Satisfaction Problems - GeeksforGeeks](https://www.geeksforgeeks.org/artificial-intelligence/constraint-satisfaction-problems-csp-in-artificial-intelligence/)
3. [Crossword Puzzles as CSPs - Columbia University](http://www.cs.columbia.edu/~evs/ais/finalprojs/steinthal/)
4. [Backtracking and Crossword Puzzles - Medium](https://medium.com/@vanacorec/backtracking-and-crossword-puzzles-4abe195166f9)
5. [Generating a Crossword Puzzle - Baeldung](https://www.baeldung.com/cs/generate-crossword-puzzle)
6. [CSP Stanford Lecture Notes](https://stanford-cs221.github.io/spring2023-extra/modules/csps/csps2.pdf)
7. [Solving CSPs - CamelEdge](https://cameledge.com/post/ai/constraint-satisfaction-problems)

---

*End of Detailed Placement Algorithm Design*
