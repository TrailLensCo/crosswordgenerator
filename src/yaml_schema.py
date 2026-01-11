# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.
# Unauthorized copying, distribution, or use of this file,
# via any medium, is strictly prohibited without the express
# written permission of TrailLensCo.

"""
YAML schema definitions for crossword puzzle intermediate format.

Defines the data structures for the YAML intermediate format that
replaces the markdown intermediate file.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime


@dataclass
class CellData:
    """Represents a single cell in the puzzle grid."""
    row: int
    col: int
    cell_type: str  # 'letter' or 'block'
    letter: Optional[str] = None
    number: Optional[int] = None
    across_clue: Optional[int] = None
    down_clue: Optional[int] = None


@dataclass
class WordSlotData:
    """Represents a word slot (across or down)."""
    number: int
    row: int
    col: int
    length: int
    answer: str
    clue: str
    is_theme: bool = False


@dataclass
class ThemeEntryData:
    """Represents a theme entry in the puzzle."""
    number: int
    direction: str  # 'across' or 'down'
    answer: str
    clue: str
    theme_connection: str = ""


@dataclass
class RevealerData:
    """Represents the revealer entry for themed puzzles."""
    number: int
    direction: str
    answer: str
    clue: str
    explanation: str = ""


@dataclass
class ThemeData:
    """Theme information for the puzzle."""
    revealer: Optional[RevealerData] = None
    entries: List[ThemeEntryData] = field(default_factory=list)
    concept: str = ""


@dataclass
class GridData:
    """Grid representation in the puzzle."""
    rows: int
    columns: int
    pattern: str  # Text representation with '.' and '#'
    solution: str  # Text representation with letters
    cells: List[CellData] = field(default_factory=list)


@dataclass
class GenerationStats:
    """Statistics from puzzle generation."""
    total_ai_calls: int = 0
    pattern_match_calls: int = 0
    clue_generation_calls: int = 0
    word_list_calls: int = 0
    theme_development_calls: int = 0
    generation_time_seconds: float = 0.0
    backtracks: int = 0
    ac3_revisions: int = 0


@dataclass
class ValidationResult:
    """Validation results for the puzzle."""
    symmetry_check: str = "passed"
    connectivity_check: str = "passed"
    word_length_check: str = "passed"
    checked_squares_check: str = "passed"
    word_count_check: str = "passed"
    black_square_ratio: float = 0.0
    all_checks_passed: bool = True
    issues: List[str] = field(default_factory=list)


@dataclass
class PuzzleMetadata:
    """Metadata for the puzzle."""
    title: str
    author: str
    date: str
    difficulty: str
    puzzle_type: str
    size: int
    word_count: int = 0
    theme_entry_count: int = 0
    generation_stats: GenerationStats = field(default_factory=GenerationStats)


@dataclass
class PuzzleYAMLData:
    """
    Complete puzzle data for YAML intermediate format.

    This is the main data structure that gets serialized to/from YAML.
    """
    metadata: PuzzleMetadata
    grid: GridData
    word_slots: Dict[str, List[WordSlotData]] = field(
        default_factory=lambda: {'across': [], 'down': []}
    )
    theme: Optional[ThemeData] = None
    clues: Dict[str, Dict[int, str]] = field(
        default_factory=lambda: {'across': {}, 'down': {}}
    )
    validation: ValidationResult = field(default_factory=ValidationResult)

    @classmethod
    def create_empty(
        cls,
        title: str,
        author: str,
        size: int,
        difficulty: str = "wednesday",
        puzzle_type: str = "revealer"
    ) -> 'PuzzleYAMLData':
        """
        Create an empty puzzle data structure.

        Args:
            title: Puzzle title
            author: Puzzle author
            size: Grid size
            difficulty: Puzzle difficulty
            puzzle_type: Type of puzzle

        Returns:
            Empty PuzzleYAMLData instance
        """
        today = datetime.now().strftime("%Y-%m-%d")

        return cls(
            metadata=PuzzleMetadata(
                title=title,
                author=author,
                date=today,
                difficulty=difficulty,
                puzzle_type=puzzle_type,
                size=size,
            ),
            grid=GridData(
                rows=size,
                columns=size,
                pattern="." * size * size,
                solution="",
            ),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for YAML serialization.

        Returns:
            Dictionary representation of the puzzle
        """
        # Build cells list for grid
        cells = []
        for cell in self.grid.cells:
            cell_dict = {
                'row': cell.row,
                'col': cell.col,
                'type': cell.cell_type,
            }
            if cell.letter:
                cell_dict['letter'] = cell.letter
            if cell.number:
                cell_dict['number'] = cell.number
            if cell.across_clue:
                cell_dict['across_clue'] = cell.across_clue
            if cell.down_clue:
                cell_dict['down_clue'] = cell.down_clue
            cells.append(cell_dict)

        # Build word slots
        word_slots = {
            'across': [
                {
                    'number': ws.number,
                    'row': ws.row,
                    'col': ws.col,
                    'length': ws.length,
                    'answer': ws.answer,
                    'clue': ws.clue,
                    'is_theme': ws.is_theme,
                }
                for ws in self.word_slots.get('across', [])
            ],
            'down': [
                {
                    'number': ws.number,
                    'row': ws.row,
                    'col': ws.col,
                    'length': ws.length,
                    'answer': ws.answer,
                    'clue': ws.clue,
                    'is_theme': ws.is_theme,
                }
                for ws in self.word_slots.get('down', [])
            ],
        }

        # Build theme data if present
        theme_dict = None
        if self.theme:
            theme_dict = {
                'concept': self.theme.concept,
            }
            if self.theme.revealer:
                theme_dict['revealer'] = {
                    'number': self.theme.revealer.number,
                    'direction': self.theme.revealer.direction,
                    'answer': self.theme.revealer.answer,
                    'clue': self.theme.revealer.clue,
                    'explanation': self.theme.revealer.explanation,
                }
            if self.theme.entries:
                theme_dict['entries'] = [
                    {
                        'number': e.number,
                        'direction': e.direction,
                        'answer': e.answer,
                        'clue': e.clue,
                        'theme_connection': e.theme_connection,
                    }
                    for e in self.theme.entries
                ]

        return {
            'metadata': {
                'title': self.metadata.title,
                'author': self.metadata.author,
                'date': self.metadata.date,
                'difficulty': self.metadata.difficulty,
                'puzzle_type': self.metadata.puzzle_type,
                'size': self.metadata.size,
                'word_count': self.metadata.word_count,
                'theme_entry_count': self.metadata.theme_entry_count,
                'generation_stats': {
                    'total_ai_calls': self.metadata.generation_stats.total_ai_calls,
                    'pattern_match_calls': (
                        self.metadata.generation_stats.pattern_match_calls
                    ),
                    'clue_generation_calls': (
                        self.metadata.generation_stats.clue_generation_calls
                    ),
                    'word_list_calls': (
                        self.metadata.generation_stats.word_list_calls
                    ),
                    'theme_development_calls': (
                        self.metadata.generation_stats.theme_development_calls
                    ),
                    'generation_time_seconds': (
                        self.metadata.generation_stats.generation_time_seconds
                    ),
                    'backtracks': self.metadata.generation_stats.backtracks,
                    'ac3_revisions': self.metadata.generation_stats.ac3_revisions,
                },
            },
            'grid': {
                'dimensions': {
                    'rows': self.grid.rows,
                    'columns': self.grid.columns,
                },
                'pattern': self.grid.pattern,
                'solution': self.grid.solution,
                'cells': cells,
            },
            'word_slots': word_slots,
            'theme': theme_dict,
            'clues': self.clues,
            'validation': {
                'symmetry_check': self.validation.symmetry_check,
                'connectivity_check': self.validation.connectivity_check,
                'word_length_check': self.validation.word_length_check,
                'checked_squares_check': self.validation.checked_squares_check,
                'word_count_check': self.validation.word_count_check,
                'black_square_ratio': self.validation.black_square_ratio,
                'all_checks_passed': self.validation.all_checks_passed,
                'issues': self.validation.issues,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PuzzleYAMLData':
        """
        Create PuzzleYAMLData from dictionary.

        Args:
            data: Dictionary representation (from YAML)

        Returns:
            PuzzleYAMLData instance
        """
        # Parse metadata
        meta_data = data.get('metadata', {})
        stats_data = meta_data.get('generation_stats', {})

        stats = GenerationStats(
            total_ai_calls=stats_data.get('total_ai_calls', 0),
            pattern_match_calls=stats_data.get('pattern_match_calls', 0),
            clue_generation_calls=stats_data.get('clue_generation_calls', 0),
            word_list_calls=stats_data.get('word_list_calls', 0),
            theme_development_calls=stats_data.get('theme_development_calls', 0),
            generation_time_seconds=stats_data.get('generation_time_seconds', 0.0),
            backtracks=stats_data.get('backtracks', 0),
            ac3_revisions=stats_data.get('ac3_revisions', 0),
        )

        metadata = PuzzleMetadata(
            title=meta_data.get('title', ''),
            author=meta_data.get('author', ''),
            date=meta_data.get('date', ''),
            difficulty=meta_data.get('difficulty', 'wednesday'),
            puzzle_type=meta_data.get('puzzle_type', 'revealer'),
            size=meta_data.get('size', 11),
            word_count=meta_data.get('word_count', 0),
            theme_entry_count=meta_data.get('theme_entry_count', 0),
            generation_stats=stats,
        )

        # Parse grid
        grid_data = data.get('grid', {})
        dimensions = grid_data.get('dimensions', {})

        cells = []
        for cell_data in grid_data.get('cells', []):
            cells.append(CellData(
                row=cell_data.get('row', 0),
                col=cell_data.get('col', 0),
                cell_type=cell_data.get('type', 'letter'),
                letter=cell_data.get('letter'),
                number=cell_data.get('number'),
                across_clue=cell_data.get('across_clue'),
                down_clue=cell_data.get('down_clue'),
            ))

        grid = GridData(
            rows=dimensions.get('rows', metadata.size),
            columns=dimensions.get('columns', metadata.size),
            pattern=grid_data.get('pattern', ''),
            solution=grid_data.get('solution', ''),
            cells=cells,
        )

        # Parse word slots
        slots_data = data.get('word_slots', {})
        word_slots = {'across': [], 'down': []}

        for direction in ['across', 'down']:
            for ws_data in slots_data.get(direction, []):
                word_slots[direction].append(WordSlotData(
                    number=ws_data.get('number', 0),
                    row=ws_data.get('row', 0),
                    col=ws_data.get('col', 0),
                    length=ws_data.get('length', 0),
                    answer=ws_data.get('answer', ''),
                    clue=ws_data.get('clue', ''),
                    is_theme=ws_data.get('is_theme', False),
                ))

        # Parse theme
        theme = None
        theme_data = data.get('theme')
        if theme_data:
            revealer = None
            if 'revealer' in theme_data:
                rev_data = theme_data['revealer']
                revealer = RevealerData(
                    number=rev_data.get('number', 0),
                    direction=rev_data.get('direction', 'across'),
                    answer=rev_data.get('answer', ''),
                    clue=rev_data.get('clue', ''),
                    explanation=rev_data.get('explanation', ''),
                )

            entries = []
            for entry_data in theme_data.get('entries', []):
                entries.append(ThemeEntryData(
                    number=entry_data.get('number', 0),
                    direction=entry_data.get('direction', 'across'),
                    answer=entry_data.get('answer', ''),
                    clue=entry_data.get('clue', ''),
                    theme_connection=entry_data.get('theme_connection', ''),
                ))

            theme = ThemeData(
                revealer=revealer,
                entries=entries,
                concept=theme_data.get('concept', ''),
            )

        # Parse clues
        clues = data.get('clues', {'across': {}, 'down': {}})
        # Convert string keys to int
        parsed_clues = {'across': {}, 'down': {}}
        for direction in ['across', 'down']:
            for key, value in clues.get(direction, {}).items():
                parsed_clues[direction][int(key)] = value

        # Parse validation
        val_data = data.get('validation', {})
        validation = ValidationResult(
            symmetry_check=val_data.get('symmetry_check', 'passed'),
            connectivity_check=val_data.get('connectivity_check', 'passed'),
            word_length_check=val_data.get('word_length_check', 'passed'),
            checked_squares_check=val_data.get('checked_squares_check', 'passed'),
            word_count_check=val_data.get('word_count_check', 'passed'),
            black_square_ratio=val_data.get('black_square_ratio', 0.0),
            all_checks_passed=val_data.get('all_checks_passed', True),
            issues=val_data.get('issues', []),
        )

        return cls(
            metadata=metadata,
            grid=grid,
            word_slots=word_slots,
            theme=theme,
            clues=parsed_clues,
            validation=validation,
        )
