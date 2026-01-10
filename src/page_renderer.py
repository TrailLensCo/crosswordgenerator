"""
Multi-page Crossword Renderer

Generates a complete crossword puzzle package:
- Page 1: Empty puzzle grid with numbers
- Page 2: Clues (Across and Down)  
- Page 3: Solution grid with answers

Outputs:
- Individual SVG files for each page
- Combined PDF document
- Optional: Combined HTML with print styles
"""

import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PageConfig:
    """Configuration for page layout."""
    # Page dimensions (default: US Letter)
    page_width: int = 612  # 8.5 inches at 72 DPI
    page_height: int = 792  # 11 inches at 72 DPI
    
    # Margins
    margin_top: int = 50
    margin_bottom: int = 50
    margin_left: int = 50
    margin_right: int = 50
    
    # Grid settings
    cell_size: int = 32
    border_width: int = 2
    inner_border_width: int = 1
    
    # Colors
    background_color: str = "#FFFFFF"
    grid_color: str = "#000000"
    block_color: str = "#000000"
    letter_color: str = "#000000"
    number_color: str = "#555555"
    
    # Fonts
    font_family: str = "Arial, Helvetica, sans-serif"
    title_font_size: int = 24
    subtitle_font_size: int = 14
    letter_font_size: int = 20
    number_font_size: int = 9
    clue_font_size: int = 11
    clue_number_font_size: int = 11
    
    # Clue layout
    clue_line_height: int = 14
    clue_column_gap: int = 30


@dataclass 
class CrosswordData:
    """Complete crossword puzzle data."""
    title: str
    author: str
    size: int
    grid: List[List[str]]  # '#' for blocks, letters for filled, '.' for empty
    numbers: Dict[Tuple[int, int], int]  # (row, col) -> clue number
    across_clues: List[Tuple[int, str, int]]  # (number, clue, word_length)
    down_clues: List[Tuple[int, str, int]]  # (number, clue, word_length)
    theme: Optional[str] = None
    difficulty: str = "Medium"
    date: str = field(default_factory=lambda: datetime.now().strftime("%B %d, %Y"))
    copyright: str = ""


class CrosswordPageRenderer:
    """Renders multi-page crossword puzzle documents."""
    
    def __init__(self, config: Optional[PageConfig] = None):
        self.config = config or PageConfig()
    
    def render_all_pages(
        self, 
        data: CrosswordData,
        output_dir: str = ".",
        base_name: str = "crossword"
    ) -> Dict[str, str]:
        """
        Render all pages and save to files.
        
        Returns dict with paths to generated files.
        """
        os.makedirs(output_dir, exist_ok=True)
        
        files = {}
        
        # Page 1: Puzzle grid
        puzzle_svg = self.render_puzzle_page(data)
        puzzle_path = os.path.join(output_dir, f"{base_name}_puzzle.svg")
        with open(puzzle_path, 'w') as f:
            f.write(puzzle_svg)
        files['puzzle'] = puzzle_path
        
        # Page 2: Clues
        clues_svg = self.render_clues_page(data)
        clues_path = os.path.join(output_dir, f"{base_name}_clues.svg")
        with open(clues_path, 'w') as f:
            f.write(clues_svg)
        files['clues'] = clues_path
        
        # Page 3: Solution
        solution_svg = self.render_solution_page(data)
        solution_path = os.path.join(output_dir, f"{base_name}_solution.svg")
        with open(solution_path, 'w') as f:
            f.write(solution_svg)
        files['solution'] = solution_path
        
        # Combined HTML (for easy printing)
        html = self.render_combined_html(data)
        html_path = os.path.join(output_dir, f"{base_name}_complete.html")
        with open(html_path, 'w') as f:
            f.write(html)
        files['html'] = html_path
        
        # Markdown
        markdown = self.render_markdown(data)
        md_path = os.path.join(output_dir, f"{base_name}.md")
        with open(md_path, 'w') as f:
            f.write(markdown)
        files['markdown'] = md_path
        
        return files
    
    def render_puzzle_page(self, data: CrosswordData) -> str:
        """Render Page 1: Empty puzzle grid."""
        cfg = self.config
        
        # Calculate grid dimensions
        grid_size = data.size * cfg.cell_size
        
        # Center grid on page
        grid_x = (cfg.page_width - grid_size) / 2
        grid_y = cfg.margin_top + 60  # Space for title
        
        svg = self._svg_header()
        svg += self._render_styles()
        
        # Background
        svg += f'  <rect width="{cfg.page_width}" height="{cfg.page_height}" fill="{cfg.background_color}"/>\n'
        
        # Title
        svg += self._render_title(data)
        
        # Grid
        svg += self._render_grid(data, grid_x, grid_y, show_letters=False)
        
        # Footer with instructions
        footer_y = grid_y + grid_size + 40
        svg += f'  <text x="{cfg.page_width/2}" y="{footer_y}" class="footer" text-anchor="middle">'
        svg += f'See next page for clues</text>\n'
        
        svg += '</svg>'
        return svg
    
    def render_clues_page(self, data: CrosswordData) -> str:
        """Render Page 2: Clues."""
        cfg = self.config
        
        svg = self._svg_header()
        svg += self._render_styles()
        
        # Background
        svg += f'  <rect width="{cfg.page_width}" height="{cfg.page_height}" fill="{cfg.background_color}"/>\n'
        
        # Title
        svg += f'  <text x="{cfg.page_width/2}" y="{cfg.margin_top}" class="title" text-anchor="middle">'
        svg += f'{data.title} - Clues</text>\n'
        
        # Calculate column layout
        content_width = cfg.page_width - cfg.margin_left - cfg.margin_right
        column_width = (content_width - cfg.clue_column_gap) / 2
        
        start_y = cfg.margin_top + 40
        
        # Render ACROSS clues in left column
        svg += self._render_clue_column(
            data.across_clues, 
            "ACROSS", 
            cfg.margin_left, 
            start_y,
            column_width
        )
        
        # Render DOWN clues in right column
        svg += self._render_clue_column(
            data.down_clues,
            "DOWN",
            cfg.margin_left + column_width + cfg.clue_column_gap,
            start_y,
            column_width
        )
        
        # Page number
        svg += f'  <text x="{cfg.page_width/2}" y="{cfg.page_height - 30}" class="footer" text-anchor="middle">'
        svg += f'Page 2</text>\n'
        
        svg += '</svg>'
        return svg
    
    def render_solution_page(self, data: CrosswordData) -> str:
        """Render Page 3: Solution grid."""
        cfg = self.config
        
        # Calculate grid dimensions
        grid_size = data.size * cfg.cell_size
        
        # Center grid on page
        grid_x = (cfg.page_width - grid_size) / 2
        grid_y = cfg.margin_top + 60
        
        svg = self._svg_header()
        svg += self._render_styles()
        
        # Background
        svg += f'  <rect width="{cfg.page_width}" height="{cfg.page_height}" fill="{cfg.background_color}"/>\n'
        
        # Title
        svg += f'  <text x="{cfg.page_width/2}" y="{cfg.margin_top}" class="title" text-anchor="middle">'
        svg += f'{data.title} - Solution</text>\n'
        
        # Grid with letters
        svg += self._render_grid(data, grid_x, grid_y, show_letters=True)
        
        # Page number
        svg += f'  <text x="{cfg.page_width/2}" y="{cfg.page_height - 30}" class="footer" text-anchor="middle">'
        svg += f'Page 3</text>\n'
        
        svg += '</svg>'
        return svg
    
    def render_combined_html(self, data: CrosswordData) -> str:
        """Render combined HTML document with all pages."""
        puzzle_svg = self.render_puzzle_page(data)
        clues_svg = self.render_clues_page(data)
        solution_svg = self.render_solution_page(data)
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data.title}</title>
    <style>
        @media print {{
            .page {{
                page-break-after: always;
            }}
            .page:last-child {{
                page-break-after: avoid;
            }}
        }}
        
        body {{
            margin: 0;
            padding: 0;
            font-family: {self.config.font_family};
        }}
        
        .page {{
            width: {self.config.page_width}px;
            height: {self.config.page_height}px;
            margin: 0 auto 20px auto;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        
        @media screen {{
            .page {{
                margin-bottom: 40px;
            }}
        }}
        
        svg {{
            display: block;
            width: 100%;
            height: auto;
        }}
        
        .print-button {{
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 20px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }}
        
        .print-button:hover {{
            background: #0056b3;
        }}
        
        @media print {{
            .print-button {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <button class="print-button" onclick="window.print()">🖨️ Print Puzzle</button>
    
    <div class="page" id="puzzle">
        {puzzle_svg}
    </div>
    
    <div class="page" id="clues">
        {clues_svg}
    </div>
    
    <div class="page" id="solution">
        {solution_svg}
    </div>
</body>
</html>'''
        return html
    
    def render_markdown(self, data: CrosswordData) -> str:
        """Render puzzle as Markdown."""
        md = []
        
        # Frontmatter
        md.append("---")
        md.append(f"title: \"{data.title}\"")
        md.append(f"author: \"{data.author}\"")
        md.append(f"date: \"{data.date}\"")
        md.append(f"theme: \"{data.theme or 'Themeless'}\"")
        md.append(f"difficulty: \"{data.difficulty}\"")
        md.append(f"size: {data.size}")
        md.append("---")
        md.append("")
        
        # Title
        md.append(f"# {data.title}")
        md.append("")
        md.append(f"**Author:** {data.author}  ")
        md.append(f"**Date:** {data.date}  ")
        md.append(f"**Difficulty:** {data.difficulty}")
        if data.theme:
            md.append(f"  \n**Theme:** {data.theme}")
        md.append("")
        
        # Grid (text representation)
        md.append("## Grid")
        md.append("")
        md.append("```")
        for row_idx, row in enumerate(data.grid):
            line = ""
            for col_idx, cell in enumerate(row):
                if cell == '#':
                    line += "██"
                elif cell == '.':
                    # Check for number
                    num = data.numbers.get((row_idx, col_idx))
                    if num:
                        line += f"{num:2d}" if num < 10 else f"{num}"
                    else:
                        line += "  "
                else:
                    line += f" {cell}"
            md.append(line)
        md.append("```")
        md.append("")
        
        # Clues
        md.append("## Clues")
        md.append("")
        md.append("### ACROSS")
        md.append("")
        for num, clue, length in data.across_clues:
            md.append(f"**{num}.** {clue} ({length})")
        md.append("")
        
        md.append("### DOWN")
        md.append("")
        for num, clue, length in data.down_clues:
            md.append(f"**{num}.** {clue} ({length})")
        md.append("")
        
        # Solution
        md.append("## Solution")
        md.append("")
        md.append("```")
        for row in data.grid:
            line = ""
            for cell in row:
                if cell == '#':
                    line += "█"
                else:
                    line += cell if cell != '.' else ' '
            md.append(line)
        md.append("```")
        
        return "\n".join(md)
    
    def _svg_header(self) -> str:
        """Generate SVG header."""
        cfg = self.config
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" 
     viewBox="0 0 {cfg.page_width} {cfg.page_height}"
     width="{cfg.page_width}" height="{cfg.page_height}">
'''
    
    def _render_styles(self) -> str:
        """Generate SVG styles."""
        cfg = self.config
        return f'''  <defs>
    <style>
      .title {{ 
        font-family: {cfg.font_family}; 
        font-size: {cfg.title_font_size}px; 
        font-weight: bold; 
        fill: {cfg.letter_color}; 
      }}
      .subtitle {{ 
        font-family: {cfg.font_family}; 
        font-size: {cfg.subtitle_font_size}px; 
        fill: {cfg.number_color}; 
      }}
      .cell {{ 
        stroke: {cfg.grid_color}; 
        stroke-width: {cfg.inner_border_width}; 
      }}
      .block {{ 
        fill: {cfg.block_color}; 
      }}
      .empty {{ 
        fill: {cfg.background_color}; 
      }}
      .number {{ 
        font-family: {cfg.font_family}; 
        font-size: {cfg.number_font_size}px; 
        fill: {cfg.number_color}; 
      }}
      .letter {{ 
        font-family: {cfg.font_family}; 
        font-size: {cfg.letter_font_size}px; 
        fill: {cfg.letter_color}; 
        text-anchor: middle;
        dominant-baseline: middle;
      }}
      .clue-header {{ 
        font-family: {cfg.font_family}; 
        font-size: {cfg.clue_font_size + 2}px; 
        font-weight: bold;
        fill: {cfg.letter_color}; 
      }}
      .clue-number {{ 
        font-family: {cfg.font_family}; 
        font-size: {cfg.clue_number_font_size}px; 
        font-weight: bold;
        fill: {cfg.letter_color}; 
      }}
      .clue-text {{ 
        font-family: {cfg.font_family}; 
        font-size: {cfg.clue_font_size}px; 
        fill: {cfg.letter_color}; 
      }}
      .footer {{
        font-family: {cfg.font_family};
        font-size: 10px;
        fill: {cfg.number_color};
      }}
    </style>
  </defs>
'''
    
    def _render_title(self, data: CrosswordData) -> str:
        """Render puzzle title and metadata."""
        cfg = self.config
        svg = ""
        
        # Main title
        svg += f'  <text x="{cfg.page_width/2}" y="{cfg.margin_top}" class="title" text-anchor="middle">'
        svg += f'{data.title}</text>\n'
        
        # Subtitle with author and date
        subtitle = f"By {data.author}"
        if data.difficulty:
            subtitle += f" • {data.difficulty}"
        if data.date:
            subtitle += f" • {data.date}"
        
        svg += f'  <text x="{cfg.page_width/2}" y="{cfg.margin_top + 25}" class="subtitle" text-anchor="middle">'
        svg += f'{subtitle}</text>\n'
        
        return svg
    
    def _render_grid(
        self, 
        data: CrosswordData, 
        x: float, 
        y: float, 
        show_letters: bool
    ) -> str:
        """Render the crossword grid."""
        cfg = self.config
        grid_size = data.size * cfg.cell_size
        svg = ""
        
        # Outer border
        svg += f'  <rect x="{x}" y="{y}" width="{grid_size}" height="{grid_size}" '
        svg += f'fill="none" stroke="{cfg.grid_color}" stroke-width="{cfg.border_width}"/>\n'
        
        # Cells
        for row_idx in range(data.size):
            for col_idx in range(data.size):
                cell_x = x + col_idx * cfg.cell_size
                cell_y = y + row_idx * cfg.cell_size
                
                cell = data.grid[row_idx][col_idx] if row_idx < len(data.grid) else '.'
                
                if cell == '#':
                    # Black square
                    svg += f'  <rect x="{cell_x}" y="{cell_y}" '
                    svg += f'width="{cfg.cell_size}" height="{cfg.cell_size}" '
                    svg += f'class="cell block"/>\n'
                else:
                    # White square
                    svg += f'  <rect x="{cell_x}" y="{cell_y}" '
                    svg += f'width="{cfg.cell_size}" height="{cfg.cell_size}" '
                    svg += f'class="cell empty"/>\n'
                    
                    # Clue number
                    if (row_idx, col_idx) in data.numbers:
                        num = data.numbers[(row_idx, col_idx)]
                        svg += f'  <text x="{cell_x + 3}" y="{cell_y + 10}" class="number">{num}</text>\n'
                    
                    # Letter (for solution)
                    if show_letters and cell not in ('.', '#'):
                        letter_x = cell_x + cfg.cell_size / 2
                        letter_y = cell_y + cfg.cell_size / 2 + 4  # Slight offset for visual centering
                        svg += f'  <text x="{letter_x}" y="{letter_y}" class="letter">{cell}</text>\n'
        
        return svg
    
    def _render_clue_column(
        self,
        clues: List[Tuple[int, str, int]],
        header: str,
        x: float,
        y: float,
        width: float
    ) -> str:
        """Render a column of clues."""
        cfg = self.config
        svg = ""
        
        # Header
        svg += f'  <text x="{x}" y="{y}" class="clue-header">{header}</text>\n'
        
        current_y = y + cfg.clue_line_height + 5
        
        for num, clue, length in clues:
            # Check if we need to wrap
            # Simple word wrap based on character count
            max_chars = int(width / (cfg.clue_font_size * 0.5))
            
            clue_with_length = f"{clue} ({length})"
            
            if len(clue_with_length) > max_chars:
                # Wrap the clue
                words = clue_with_length.split()
                lines = []
                current_line = f"{num}. "
                
                for word in words:
                    test_line = current_line + word + " "
                    if len(test_line) > max_chars and current_line != f"{num}. ":
                        lines.append(current_line.strip())
                        current_line = "    " + word + " "  # Indent continuation
                    else:
                        current_line = test_line
                
                if current_line.strip():
                    lines.append(current_line.strip())
                
                for i, line in enumerate(lines):
                    if i == 0:
                        # First line with number
                        svg += f'  <text x="{x}" y="{current_y}" class="clue-text">'
                        svg += f'<tspan class="clue-number">{num}.</tspan> {line[len(str(num))+2:]}</text>\n'
                    else:
                        svg += f'  <text x="{x + 15}" y="{current_y}" class="clue-text">{line}</text>\n'
                    current_y += cfg.clue_line_height
            else:
                svg += f'  <text x="{x}" y="{current_y}" class="clue-text">'
                svg += f'<tspan class="clue-number">{num}.</tspan> {clue_with_length}</text>\n'
                current_y += cfg.clue_line_height
            
            # Check page overflow
            if current_y > cfg.page_height - cfg.margin_bottom:
                break
        
        return svg


def create_sample_crossword() -> CrosswordData:
    """Create a sample crossword for testing."""
    # 5x5 sample grid
    grid = [
        ['S', 'T', 'A', 'R', 'S'],
        ['P', '#', 'R', '#', 'U'],
        ['A', 'L', 'E', 'R', 'N'],
        ['C', '#', 'A', '#', '#'],
        ['E', 'A', 'S', 'T', '#'],
    ]
    
    numbers = {
        (0, 0): 1,
        (0, 2): 2,
        (0, 4): 3,
        (2, 0): 4,
        (2, 1): 5,
        (2, 3): 6,
        (4, 0): 7,
        (4, 1): 8,
    }
    
    across_clues = [
        (1, "Celestial bodies", 5),
        (4, "Notify", 5),
        (7, "Direction of sunrise", 4),
    ]
    
    down_clues = [
        (1, "Outer ___", 5),
        (2, "Region", 4),
        (3, "Celestial body", 3),
        (5, "Zodiac lion", 3),
        (6, "Sprint", 3),
    ]
    
    return CrosswordData(
        title="Space Theme Mini",
        author="AI Generator",
        size=5,
        grid=grid,
        numbers=numbers,
        across_clues=across_clues,
        down_clues=down_clues,
        theme="Space",
        difficulty="Easy"
    )


if __name__ == "__main__":
    # Test the renderer
    data = create_sample_crossword()
    renderer = CrosswordPageRenderer()
    
    files = renderer.render_all_pages(data, output_dir="/tmp/crossword_test")
    
    print("Generated files:")
    for name, path in files.items():
        print(f"  {name}: {path}")
