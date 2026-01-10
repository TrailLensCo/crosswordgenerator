"""
Markdown exporter for crossword puzzles.
Exports puzzles to a structured Markdown format.
"""

from datetime import datetime
from typing import Dict, List, Optional
from models import Grid, Puzzle, WordSlot, Direction, ThemedWord


class MarkdownExporter:
    """Exports crossword puzzles to Markdown format."""
    
    def __init__(self, puzzle: Puzzle):
        self.puzzle = puzzle
        self.grid = puzzle.grid
    
    def export(self, filepath: Optional[str] = None) -> str:
        """
        Export puzzle to Markdown format.
        
        Args:
            filepath: Optional path to save the file
            
        Returns:
            Markdown string
        """
        md = []
        
        # Title and metadata
        md.append(f"# {self.puzzle.title}")
        md.append("")
        md.append("## Metadata")
        md.append("")
        md.append(f"- **Date**: {datetime.now().strftime('%Y-%m-%d')}")
        md.append(f"- **Author**: {self.puzzle.author}")
        if self.puzzle.theme:
            md.append(f"- **Theme**: {self.puzzle.theme}")
        md.append(f"- **Difficulty**: {self.puzzle.difficulty.title()}")
        md.append(f"- **Size**: {self.grid.size}×{self.grid.size}")
        
        # Stats
        validation = self.grid.validate()
        stats = validation["stats"]
        md.append(f"- **Word Count**: {stats['word_count']}")
        md.append(f"- **Black Squares**: {stats['block_count']} ({stats['block_ratio']:.1%})")
        md.append("")
        
        # Empty grid (for solving)
        md.append("## Grid")
        md.append("")
        md.append(self._render_grid_table(show_solution=False))
        md.append("")
        
        # Clues
        md.append("## Clues")
        md.append("")
        md.append("### Across")
        md.append("")
        for num, clue in self.puzzle.get_across_clues():
            md.append(f"{num}. {clue}")
        md.append("")
        
        md.append("### Down")
        md.append("")
        for num, clue in self.puzzle.get_down_clues():
            md.append(f"{num}. {clue}")
        md.append("")
        
        # Solution
        md.append("## Solution")
        md.append("")
        md.append(self._render_grid_table(show_solution=True))
        md.append("")
        
        result = "\n".join(md)
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(result)
        
        return result
    
    def _render_grid_table(self, show_solution: bool = False) -> str:
        """Render grid as a Markdown table."""
        lines = []
        
        # Header row with column numbers
        header = "| |"
        for col in range(self.grid.size):
            header += f" {col+1} |"
        lines.append(header)
        
        # Separator row
        separator = "|---|"
        for _ in range(self.grid.size):
            separator += "---|"
        lines.append(separator)
        
        # Data rows
        for row in range(self.grid.size):
            line = f"| {row+1} |"
            for col in range(self.grid.size):
                cell = self.grid.get_cell(row, col)
                if cell.is_block():
                    line += " ■ |"
                elif show_solution and cell.letter:
                    # Show number in superscript if present
                    if cell.number:
                        line += f" ^{cell.number}^{cell.letter} |"
                    else:
                        line += f" {cell.letter} |"
                else:
                    # Empty cell, show number if present
                    if cell.number:
                        line += f" ^{cell.number}^ |"
                    else:
                        line += "   |"
            lines.append(line)
        
        return "\n".join(lines)
    
    def export_simple(self, filepath: Optional[str] = None) -> str:
        """
        Export puzzle to a simpler Markdown format optimized for SVG conversion.
        
        This format is easier to parse programmatically.
        """
        md = []
        
        # YAML-style frontmatter
        md.append("---")
        md.append(f"title: {self.puzzle.title}")
        md.append(f"author: {self.puzzle.author}")
        md.append(f"date: {datetime.now().strftime('%Y-%m-%d')}")
        md.append(f"theme: {self.puzzle.theme or 'Themeless'}")
        md.append(f"difficulty: {self.puzzle.difficulty}")
        md.append(f"size: {self.grid.size}")
        md.append("---")
        md.append("")
        
        # Grid section (compact format)
        md.append("# GRID")
        md.append("")
        md.append("```grid")
        for row in range(self.grid.size):
            line = ""
            for col in range(self.grid.size):
                cell = self.grid.get_cell(row, col)
                if cell.is_block():
                    line += "#"
                elif cell.letter:
                    line += cell.letter
                else:
                    line += "."
            md.append(line)
        md.append("```")
        md.append("")
        
        # Numbers section
        md.append("# NUMBERS")
        md.append("")
        md.append("```numbers")
        for row in range(self.grid.size):
            for col in range(self.grid.size):
                cell = self.grid.get_cell(row, col)
                if cell.number:
                    md.append(f"{row},{col}:{cell.number}")
        md.append("```")
        md.append("")
        
        # Clues section
        md.append("# CLUES")
        md.append("")
        md.append("## ACROSS")
        md.append("")
        for num, clue in self.puzzle.get_across_clues():
            md.append(f"{num}. {clue}")
        md.append("")
        
        md.append("## DOWN")
        md.append("")
        for num, clue in self.puzzle.get_down_clues():
            md.append(f"{num}. {clue}")
        md.append("")
        
        result = "\n".join(md)
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(result)
        
        return result


def create_puzzle_from_solution(
    grid: Grid,
    solution: Dict[WordSlot, str],
    title: str = "Crossword Puzzle",
    author: str = "AI Generator",
    theme: Optional[str] = None,
    difficulty: str = "medium",
    clue_generator: Optional[callable] = None
) -> Puzzle:
    """
    Create a Puzzle object from a solved grid.
    
    Args:
        grid: The crossword grid
        solution: Mapping of WordSlots to words
        title: Puzzle title
        author: Puzzle author
        theme: Optional theme
        difficulty: Difficulty level
        clue_generator: Optional function to generate clues
                       Signature: (word: str, difficulty: str) -> str
    """
    puzzle = Puzzle(
        title=title,
        author=author,
        grid=grid,
        theme=theme,
        difficulty=difficulty
    )
    
    # Create words with clues
    for slot, word in solution.items():
        if clue_generator:
            clue = clue_generator(word, difficulty)
        else:
            clue = f"Clue for {word} ({len(word)} letters)"
        
        themed_word = ThemedWord(
            word=word,
            clue=clue,
            difficulty=difficulty
        )
        
        puzzle.words[(slot.number, slot.direction)] = themed_word
    
    return puzzle
