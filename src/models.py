"""
Data models for the crossword generator.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Tuple, Set
import re


class Direction(Enum):
    ACROSS = "across"
    DOWN = "down"


class CellType(Enum):
    EMPTY = "empty"
    LETTER = "letter"
    BLOCK = "block"


@dataclass
class Cell:
    """Represents a single cell in the crossword grid."""
    row: int
    col: int
    cell_type: CellType = CellType.EMPTY
    letter: Optional[str] = None
    number: Optional[int] = None  # Clue number if this starts a word
    
    def is_block(self) -> bool:
        return self.cell_type == CellType.BLOCK
    
    def is_empty(self) -> bool:
        return self.cell_type == CellType.EMPTY
    
    def is_letter(self) -> bool:
        return self.cell_type == CellType.LETTER


@dataclass(frozen=False)
class WordSlot:
    """Represents a slot where a word can be placed."""
    start_row: int
    start_col: int
    direction: Direction
    length: int
    number: Optional[int] = None  # Clue number
    cells: List[Tuple[int, int]] = field(default_factory=list)
    
    def __hash__(self):
        return hash((self.start_row, self.start_col, self.direction, self.length))
    
    def __eq__(self, other):
        if not isinstance(other, WordSlot):
            return False
        return (self.start_row == other.start_row and 
                self.start_col == other.start_col and
                self.direction == other.direction and
                self.length == other.length)
    
    def __post_init__(self):
        if not self.cells:
            self.cells = self._calculate_cells()
    
    def _calculate_cells(self) -> List[Tuple[int, int]]:
        """Calculate all cell positions for this slot."""
        cells = []
        for i in range(self.length):
            if self.direction == Direction.ACROSS:
                cells.append((self.start_row, self.start_col + i))
            else:
                cells.append((self.start_row + i, self.start_col))
        return cells
    
    def get_pattern(self, grid: 'Grid') -> str:
        """Get the current pattern (letters and wildcards) for this slot."""
        pattern = ""
        for row, col in self.cells:
            cell = grid.get_cell(row, col)
            if cell.letter:
                pattern += cell.letter
            else:
                pattern += "."
        return pattern
    
    def overlaps_with(self, other: 'WordSlot') -> Optional[Tuple[int, int]]:
        """
        Check if this slot overlaps with another.
        Returns (index_in_self, index_in_other) if they overlap, None otherwise.
        """
        for i, (r1, c1) in enumerate(self.cells):
            for j, (r2, c2) in enumerate(other.cells):
                if r1 == r2 and c1 == c2:
                    return (i, j)
        return None


@dataclass
class ThemedWord:
    """A word with its clue and theme relevance."""
    word: str
    clue: str
    theme_relevance: float = 1.0  # 0-1, how relevant to theme
    difficulty: str = "medium"  # easy, medium, hard
    
    def __post_init__(self):
        self.word = self.word.upper().replace(" ", "")


@dataclass
class Grid:
    """Represents the crossword grid."""
    size: int
    cells: List[List[Cell]] = field(default_factory=list)
    word_slots: List[WordSlot] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.cells:
            self.cells = [
                [Cell(row=r, col=c) for c in range(self.size)]
                for r in range(self.size)
            ]
    
    def get_cell(self, row: int, col: int) -> Cell:
        """Get cell at position."""
        return self.cells[row][col]
    
    def set_block(self, row: int, col: int):
        """Set a cell as a block (black square)."""
        self.cells[row][col].cell_type = CellType.BLOCK
        # Enforce 180° rotational symmetry
        sym_row = self.size - 1 - row
        sym_col = self.size - 1 - col
        self.cells[sym_row][sym_col].cell_type = CellType.BLOCK
    
    def set_letter(self, row: int, col: int, letter: str):
        """Set a letter in a cell."""
        self.cells[row][col].cell_type = CellType.LETTER
        self.cells[row][col].letter = letter.upper()
    
    def is_valid_position(self, row: int, col: int) -> bool:
        """Check if position is within grid bounds."""
        return 0 <= row < self.size and 0 <= col < self.size
    
    def count_blocks(self) -> int:
        """Count black squares."""
        count = 0
        for row in self.cells:
            for cell in row:
                if cell.is_block():
                    count += 1
        return count
    
    def block_ratio(self) -> float:
        """Calculate ratio of black squares to total cells."""
        total = self.size * self.size
        return self.count_blocks() / total
    
    def find_word_slots(self) -> List[WordSlot]:
        """Identify all word slots (across and down) in the grid."""
        slots = []
        number = 1
        
        for row in range(self.size):
            for col in range(self.size):
                cell = self.get_cell(row, col)
                if cell.is_block():
                    continue
                
                starts_across = False
                starts_down = False
                
                # Check if this starts an ACROSS word
                if col == 0 or self.get_cell(row, col - 1).is_block():
                    # Check if there's room for at least 3 letters
                    length = 0
                    for c in range(col, self.size):
                        if self.get_cell(row, c).is_block():
                            break
                        length += 1
                    if length >= 3:
                        starts_across = True
                        slots.append(WordSlot(
                            start_row=row,
                            start_col=col,
                            direction=Direction.ACROSS,
                            length=length,
                            number=number
                        ))
                
                # Check if this starts a DOWN word
                if row == 0 or self.get_cell(row - 1, col).is_block():
                    # Check if there's room for at least 3 letters
                    length = 0
                    for r in range(row, self.size):
                        if self.get_cell(r, col).is_block():
                            break
                        length += 1
                    if length >= 3:
                        starts_down = True
                        slots.append(WordSlot(
                            start_row=row,
                            start_col=col,
                            direction=Direction.DOWN,
                            length=length,
                            number=number if not starts_across else number
                        ))
                
                # Increment number if this cell starts any word
                if starts_across or starts_down:
                    self.cells[row][col].number = number
                    number += 1
        
        self.word_slots = slots
        return slots
    
    def is_connected(self) -> bool:
        """Check if all white cells are connected."""
        # Find first non-block cell
        start = None
        for row in range(self.size):
            for col in range(self.size):
                if not self.get_cell(row, col).is_block():
                    start = (row, col)
                    break
            if start:
                break
        
        if not start:
            return True  # All blocks is technically connected
        
        # BFS to find all connected cells
        visited = set()
        queue = [start]
        visited.add(start)
        
        while queue:
            row, col = queue.pop(0)
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = row + dr, col + dc
                if (self.is_valid_position(nr, nc) and 
                    (nr, nc) not in visited and
                    not self.get_cell(nr, nc).is_block()):
                    visited.add((nr, nc))
                    queue.append((nr, nc))
        
        # Count total non-block cells
        total_white = sum(
            1 for row in self.cells for cell in row if not cell.is_block()
        )
        
        return len(visited) == total_white
    
    def to_string(self, show_solution: bool = True) -> str:
        """Convert grid to string representation."""
        result = []
        for row in self.cells:
            line = ""
            for cell in row:
                if cell.is_block():
                    line += "■ "
                elif show_solution and cell.letter:
                    line += f"{cell.letter} "
                else:
                    line += "_ "
            result.append(line)
        return "\n".join(result)
    
    def validate(self) -> Dict[str, any]:
        """Validate grid against NYT requirements."""
        issues = []
        
        # Check block ratio
        ratio = self.block_ratio()
        if ratio > 0.16:
            issues.append(f"Too many black squares: {ratio:.1%} (max 16%)")
        
        # Check connectivity
        if not self.is_connected():
            issues.append("Grid is not fully connected")
        
        # Check word slots
        slots = self.find_word_slots()
        word_count = len(slots)
        
        # Count by direction
        across_count = sum(1 for s in slots if s.direction == Direction.ACROSS)
        down_count = sum(1 for s in slots if s.direction == Direction.DOWN)
        
        # Check minimum word length (should be 3+)
        short_words = [s for s in slots if s.length < 3]
        if short_words:
            issues.append(f"Found {len(short_words)} words shorter than 3 letters")
        
        # Check max word count (78 for themed, 72 for themeless)
        if word_count > 78:
            issues.append(f"Too many words: {word_count} (max 78)")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "stats": {
                "size": self.size,
                "block_count": self.count_blocks(),
                "block_ratio": ratio,
                "word_count": word_count,
                "across_count": across_count,
                "down_count": down_count,
                "is_connected": self.is_connected()
            }
        }


@dataclass
class Puzzle:
    """Complete crossword puzzle with grid, words, and clues."""
    title: str
    author: str
    grid: Grid
    theme: Optional[str] = None
    difficulty: str = "medium"  # monday, tuesday, ..., saturday
    words: Dict[Tuple[int, Direction], ThemedWord] = field(default_factory=dict)
    
    def get_across_clues(self) -> List[Tuple[int, str]]:
        """Get all across clues in order."""
        clues = []
        for (num, direction), word in sorted(self.words.items()):
            if direction == Direction.ACROSS:
                clues.append((num, word.clue))
        return clues
    
    def get_down_clues(self) -> List[Tuple[int, str]]:
        """Get all down clues in order."""
        clues = []
        for (num, direction), word in sorted(self.words.items()):
            if direction == Direction.DOWN:
                clues.append((num, word.clue))
        return clues


# Pattern matching utilities
def matches_pattern(word: str, pattern: str) -> bool:
    """
    Check if a word matches a pattern.
    Pattern uses '.' for unknown letters.
    Example: 'A.P.E' matches 'APPLE'
    """
    if len(word) != len(pattern):
        return False
    for w, p in zip(word.upper(), pattern.upper()):
        if p != '.' and w != p:
            return False
    return True


def pattern_to_regex(pattern: str) -> re.Pattern:
    """Convert a pattern to a regex for matching."""
    regex_str = "^" + pattern.replace(".", "[A-Z]") + "$"
    return re.compile(regex_str, re.IGNORECASE)
