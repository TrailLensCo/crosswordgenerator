# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.
# Unauthorized copying, distribution, or use of this file,
# via any medium, is strictly prohibited without the express
# written permission of TrailLensCo.

"""
YAML importer for crossword puzzles.

Imports puzzles from the YAML intermediate format,
allowing resumption of partial puzzles or loading
completed puzzles for rendering.
"""

from pathlib import Path
from typing import Dict, Optional, Tuple, List, Any

# Try to import yaml
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None

from models import Grid, WordSlot, Direction, CellType
from yaml_schema import PuzzleYAMLData


class YAMLImportError(Exception):
    """Raised when YAML import fails."""
    pass


class YAMLImporter:
    """
    Imports crossword puzzles from YAML intermediate format.

    Usage:
        importer = YAMLImporter()
        puzzle_data = importer.load('puzzle.yaml')
        grid, solution, clues = importer.to_components(puzzle_data)
    """

    def __init__(self):
        """Initialize the YAML importer."""
        if not HAS_YAML:
            raise YAMLImportError(
                "PyYAML is required for YAML import. "
                "Install with: pip install pyyaml"
            )

    def load(self, path: str) -> PuzzleYAMLData:
        """
        Load puzzle from YAML file.

        Args:
            path: Path to YAML file

        Returns:
            PuzzleYAMLData instance

        Raises:
            YAMLImportError: If file doesn't exist or is invalid
        """
        path = Path(path)

        if not path.exists():
            raise YAMLImportError(f"Puzzle file not found: {path}")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise YAMLImportError(f"Invalid YAML in puzzle file: {e}")

        if not isinstance(data, dict):
            raise YAMLImportError(
                f"Puzzle file must contain a YAML mapping, got {type(data)}"
            )

        return self.parse(data)

    def load_string(self, yaml_content: str) -> PuzzleYAMLData:
        """
        Load puzzle from YAML string.

        Args:
            yaml_content: YAML string content

        Returns:
            PuzzleYAMLData instance
        """
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise YAMLImportError(f"Invalid YAML content: {e}")

        if not isinstance(data, dict):
            raise YAMLImportError(
                f"YAML content must be a mapping, got {type(data)}"
            )

        return self.parse(data)

    def parse(self, data: Dict[str, Any]) -> PuzzleYAMLData:
        """
        Parse dictionary data into PuzzleYAMLData.

        Args:
            data: Dictionary from YAML

        Returns:
            PuzzleYAMLData instance
        """
        try:
            return PuzzleYAMLData.from_dict(data)
        except Exception as e:
            raise YAMLImportError(f"Failed to parse puzzle data: {e}")

    def to_grid(self, puzzle_data: PuzzleYAMLData) -> Grid:
        """
        Convert puzzle data to Grid object.

        Args:
            puzzle_data: PuzzleYAMLData instance

        Returns:
            Grid object with letters filled
        """
        size = puzzle_data.metadata.size
        grid = Grid(size=size)

        # Parse pattern to set blocks
        pattern_lines = puzzle_data.grid.pattern.strip().split('\n')
        for row, line in enumerate(pattern_lines):
            for col, char in enumerate(line):
                if char == '#':
                    grid.set_block(row, col)

        # Parse solution to set letters
        solution_lines = puzzle_data.grid.solution.strip().split('\n')
        for row, line in enumerate(solution_lines):
            for col, char in enumerate(line):
                if char not in ('#', '.') and char.isalpha():
                    grid.set_letter(row, col, char)

        # Set cell numbers from word slots
        for direction in ['across', 'down']:
            for ws in puzzle_data.word_slots.get(direction, []):
                cell = grid.get_cell(ws.row, ws.col)
                cell.number = ws.number

        return grid

    def to_solution(
        self,
        puzzle_data: PuzzleYAMLData
    ) -> Dict[WordSlot, str]:
        """
        Extract solution mapping from puzzle data.

        Args:
            puzzle_data: PuzzleYAMLData instance

        Returns:
            Dictionary mapping WordSlots to answer strings
        """
        solution = {}

        for direction_str, direction_enum in [
            ('across', Direction.ACROSS),
            ('down', Direction.DOWN)
        ]:
            for ws_data in puzzle_data.word_slots.get(direction_str, []):
                slot = WordSlot(
                    start_row=ws_data.row,
                    start_col=ws_data.col,
                    direction=direction_enum,
                    length=ws_data.length,
                    number=ws_data.number,
                )
                solution[slot] = ws_data.answer

        return solution

    def to_clues(
        self,
        puzzle_data: PuzzleYAMLData
    ) -> Dict[str, List[Tuple[int, str, int]]]:
        """
        Extract clues from puzzle data.

        Args:
            puzzle_data: PuzzleYAMLData instance

        Returns:
            Dictionary with 'across' and 'down' clue lists
        """
        clues = {'across': [], 'down': []}

        for direction in ['across', 'down']:
            for ws in puzzle_data.word_slots.get(direction, []):
                # Parse length from clue if present
                clue_text = ws.clue
                length = ws.length
                clues[direction].append((ws.number, clue_text, length))

        # Sort by number
        clues['across'].sort(key=lambda x: x[0])
        clues['down'].sort(key=lambda x: x[0])

        return clues

    def to_components(
        self,
        puzzle_data: PuzzleYAMLData
    ) -> Tuple[Grid, Dict[WordSlot, str], Dict[str, List]]:
        """
        Convert puzzle data to all components.

        Args:
            puzzle_data: PuzzleYAMLData instance

        Returns:
            Tuple of (grid, solution, clues)
        """
        grid = self.to_grid(puzzle_data)
        solution = self.to_solution(puzzle_data)
        clues = self.to_clues(puzzle_data)
        return grid, solution, clues

    def get_metadata(
        self,
        puzzle_data: PuzzleYAMLData
    ) -> Dict[str, Any]:
        """
        Extract metadata from puzzle data.

        Args:
            puzzle_data: PuzzleYAMLData instance

        Returns:
            Dictionary with metadata fields
        """
        return {
            'title': puzzle_data.metadata.title,
            'author': puzzle_data.metadata.author,
            'date': puzzle_data.metadata.date,
            'difficulty': puzzle_data.metadata.difficulty,
            'puzzle_type': puzzle_data.metadata.puzzle_type,
            'size': puzzle_data.metadata.size,
            'word_count': puzzle_data.metadata.word_count,
            'theme_entry_count': puzzle_data.metadata.theme_entry_count,
        }

    def get_theme(
        self,
        puzzle_data: PuzzleYAMLData
    ) -> Optional[Dict[str, Any]]:
        """
        Extract theme data from puzzle data.

        Args:
            puzzle_data: PuzzleYAMLData instance

        Returns:
            Theme dictionary or None
        """
        if not puzzle_data.theme:
            return None

        theme = {
            'concept': puzzle_data.theme.concept,
            'entries': [],
        }

        if puzzle_data.theme.revealer:
            theme['revealer'] = {
                'number': puzzle_data.theme.revealer.number,
                'direction': puzzle_data.theme.revealer.direction,
                'answer': puzzle_data.theme.revealer.answer,
                'clue': puzzle_data.theme.revealer.clue,
                'explanation': puzzle_data.theme.revealer.explanation,
            }

        for entry in puzzle_data.theme.entries:
            theme['entries'].append({
                'number': entry.number,
                'direction': entry.direction,
                'answer': entry.answer,
                'clue': entry.clue,
                'theme_connection': entry.theme_connection,
            })

        return theme

    def get_stats(
        self,
        puzzle_data: PuzzleYAMLData
    ) -> Dict[str, Any]:
        """
        Extract generation statistics from puzzle data.

        Args:
            puzzle_data: PuzzleYAMLData instance

        Returns:
            Dictionary with generation statistics
        """
        stats = puzzle_data.metadata.generation_stats
        return {
            'total_ai_calls': stats.total_ai_calls,
            'pattern_match_calls': stats.pattern_match_calls,
            'clue_generation_calls': stats.clue_generation_calls,
            'word_list_calls': stats.word_list_calls,
            'theme_development_calls': stats.theme_development_calls,
            'generation_time_seconds': stats.generation_time_seconds,
            'backtracks': stats.backtracks,
            'ac3_revisions': stats.ac3_revisions,
        }

    def validate_structure(
        self,
        puzzle_data: PuzzleYAMLData
    ) -> List[str]:
        """
        Validate puzzle data structure.

        Args:
            puzzle_data: PuzzleYAMLData instance

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check metadata
        if not puzzle_data.metadata.title:
            errors.append("Missing puzzle title")
        if not puzzle_data.metadata.author:
            errors.append("Missing puzzle author")
        if puzzle_data.metadata.size < 3:
            errors.append(f"Invalid size: {puzzle_data.metadata.size}")

        # Check grid
        if puzzle_data.grid.rows != puzzle_data.metadata.size:
            errors.append("Grid rows don't match metadata size")
        if puzzle_data.grid.columns != puzzle_data.metadata.size:
            errors.append("Grid columns don't match metadata size")

        # Check word slots
        total_slots = (
            len(puzzle_data.word_slots.get('across', [])) +
            len(puzzle_data.word_slots.get('down', []))
        )
        if total_slots == 0:
            errors.append("No word slots defined")

        # Check clues match word slots
        for direction in ['across', 'down']:
            for ws in puzzle_data.word_slots.get(direction, []):
                if not ws.clue:
                    errors.append(
                        f"Missing clue for {ws.number} {direction}"
                    )

        return errors


def load_puzzle_from_yaml(path: str) -> Tuple[Grid, Dict[WordSlot, str], Dict[str, List]]:
    """
    Convenience function to load puzzle from YAML file.

    Args:
        path: Path to YAML file

    Returns:
        Tuple of (grid, solution, clues)
    """
    importer = YAMLImporter()
    puzzle_data = importer.load(path)
    return importer.to_components(puzzle_data)
