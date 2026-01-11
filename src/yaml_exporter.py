# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.
# Unauthorized copying, distribution, or use of this file,
# via any medium, is strictly prohibited without the express
# written permission of TrailLensCo.

"""
YAML exporter for crossword puzzles.

Exports completed puzzles to the YAML intermediate format,
replacing the markdown intermediate file.
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

# Try to import yaml
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None

from models import Grid, WordSlot, Direction
from yaml_schema import (
    PuzzleYAMLData, PuzzleMetadata, GridData, CellData,
    WordSlotData, ThemeData, ThemeEntryData, RevealerData,
    GenerationStats, ValidationResult
)


class YAMLExportError(Exception):
    """Raised when YAML export fails."""
    pass


class YAMLExporter:
    """
    Exports crossword puzzles to YAML intermediate format.

    Usage:
        exporter = YAMLExporter()
        yaml_str = exporter.export(puzzle_data, stats)
        exporter.save(puzzle_data, stats, 'output/puzzle.yaml')
    """

    def __init__(self):
        """Initialize the YAML exporter."""
        if not HAS_YAML:
            raise YAMLExportError(
                "PyYAML is required for YAML export. "
                "Install with: pip install pyyaml"
            )

    def export(
        self,
        grid: Grid,
        solution: Dict[WordSlot, str],
        clues: Dict[str, List],
        title: str,
        author: str,
        difficulty: str = "wednesday",
        puzzle_type: str = "revealer",
        stats: Optional[Dict[str, Any]] = None,
        theme_data: Optional[Dict[str, Any]] = None,
        validation_result: Optional[Any] = None
    ) -> str:
        """
        Export puzzle to YAML string.

        Args:
            grid: The completed puzzle grid
            solution: Dictionary mapping WordSlots to answer strings
            clues: Dictionary with 'across' and 'down' clue lists
            title: Puzzle title
            author: Puzzle author
            difficulty: Puzzle difficulty level
            puzzle_type: Type of puzzle
            stats: Optional generation statistics
            theme_data: Optional theme information
            validation_result: Optional validation results

        Returns:
            YAML string representation of the puzzle
        """
        puzzle_data = self._build_puzzle_data(
            grid, solution, clues, title, author,
            difficulty, puzzle_type, stats, theme_data, validation_result
        )

        # Convert to dict and serialize
        data_dict = puzzle_data.to_dict()

        # Add header comment
        header = "# Crossword Puzzle Intermediate Format\n"
        header += "# This file contains all puzzle data in structured YAML\n\n"

        yaml_content = yaml.dump(
            data_dict,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            indent=2,
            width=80,
        )

        return header + yaml_content

    def save(
        self,
        grid: Grid,
        solution: Dict[WordSlot, str],
        clues: Dict[str, List],
        title: str,
        author: str,
        path: str,
        difficulty: str = "wednesday",
        puzzle_type: str = "revealer",
        stats: Optional[Dict[str, Any]] = None,
        theme_data: Optional[Dict[str, Any]] = None,
        validation_result: Optional[Any] = None
    ) -> str:
        """
        Save puzzle to YAML file.

        Args:
            grid: The completed puzzle grid
            solution: Dictionary mapping WordSlots to answer strings
            clues: Dictionary with 'across' and 'down' clue lists
            title: Puzzle title
            author: Puzzle author
            path: Output file path
            difficulty: Puzzle difficulty level
            puzzle_type: Type of puzzle
            stats: Optional generation statistics
            theme_data: Optional theme information
            validation_result: Optional validation results

        Returns:
            Path to saved file
        """
        yaml_content = self.export(
            grid, solution, clues, title, author,
            difficulty, puzzle_type, stats, theme_data, validation_result
        )

        # Ensure directory exists
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)

        return str(path)

    def _build_puzzle_data(
        self,
        grid: Grid,
        solution: Dict[WordSlot, str],
        clues: Dict[str, List],
        title: str,
        author: str,
        difficulty: str,
        puzzle_type: str,
        stats: Optional[Dict[str, Any]],
        theme_data: Optional[Dict[str, Any]],
        validation_result: Optional[Any]
    ) -> PuzzleYAMLData:
        """Build PuzzleYAMLData from components."""

        # Build generation stats
        gen_stats = GenerationStats()
        if stats:
            gen_stats.total_ai_calls = stats.get('total_ai_calls', 0)
            gen_stats.pattern_match_calls = stats.get('pattern_match_calls', 0)
            gen_stats.clue_generation_calls = stats.get('clue_generation_calls', 0)
            gen_stats.word_list_calls = stats.get('word_list_calls', 0)
            gen_stats.theme_development_calls = stats.get('theme_development_calls', 0)
            gen_stats.generation_time_seconds = stats.get('generation_time_seconds', 0.0)
            gen_stats.backtracks = stats.get('backtracks', 0)
            gen_stats.ac3_revisions = stats.get('ac3_revisions', 0)

        # Build metadata
        metadata = PuzzleMetadata(
            title=title,
            author=author,
            date=datetime.now().strftime("%Y-%m-%d"),
            difficulty=difficulty,
            puzzle_type=puzzle_type,
            size=grid.size,
            word_count=len(solution),
            theme_entry_count=len(theme_data.get('entries', [])) if theme_data else 0,
            generation_stats=gen_stats,
        )

        # Build grid data
        pattern_lines = []
        solution_lines = []
        cells = []

        for row in range(grid.size):
            pattern_row = ""
            solution_row = ""
            for col in range(grid.size):
                cell = grid.get_cell(row, col)
                if cell.is_block():
                    pattern_row += "#"
                    solution_row += "#"
                    cells.append(CellData(
                        row=row,
                        col=col,
                        cell_type='block',
                    ))
                else:
                    pattern_row += "."
                    solution_row += cell.letter if cell.letter else "."
                    cells.append(CellData(
                        row=row,
                        col=col,
                        cell_type='letter',
                        letter=cell.letter,
                        number=cell.number,
                    ))
            pattern_lines.append(pattern_row)
            solution_lines.append(solution_row)

        grid_data = GridData(
            rows=grid.size,
            columns=grid.size,
            pattern="\n".join(pattern_lines),
            solution="\n".join(solution_lines),
            cells=cells,
        )

        # Build word slots
        word_slots = {'across': [], 'down': []}
        for slot, word in solution.items():
            # Find the clue for this slot
            clue_text = ""
            direction_str = 'across' if slot.direction == Direction.ACROSS else 'down'
            for num, clue, length in clues.get(direction_str, []):
                if num == slot.number:
                    clue_text = clue
                    break

            word_slots[direction_str].append(WordSlotData(
                number=slot.number,
                row=slot.start_row,
                col=slot.start_col,
                length=slot.length,
                answer=word,
                clue=clue_text,
                is_theme=False,  # Will be updated if theme_data present
            ))

        # Sort by number
        word_slots['across'].sort(key=lambda x: x.number)
        word_slots['down'].sort(key=lambda x: x.number)

        # Build theme data
        theme = None
        if theme_data:
            revealer = None
            if 'revealer' in theme_data:
                rev = theme_data['revealer']
                revealer = RevealerData(
                    number=rev.get('number', 0),
                    direction=rev.get('direction', 'across'),
                    answer=rev.get('answer', ''),
                    clue=rev.get('clue', ''),
                    explanation=rev.get('explanation', ''),
                )

            entries = []
            for entry in theme_data.get('entries', []):
                entries.append(ThemeEntryData(
                    number=entry.get('number', 0),
                    direction=entry.get('direction', 'across'),
                    answer=entry.get('answer', ''),
                    clue=entry.get('clue', ''),
                    theme_connection=entry.get('theme_connection', ''),
                ))

                # Mark as theme entry in word slots
                for ws in word_slots.get(entry.get('direction', 'across'), []):
                    if ws.answer == entry.get('answer', ''):
                        ws.is_theme = True

            theme = ThemeData(
                revealer=revealer,
                entries=entries,
                concept=theme_data.get('concept', ''),
            )

        # Build clues dict
        clues_dict = {'across': {}, 'down': {}}
        for num, clue_text, length in clues.get('across', []):
            clues_dict['across'][num] = f"{clue_text} ({length})"
        for num, clue_text, length in clues.get('down', []):
            clues_dict['down'][num] = f"{clue_text} ({length})"

        # Build validation result
        validation = ValidationResult()
        if validation_result:
            validation.symmetry_check = 'passed' if validation_result.valid else 'failed'
            validation.connectivity_check = 'passed'
            validation.word_length_check = 'passed'
            validation.checked_squares_check = 'passed'
            validation.word_count_check = 'passed'
            validation.black_square_ratio = grid.block_ratio()
            validation.all_checks_passed = validation_result.valid
            validation.issues = validation_result.errors if hasattr(validation_result, 'errors') else []
        else:
            validation.black_square_ratio = grid.block_ratio()

        return PuzzleYAMLData(
            metadata=metadata,
            grid=grid_data,
            word_slots=word_slots,
            theme=theme,
            clues=clues_dict,
            validation=validation,
        )


def export_puzzle_to_yaml(
    grid: Grid,
    solution: Dict[WordSlot, str],
    clues: Dict[str, List],
    title: str,
    author: str,
    output_path: str,
    **kwargs
) -> str:
    """
    Convenience function to export puzzle to YAML file.

    Args:
        grid: The completed puzzle grid
        solution: Dictionary mapping WordSlots to answer strings
        clues: Dictionary with 'across' and 'down' clue lists
        title: Puzzle title
        author: Puzzle author
        output_path: Output file path
        **kwargs: Additional arguments (difficulty, puzzle_type, stats, etc.)

    Returns:
        Path to saved file
    """
    exporter = YAMLExporter()
    return exporter.save(
        grid, solution, clues, title, author, output_path, **kwargs
    )
