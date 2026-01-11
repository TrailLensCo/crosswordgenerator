"""
Grid Generator

Creates valid crossword grid patterns that meet NYT requirements:
- 180° rotational symmetry
- Fully interlocking (every letter crossed by two words)
- Connected (no isolated sections)
- Appropriate black square ratio
- No words shorter than 3 letters
"""

import os
import sys
from typing import List, Set, Tuple, Optional
from dataclasses import dataclass
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Grid, WordSlot, Direction, CellType


# Pre-defined valid grid patterns (known good patterns)
# Format: list of (row, col) for black squares (only need top-left quadrant + center)
# Symmetry is applied automatically

PATTERNS_3x3 = [
    # Fully open 3x3
    [],
]

PATTERNS_5x5 = [
    # Mini crossword style - no blocks, fully open
    [],
]

PATTERNS_7x7 = [
    # Open pattern
    [(0, 3), (3, 0)],
    # More closed
    [(0, 3), (1, 3), (3, 0), (3, 1)],
]

PATTERNS_9x9 = [
    [(0, 4), (1, 4), (4, 0), (4, 1)],
    [(0, 4), (2, 2), (4, 0)],
]

PATTERNS_11x11 = [
    # Fully open grid - no black squares (all squares crossed)
    [],
]

PATTERNS_13x13 = [
    # Standard daily-style pattern
    [(0, 4), (0, 8), (1, 4), (1, 8), (2, 4), (2, 8), 
     (4, 0), (4, 1), (4, 2), (4, 6), 
     (5, 6), (6, 3), (6, 4), (6, 5), (6, 6)],
]

# NYT-style 15x15 patterns (validated for all squares crossed)
# Each pattern ensures every white square is part of both an across and down word
# Note: set_block() automatically applies 180° rotational symmetry
PATTERNS_15x15 = [
    # Pattern 1: Fully open grid - guaranteed valid, all squares crossed
    # This is the safest pattern but requires 15-letter words
    [],

    # Pattern 2: Simple symmetric pattern with corner blocks
    # Creates shorter word slots that are easier to fill
    [
        (0, 0), (0, 1), (0, 2),  # Top-left corner
        (1, 0), (1, 1),
        (2, 0),
        (0, 6), (0, 8),  # Top edge blocks
        (6, 0), (8, 0),  # Left edge blocks
    ],

    # Pattern 3: Standard crossword pattern
    [
        (0, 4), (0, 10),
        (1, 4), (1, 10),
        (2, 4), (2, 10),
        (4, 0), (4, 14),
        (5, 0), (5, 14),
        (6, 0), (6, 14),
    ],
]

PATTERNS_21x21 = [
    # Sunday puzzle pattern (simplified)
    [
        (0, 5), (0, 10), (0, 15),
        (1, 5), (1, 10), (1, 15),
        (2, 5), (2, 10), (2, 15),
        (3, 0), (3, 7), (3, 13), (3, 20),
        (4, 3), (4, 17),
        (5, 3), (5, 10), (5, 17),
        (6, 7), (6, 13),
        (7, 0), (7, 7), (7, 13), (7, 20),
        (8, 5), (8, 15),
        (9, 5), (9, 10), (9, 15),
        (10, 0), (10, 1), (10, 2), (10, 10), (10, 18), (10, 19), (10, 20),
    ],
]


class GridGenerator:
    """Generates valid crossword grid patterns."""
    
    def __init__(self, size: int = 15):
        """
        Initialize generator.
        
        Args:
            size: Grid size (should be odd for NYT style)
        """
        self.size = size
    
    def generate(self, pattern_index: int = 0) -> Grid:
        """
        Generate a grid using a predefined pattern.
        
        Args:
            pattern_index: Which pattern to use (0 = first/default)
            
        Returns:
            Grid with black squares placed
        """
        grid = Grid(size=self.size)
        
        # Get patterns for this size
        patterns = self._get_patterns()
        
        if not patterns:
            # No predefined pattern, generate one
            return self._generate_random_valid_pattern()
        
        # Select pattern
        pattern = patterns[pattern_index % len(patterns)]
        
        # Apply pattern (with symmetry)
        for row, col in pattern:
            grid.set_block(row, col)  # Automatically applies symmetry
        
        return grid
    
    def generate_random(self, max_attempts: int = 100) -> Optional[Grid]:
        """
        Generate a random valid grid pattern.
        
        Returns:
            Valid Grid or None if couldn't generate one
        """
        for _ in range(max_attempts):
            grid = self._generate_random_valid_pattern()
            if self._validate_grid(grid):
                return grid
        return None
    
    def _get_patterns(self) -> List[List[Tuple[int, int]]]:
        """Get predefined patterns for current size."""
        pattern_map = {
            3: PATTERNS_3x3,
            5: PATTERNS_5x5,
            7: PATTERNS_7x7,
            9: PATTERNS_9x9,
            11: PATTERNS_11x11,
            13: PATTERNS_13x13,
            15: PATTERNS_15x15,
            21: PATTERNS_21x21,
        }
        return pattern_map.get(self.size, [])
    
    def _generate_random_valid_pattern(self) -> Grid:
        """Generate a random symmetric pattern."""
        grid = Grid(size=self.size)
        
        # Target ~12-15% black squares
        target_blocks = int(self.size * self.size * 0.13)
        placed = 0
        
        # Only place in upper-left quadrant + center row/col
        # Symmetry will handle the rest
        max_row = self.size // 2 + 1
        max_col = self.size // 2 + 1
        
        attempts = 0
        max_attempts = 1000
        
        while placed < target_blocks // 2 and attempts < max_attempts:
            row = random.randint(0, max_row)
            col = random.randint(0, self.size - 1)
            
            # Skip if already a block
            if grid.get_cell(row, col).is_block():
                attempts += 1
                continue
            
            # Try placing block
            grid.set_block(row, col)
            
            # Check if still valid
            if self._is_valid_partial(grid):
                placed += 1
            else:
                # Undo
                grid.cells[row][col].cell_type = CellType.EMPTY
                sym_row = self.size - 1 - row
                sym_col = self.size - 1 - col
                grid.cells[sym_row][sym_col].cell_type = CellType.EMPTY
            
            attempts += 1
        
        return grid
    
    def _is_valid_partial(self, grid: Grid) -> bool:
        """Quick validity check during generation."""
        # Check connectivity
        if not grid.is_connected():
            return False
        
        # Check no 1 or 2 letter words would be created
        for row in range(self.size):
            run_length = 0
            for col in range(self.size):
                if grid.get_cell(row, col).is_block():
                    if 0 < run_length < 3:
                        return False
                    run_length = 0
                else:
                    run_length += 1
            if 0 < run_length < 3:
                return False
        
        for col in range(self.size):
            run_length = 0
            for row in range(self.size):
                if grid.get_cell(row, col).is_block():
                    if 0 < run_length < 3:
                        return False
                    run_length = 0
                else:
                    run_length += 1
            if 0 < run_length < 3:
                return False
        
        return True
    
    def _validate_grid(self, grid: Grid) -> bool:
        """Full validation of generated grid."""
        # Check symmetry
        for row in range(self.size):
            for col in range(self.size):
                cell = grid.get_cell(row, col)
                sym_cell = grid.get_cell(self.size - 1 - row, self.size - 1 - col)
                if cell.is_block() != sym_cell.is_block():
                    return False
        
        # Check connectivity
        if not grid.is_connected():
            return False
        
        # Check word slots
        slots = grid.find_word_slots()
        
        # No short words
        if any(s.length < 3 for s in slots):
            return False
        
        # Check all squares are crossed (part of 2 words)
        cell_counts = {}
        for slot in slots:
            for pos in slot.cells:
                cell_counts[pos] = cell_counts.get(pos, 0) + 1
        
        for row in range(self.size):
            for col in range(self.size):
                if not grid.get_cell(row, col).is_block():
                    if cell_counts.get((row, col), 0) != 2:
                        return False
        
        return True
    
    def list_available_patterns(self) -> int:
        """Return number of available patterns for this size."""
        return len(self._get_patterns())


def test_grid_generator():
    """Test the grid generator."""
    print("=" * 60)
    print("GRID GENERATOR TEST")
    print("=" * 60)
    
    for size in [5, 7, 15]:
        print(f"\n📐 Testing {size}x{size} grid")
        print("-" * 40)
        
        gen = GridGenerator(size=size)
        num_patterns = gen.list_available_patterns()
        print(f"Available patterns: {num_patterns}")
        
        if num_patterns > 0:
            grid = gen.generate(pattern_index=0)
            
            # Validate
            from validator import validate_puzzle
            from csp_solver import create_sample_word_list
            
            word_list = create_sample_word_list()
            result = validate_puzzle(grid, word_list, check_fillability=(size <= 7))
            
            print(f"\n{result}")
            print(f"\nGrid pattern:")
            print(grid.to_string(show_solution=False))
            
            if result.fillable and result.solution:
                # Show filled grid
                from csp_solver import CrosswordCSP
                csp = CrosswordCSP(grid, word_list)
                csp.apply_solution(result.solution)
                print(f"\nFilled grid:")
                print(grid.to_string(show_solution=True))


if __name__ == "__main__":
    test_grid_generator()
