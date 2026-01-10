"""
SVG Renderer for crossword puzzles.
Converts Markdown crossword format to SVG.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class SVGConfig:
    """Configuration for SVG rendering."""
    cell_size: int = 40
    border_width: int = 2
    inner_border_width: int = 1
    
    # Colors
    background_color: str = "#FFFFFF"
    grid_color: str = "#000000"
    block_color: str = "#000000"
    letter_color: str = "#000000"
    number_color: str = "#333333"
    
    # Fonts
    font_family: str = "Arial, Helvetica, sans-serif"
    letter_font_size: int = 24
    number_font_size: int = 10
    
    # Padding
    number_offset_x: int = 3
    number_offset_y: int = 12
    letter_offset_x: int = 20  # Center of cell
    letter_offset_y: int = 30  # Slightly below center


class SVGRenderer:
    """Renders crossword puzzles as SVG."""
    
    def __init__(self, config: Optional[SVGConfig] = None):
        self.config = config or SVGConfig()
    
    def render_from_markdown(
        self, 
        markdown: str, 
        show_solution: bool = False
    ) -> str:
        """
        Render SVG from Markdown crossword format.
        
        Args:
            markdown: Markdown string in the simple format
            show_solution: Whether to show letters in the grid
            
        Returns:
            SVG string
        """
        # Parse the markdown
        parsed = self._parse_markdown(markdown)
        
        return self.render(
            grid=parsed["grid"],
            numbers=parsed["numbers"],
            size=parsed["size"],
            title=parsed.get("title", "Crossword"),
            show_solution=show_solution
        )
    
    def render(
        self,
        grid: List[List[str]],
        numbers: Dict[Tuple[int, int], int],
        size: int,
        title: str = "Crossword",
        show_solution: bool = False
    ) -> str:
        """
        Render SVG from grid data.
        
        Args:
            grid: 2D list of characters ('#' for blocks, letters for filled, '.' for empty)
            numbers: Dict mapping (row, col) to clue numbers
            size: Grid size
            title: Puzzle title
            show_solution: Whether to show letters
            
        Returns:
            SVG string
        """
        cfg = self.config
        
        # Calculate dimensions
        grid_width = size * cfg.cell_size
        grid_height = size * cfg.cell_size
        total_width = grid_width + 2 * cfg.border_width
        total_height = grid_height + 2 * cfg.border_width
        
        svg_parts = []
        
        # SVG header
        svg_parts.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {total_width} {total_height}" '
            f'width="{total_width}" height="{total_height}">'
        )
        
        # Title (for accessibility)
        svg_parts.append(f'  <title>{title}</title>')
        
        # Styles
        svg_parts.append('  <style>')
        svg_parts.append(f'    .cell {{ stroke: {cfg.grid_color}; stroke-width: {cfg.inner_border_width}; }}')
        svg_parts.append(f'    .block {{ fill: {cfg.block_color}; }}')
        svg_parts.append(f'    .empty {{ fill: {cfg.background_color}; }}')
        svg_parts.append(f'    .number {{ font-family: {cfg.font_family}; font-size: {cfg.number_font_size}px; fill: {cfg.number_color}; }}')
        svg_parts.append(f'    .letter {{ font-family: {cfg.font_family}; font-size: {cfg.letter_font_size}px; fill: {cfg.letter_color}; text-anchor: middle; }}')
        svg_parts.append('  </style>')
        
        # Background
        svg_parts.append(
            f'  <rect x="0" y="0" width="{total_width}" height="{total_height}" '
            f'fill="{cfg.background_color}" />'
        )
        
        # Outer border
        svg_parts.append(
            f'  <rect x="{cfg.border_width/2}" y="{cfg.border_width/2}" '
            f'width="{grid_width + cfg.border_width}" height="{grid_height + cfg.border_width}" '
            f'fill="none" stroke="{cfg.grid_color}" stroke-width="{cfg.border_width}" />'
        )
        
        # Grid cells
        for row in range(size):
            for col in range(size):
                x = cfg.border_width + col * cfg.cell_size
                y = cfg.border_width + row * cfg.cell_size
                
                cell_char = grid[row][col] if row < len(grid) and col < len(grid[row]) else '.'
                
                if cell_char == '#':
                    # Black square
                    svg_parts.append(
                        f'  <rect x="{x}" y="{y}" '
                        f'width="{cfg.cell_size}" height="{cfg.cell_size}" '
                        f'class="cell block" />'
                    )
                else:
                    # White square
                    svg_parts.append(
                        f'  <rect x="{x}" y="{y}" '
                        f'width="{cfg.cell_size}" height="{cfg.cell_size}" '
                        f'class="cell empty" />'
                    )
                    
                    # Add number if present
                    if (row, col) in numbers:
                        num = numbers[(row, col)]
                        svg_parts.append(
                            f'  <text x="{x + cfg.number_offset_x}" '
                            f'y="{y + cfg.number_offset_y}" '
                            f'class="number">{num}</text>'
                        )
                    
                    # Add letter if showing solution
                    if show_solution and cell_char not in ('.', '#'):
                        svg_parts.append(
                            f'  <text x="{x + cfg.letter_offset_x}" '
                            f'y="{y + cfg.letter_offset_y}" '
                            f'class="letter">{cell_char}</text>'
                        )
        
        svg_parts.append('</svg>')
        
        return '\n'.join(svg_parts)
    
    def render_with_clues(
        self,
        grid: List[List[str]],
        numbers: Dict[Tuple[int, int], int],
        across_clues: List[Tuple[int, str]],
        down_clues: List[Tuple[int, str]],
        size: int,
        title: str = "Crossword",
        show_solution: bool = False
    ) -> str:
        """
        Render SVG with grid and clues.
        
        Returns a complete puzzle page with grid on top and clues below.
        """
        cfg = self.config
        
        # Grid dimensions
        grid_width = size * cfg.cell_size
        grid_height = size * cfg.cell_size
        
        # Clue section dimensions
        clue_font_size = 12
        clue_line_height = 16
        clue_width = 300
        clue_padding = 20
        
        # Calculate clue heights
        across_height = len(across_clues) * clue_line_height + 30
        down_height = len(down_clues) * clue_line_height + 30
        clue_section_height = max(across_height, down_height) + clue_padding
        
        # Total dimensions
        total_width = max(grid_width + 2 * cfg.border_width, 2 * clue_width + clue_padding)
        total_height = grid_height + 2 * cfg.border_width + clue_section_height + 50  # 50 for title
        
        svg_parts = []
        
        # SVG header
        svg_parts.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {total_width} {total_height}" '
            f'width="{total_width}" height="{total_height}">'
        )
        
        # Styles
        svg_parts.append('  <style>')
        svg_parts.append(f'    .cell {{ stroke: {cfg.grid_color}; stroke-width: {cfg.inner_border_width}; }}')
        svg_parts.append(f'    .block {{ fill: {cfg.block_color}; }}')
        svg_parts.append(f'    .empty {{ fill: {cfg.background_color}; }}')
        svg_parts.append(f'    .number {{ font-family: {cfg.font_family}; font-size: {cfg.number_font_size}px; fill: {cfg.number_color}; }}')
        svg_parts.append(f'    .letter {{ font-family: {cfg.font_family}; font-size: {cfg.letter_font_size}px; fill: {cfg.letter_color}; text-anchor: middle; }}')
        svg_parts.append(f'    .title {{ font-family: {cfg.font_family}; font-size: 20px; font-weight: bold; fill: {cfg.letter_color}; }}')
        svg_parts.append(f'    .clue-header {{ font-family: {cfg.font_family}; font-size: 14px; font-weight: bold; fill: {cfg.letter_color}; }}')
        svg_parts.append(f'    .clue {{ font-family: {cfg.font_family}; font-size: {clue_font_size}px; fill: {cfg.letter_color}; }}')
        svg_parts.append('  </style>')
        
        # Background
        svg_parts.append(f'  <rect x="0" y="0" width="{total_width}" height="{total_height}" fill="{cfg.background_color}" />')
        
        # Title
        svg_parts.append(f'  <text x="{total_width/2}" y="30" class="title" text-anchor="middle">{title}</text>')
        
        # Grid (offset for title)
        grid_offset_x = (total_width - grid_width) / 2
        grid_offset_y = 50
        
        # Outer border
        svg_parts.append(
            f'  <rect x="{grid_offset_x}" y="{grid_offset_y}" '
            f'width="{grid_width}" height="{grid_height}" '
            f'fill="none" stroke="{cfg.grid_color}" stroke-width="{cfg.border_width}" />'
        )
        
        # Grid cells
        for row in range(size):
            for col in range(size):
                x = grid_offset_x + col * cfg.cell_size
                y = grid_offset_y + row * cfg.cell_size
                
                cell_char = grid[row][col] if row < len(grid) and col < len(grid[row]) else '.'
                
                if cell_char == '#':
                    svg_parts.append(
                        f'  <rect x="{x}" y="{y}" '
                        f'width="{cfg.cell_size}" height="{cfg.cell_size}" '
                        f'class="cell block" />'
                    )
                else:
                    svg_parts.append(
                        f'  <rect x="{x}" y="{y}" '
                        f'width="{cfg.cell_size}" height="{cfg.cell_size}" '
                        f'class="cell empty" />'
                    )
                    
                    if (row, col) in numbers:
                        svg_parts.append(
                            f'  <text x="{x + cfg.number_offset_x}" '
                            f'y="{y + cfg.number_offset_y}" '
                            f'class="number">{numbers[(row, col)]}</text>'
                        )
                    
                    if show_solution and cell_char not in ('.', '#'):
                        svg_parts.append(
                            f'  <text x="{x + cfg.letter_offset_x}" '
                            f'y="{y + cfg.letter_offset_y}" '
                            f'class="letter">{cell_char}</text>'
                        )
        
        # Clues section
        clue_y_start = grid_offset_y + grid_height + 30
        
        # Across clues
        svg_parts.append(f'  <text x="{clue_padding}" y="{clue_y_start}" class="clue-header">ACROSS</text>')
        for i, (num, clue) in enumerate(across_clues):
            y = clue_y_start + 20 + i * clue_line_height
            # Truncate long clues
            display_clue = clue[:40] + "..." if len(clue) > 40 else clue
            svg_parts.append(f'  <text x="{clue_padding}" y="{y}" class="clue">{num}. {display_clue}</text>')
        
        # Down clues
        down_x = total_width / 2 + clue_padding
        svg_parts.append(f'  <text x="{down_x}" y="{clue_y_start}" class="clue-header">DOWN</text>')
        for i, (num, clue) in enumerate(down_clues):
            y = clue_y_start + 20 + i * clue_line_height
            display_clue = clue[:40] + "..." if len(clue) > 40 else clue
            svg_parts.append(f'  <text x="{down_x}" y="{y}" class="clue">{num}. {display_clue}</text>')
        
        svg_parts.append('</svg>')
        
        return '\n'.join(svg_parts)
    
    def _parse_markdown(self, markdown: str) -> Dict:
        """Parse the simple Markdown format."""
        result = {
            "grid": [],
            "numbers": {},
            "size": 0,
            "title": "Crossword",
            "across_clues": [],
            "down_clues": []
        }
        
        # Parse frontmatter
        frontmatter_match = re.search(r'^---\n(.*?)\n---', markdown, re.DOTALL)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
            for line in frontmatter.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    if key == 'title':
                        result['title'] = value
                    elif key == 'size':
                        result['size'] = int(value)
        
        # Parse grid
        grid_match = re.search(r'```grid\n(.*?)\n```', markdown, re.DOTALL)
        if grid_match:
            grid_text = grid_match.group(1)
            for line in grid_text.strip().split('\n'):
                result['grid'].append(list(line))
            if not result['size']:
                result['size'] = len(result['grid'])
        
        # Parse numbers
        numbers_match = re.search(r'```numbers\n(.*?)\n```', markdown, re.DOTALL)
        if numbers_match:
            numbers_text = numbers_match.group(1)
            for line in numbers_text.strip().split('\n'):
                if ':' in line:
                    pos, num = line.split(':')
                    row, col = map(int, pos.split(','))
                    result['numbers'][(row, col)] = int(num)
        
        # Parse clues
        across_match = re.search(r'## ACROSS\n\n(.*?)(?=\n## DOWN|\Z)', markdown, re.DOTALL)
        if across_match:
            for line in across_match.group(1).strip().split('\n'):
                match = re.match(r'(\d+)\. (.+)', line)
                if match:
                    result['across_clues'].append((int(match.group(1)), match.group(2)))
        
        down_match = re.search(r'## DOWN\n\n(.*?)(?=\n#|\Z)', markdown, re.DOTALL)
        if down_match:
            for line in down_match.group(1).strip().split('\n'):
                match = re.match(r'(\d+)\. (.+)', line)
                if match:
                    result['down_clues'].append((int(match.group(1)), match.group(2)))
        
        return result
    
    def save(self, svg_content: str, filepath: str):
        """Save SVG to file."""
        with open(filepath, 'w') as f:
            f.write(svg_content)
