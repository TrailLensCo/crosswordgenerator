"""
Crossword Puzzle Validator

Validates that a generated puzzle is:
1. Structurally valid (meets NYT grid requirements)
2. Fillable (CSP can find at least one valid solution)

This ensures the puzzle can be completed before publishing.
"""

import os
import sys
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from copy import deepcopy
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Grid, WordSlot, Direction, matches_pattern, CellType


@dataclass
class ValidationResult:
    """Result of puzzle validation."""
    valid: bool
    fillable: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    stats: Dict = field(default_factory=dict)
    solution: Optional[Dict[WordSlot, str]] = None
    solve_time: float = 0.0
    
    def __str__(self):
        status = "✅ VALID" if self.valid else "❌ INVALID"
        fill_status = "✅ FILLABLE" if self.fillable else "❌ NOT FILLABLE"
        
        lines = [f"Structure: {status}", f"Fillability: {fill_status}"]
        
        if self.solve_time > 0:
            lines.append(f"Solve time: {self.solve_time:.2f}s")
        
        if self.errors:
            lines.append("\nErrors:")
            for e in self.errors:
                lines.append(f"  ❌ {e}")
        
        if self.warnings:
            lines.append("\nWarnings:")
            for w in self.warnings:
                lines.append(f"  ⚠️ {w}")
        
        if self.stats:
            lines.append("\nStats:")
            for k, v in self.stats.items():
                lines.append(f"  {k}: {v}")
        
        return "\n".join(lines)


class PuzzleValidator:
    """
    Validates crossword puzzles for structural correctness and fillability.
    """
    
    def __init__(self, grid: Grid, word_list: List[str]):
        """
        Initialize validator.
        
        Args:
            grid: The crossword grid (with black squares placed)
            word_list: List of valid words for filling
        """
        self.grid = grid
        self.word_list = [w.upper() for w in word_list if len(w) >= 3]
        self.words_by_length: Dict[int, Set[str]] = {}
        
        for word in self.word_list:
            length = len(word)
            if length not in self.words_by_length:
                self.words_by_length[length] = set()
            self.words_by_length[length].add(word)
    
    def validate(self, check_fillability: bool = True, timeout: float = 30.0) -> ValidationResult:
        """
        Validate the puzzle.
        
        Args:
            check_fillability: Whether to attempt solving (can be slow)
            timeout: Max seconds to spend on fillability check
            
        Returns:
            ValidationResult with details
        """
        result = ValidationResult(valid=True, fillable=False)
        
        # Step 1: Structural validation
        self._validate_structure(result)
        
        # Step 2: Fillability check (if structure is valid)
        if check_fillability and result.valid:
            self._check_fillability(result, timeout)
        
        return result
    
    def _validate_structure(self, result: ValidationResult):
        """Validate grid structure against NYT requirements."""
        size = self.grid.size
        result.stats["size"] = f"{size}x{size}"
        
        # Check size is odd (NYT requirement)
        if size % 2 == 0:
            result.warnings.append(f"Grid size {size} is even (NYT prefers odd)")
        
        # Check rotational symmetry
        if not self._check_symmetry():
            result.errors.append("Grid lacks 180° rotational symmetry")
        
        # Check connectivity
        if not self.grid.is_connected():
            result.errors.append("Grid is not fully connected (isolated sections)")
        
        # Check black square ratio
        ratio = self.grid.block_ratio()
        result.stats["black_squares"] = f"{self.grid.count_blocks()} ({ratio:.1%})"
        if ratio > 0.20:
            result.errors.append(f"Too many black squares: {ratio:.1%} (max ~16-17%)")
        elif ratio > 0.17:
            result.warnings.append(f"Black square ratio {ratio:.1%} is high")
        
        # Find word slots
        slots = self.grid.find_word_slots()
        across_slots = [s for s in slots if s.direction == Direction.ACROSS]
        down_slots = [s for s in slots if s.direction == Direction.DOWN]
        
        result.stats["total_words"] = len(slots)
        result.stats["across_words"] = len(across_slots)
        result.stats["down_words"] = len(down_slots)
        
        # Check for words shorter than 3 letters
        short_slots = [s for s in slots if s.length < 3]
        if short_slots:
            result.errors.append(f"Found {len(short_slots)} words shorter than 3 letters")
        
        # Check word count limits (NYT)
        if size == 15 and len(slots) > 78:
            result.warnings.append(f"Word count {len(slots)} exceeds NYT daily limit of 78")
        elif size == 21 and len(slots) > 140:
            result.warnings.append(f"Word count {len(slots)} exceeds NYT Sunday limit of 140")
        
        # Check for unchecked squares
        unchecked = self._find_unchecked_squares(slots)
        if unchecked:
            result.errors.append(f"Found {len(unchecked)} unchecked squares (not crossed by two words)")
        
        # Check word length distribution
        lengths = [s.length for s in slots]
        if lengths:
            avg_length = sum(lengths) / len(lengths)
            result.stats["avg_word_length"] = f"{avg_length:.1f}"
            result.stats["longest_word"] = max(lengths)
            result.stats["3_letter_words"] = sum(1 for l in lengths if l == 3)
        
        # Update valid flag
        result.valid = len(result.errors) == 0
    
    def _check_symmetry(self) -> bool:
        """Check if grid has 180° rotational symmetry."""
        size = self.grid.size
        for row in range(size):
            for col in range(size):
                cell = self.grid.get_cell(row, col)
                sym_row = size - 1 - row
                sym_col = size - 1 - col
                sym_cell = self.grid.get_cell(sym_row, sym_col)
                
                if cell.is_block() != sym_cell.is_block():
                    return False
        return True
    
    def _find_unchecked_squares(self, slots: List[WordSlot]) -> List[Tuple[int, int]]:
        """Find squares that are only part of one word (not crossed)."""
        # Count how many words each cell is part of
        cell_counts: Dict[Tuple[int, int], int] = {}
        
        for slot in slots:
            for cell_pos in slot.cells:
                cell_counts[cell_pos] = cell_counts.get(cell_pos, 0) + 1
        
        # Find cells with count == 1 (unchecked)
        unchecked = [pos for pos, count in cell_counts.items() if count == 1]
        return unchecked
    
    def _check_fillability(self, result: ValidationResult, timeout: float):
        """
        Attempt to fill the grid using CSP solver.
        
        This verifies the puzzle can actually be completed.
        """
        from csp_solver import CrosswordCSP
        
        # First, quick check: does each slot have at least one valid word?
        slots = self.grid.find_word_slots()
        empty_slots = []
        
        for slot in slots:
            available = self.words_by_length.get(slot.length, set())
            if not available:
                empty_slots.append(slot)
        
        if empty_slots:
            result.warnings.append(
                f"No words available for {len(empty_slots)} slot lengths: "
                f"{set(s.length for s in empty_slots)}"
            )
        
        # Attempt to solve
        start_time = time.time()
        
        # Make a copy of the grid for solving
        test_grid = deepcopy(self.grid)
        
        try:
            csp = CrosswordCSP(test_grid, self.word_list)
            solution = csp.solve(use_inference=True)
            
            elapsed = time.time() - start_time
            result.solve_time = elapsed
            
            if solution:
                result.fillable = True
                result.solution = solution
                result.stats["solve_backtracks"] = csp.stats["backtracks"]
                result.stats["solve_ac3_revisions"] = csp.stats["ac3_revisions"]
            else:
                result.fillable = False
                result.errors.append("CSP solver could not find a valid fill")
                
        except Exception as e:
            result.fillable = False
            result.errors.append(f"Solver error: {str(e)}")
            result.solve_time = time.time() - start_time


def validate_puzzle(
    grid: Grid, 
    word_list: List[str], 
    check_fillability: bool = True,
    timeout: float = 30.0
) -> ValidationResult:
    """
    Convenience function to validate a puzzle.
    
    Args:
        grid: The crossword grid
        word_list: Available words
        check_fillability: Whether to attempt solving
        timeout: Max solve time in seconds
        
    Returns:
        ValidationResult
    """
    validator = PuzzleValidator(grid, word_list)
    return validator.validate(check_fillability=check_fillability, timeout=timeout)


def test_validator():
    """Test the validator with sample grids."""
    from csp_solver import create_sample_word_list
    
    print("=" * 60)
    print("PUZZLE VALIDATOR TEST")
    print("=" * 60)
    
    word_list = create_sample_word_list()
    
    # Test 1: Valid 5x5 grid
    print("\n📋 Test 1: Valid 5x5 mini grid")
    print("-" * 40)
    
    grid1 = Grid(size=5)
    # Standard mini pattern with symmetric blocks
    grid1.set_block(1, 1)  # Also sets (3, 3)
    grid1.set_block(1, 3)  # Also sets (3, 1)
    
    result1 = validate_puzzle(grid1, word_list)
    print(result1)
    print(f"\nGrid:\n{grid1.to_string(show_solution=False)}")
    
    # Test 2: Invalid grid (not symmetric)
    print("\n\n📋 Test 2: Invalid grid (asymmetric)")
    print("-" * 40)
    
    grid2 = Grid(size=5)
    grid2.cells[1][1].cell_type = CellType.BLOCK  # Only set one block
    
    result2 = validate_puzzle(grid2, word_list, check_fillability=False)
    print(result2)
    
    # Test 3: Invalid grid (disconnected)
    print("\n\n📋 Test 3: Invalid grid (disconnected)")
    print("-" * 40)
    
    grid3 = Grid(size=5)
    # Create a wall that splits the grid
    for row in range(5):
        grid3.set_block(row, 2)
    
    result3 = validate_puzzle(grid3, word_list, check_fillability=False)
    print(result3)
    
    # Test 4: Valid 7x7 grid
    print("\n\n📋 Test 4: Valid 7x7 grid")
    print("-" * 40)
    
    grid4 = Grid(size=7)
    grid4.set_block(1, 1)
    grid4.set_block(1, 5)
    grid4.set_block(3, 3)
    grid4.set_block(5, 1)
    grid4.set_block(5, 5)
    
    result4 = validate_puzzle(grid4, word_list, timeout=10.0)
    print(result4)
    
    if result4.fillable and result4.solution:
        # Apply solution and show filled grid
        from csp_solver import CrosswordCSP
        csp = CrosswordCSP(grid4, word_list)
        csp.solution = result4.solution
        csp.apply_solution(result4.solution)
        print(f"\nFilled grid:\n{grid4.to_string(show_solution=True)}")


if __name__ == "__main__":
    test_validator()
