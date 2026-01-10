#!/usr/bin/env python3
"""
AI-Powered Crossword Generator

Generates NYT-style crossword puzzles using:
1. AI (Claude API) for themed word lists and clues
2. CSP solver with AC-3 for grid filling
3. Multi-page SVG/HTML output

Usage:
    python main.py --topic "Classic Movies" --size 15 --output ./puzzles
    python main.py --topic "Space Exploration" --difficulty wednesday
"""

import os
import sys
import argparse
import json
import random
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Grid, WordSlot, Direction, ThemedWord, CellType
from csp_solver import CrosswordCSP, create_sample_word_list
from page_renderer import CrosswordPageRenderer, CrosswordData, PageConfig


@dataclass
class GeneratorConfig:
    """Configuration for the crossword generator."""
    size: int = 15
    max_words: int = 78
    min_word_length: int = 3
    max_black_ratio: float = 0.16
    difficulty: str = "medium"
    use_ai: bool = False
    api_key: Optional[str] = None


class CrosswordGenerator:
    """
    Main crossword puzzle generator.
    
    Workflow:
    1. Generate or load word list (optionally using AI)
    2. Create grid with black square pattern
    3. Use CSP solver to fill grid
    4. Generate clues (optionally using AI)
    5. Render to multi-page SVG/HTML
    """
    
    def __init__(self, config: GeneratorConfig):
        self.config = config
        self.word_list: List[str] = []
        self.themed_words: Dict[str, ThemedWord] = {}
        self.grid: Optional[Grid] = None
        self.solution: Optional[Dict[WordSlot, str]] = None
    
    def generate(
        self,
        topic: str,
        author: str = "AI Generator",
        output_dir: str = ".",
        base_name: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate a complete crossword puzzle.
        
        Returns dict of output file paths.
        """
        print(f"🎯 Generating crossword puzzle on topic: {topic}")
        print(f"   Size: {self.config.size}x{self.config.size}")
        print(f"   Difficulty: {self.config.difficulty}")
        print()
        
        # Step 1: Generate word list
        print("📝 Step 1: Building word list...")
        self._build_word_list(topic)
        print(f"   Loaded {len(self.word_list)} words")
        print()
        
        # Step 2: Create grid pattern
        print("🔲 Step 2: Creating grid pattern...")
        self._create_grid()
        validation = self.grid.validate()
        print(f"   Grid created with {validation['stats']['word_count']} word slots")
        print(f"   Black squares: {validation['stats']['block_count']} ({validation['stats']['block_ratio']:.1%})")
        print()
        
        # Step 3: Solve using CSP
        print("🧩 Step 3: Filling grid with CSP solver...")
        success = self._solve_grid()
        if not success:
            print("   ❌ Failed to find solution. Try different parameters.")
            return {}
        print(f"   ✅ Solution found!")
        print()
        
        # Step 4: Generate clues
        print("📖 Step 4: Generating clues...")
        clue_data = self._generate_clues()
        print(f"   Generated {len(clue_data['across'])} across and {len(clue_data['down'])} down clues")
        print()
        
        # Step 5: Render output
        print("🖼️  Step 5: Rendering output files...")
        
        if base_name is None:
            base_name = topic.lower().replace(" ", "_")[:20]
        
        crossword_data = self._create_crossword_data(topic, author, clue_data)
        
        renderer = CrosswordPageRenderer()
        files = renderer.render_all_pages(crossword_data, output_dir, base_name)
        
        print(f"   Generated {len(files)} files:")
        for name, path in files.items():
            print(f"     - {name}: {path}")
        print()
        
        print("✨ Done!")
        return files
    
    def _build_word_list(self, topic: str):
        """Build word list, optionally using AI."""
        # Start with base word list
        self.word_list = create_sample_word_list()
        
        # Add topic-specific words (simulated - would use AI in production)
        topic_words = self._get_topic_words(topic)
        for tw in topic_words:
            self.word_list.append(tw.word)
            self.themed_words[tw.word] = tw
        
        # Remove duplicates and sort by length (longest first for theme entries)
        self.word_list = list(set(w.upper() for w in self.word_list))
        self.word_list.sort(key=len, reverse=True)
    
    def _get_topic_words(self, topic: str) -> List[ThemedWord]:
        """
        Get topic-specific words.
        In production, this would call the AI API.
        """
        # Simulated topic words for demo
        topic_banks = {
            "space": [
                ThemedWord("ASTRONAUT", "Space traveler"),
                ThemedWord("ROCKET", "Launches into space"),
                ThemedWord("ORBIT", "Path around a planet"),
                ThemedWord("LUNAR", "Of the moon"),
                ThemedWord("COSMOS", "The universe"),
                ThemedWord("NEBULA", "Interstellar cloud"),
                ThemedWord("COMET", "Icy space traveler with a tail"),
                ThemedWord("METEOR", "Shooting star"),
                ThemedWord("SATURN", "Ringed planet"),
                ThemedWord("MARS", "The Red Planet"),
                ThemedWord("VENUS", "Second planet from the sun"),
                ThemedWord("ALIEN", "Extraterrestrial being"),
                ThemedWord("GALAXY", "Star system like the Milky Way"),
                ThemedWord("SOLAR", "Of the sun"),
                ThemedWord("ECLIPSE", "Sun or moon obscured"),
            ],
            "movies": [
                ThemedWord("CINEMA", "Movie theater"),
                ThemedWord("ACTOR", "Film performer"),
                ThemedWord("DIRECTOR", "Film's creative lead"),
                ThemedWord("SCRIPT", "Movie dialogue text"),
                ThemedWord("SCENE", "Part of a movie"),
                ThemedWord("CAMERA", "Filming device"),
                ThemedWord("ACTION", "What a director yells"),
                ThemedWord("DRAMA", "Serious film genre"),
                ThemedWord("COMEDY", "Funny film genre"),
                ThemedWord("OSCAR", "Academy Award"),
                ThemedWord("SEQUEL", "Follow-up film"),
                ThemedWord("PREMIERE", "First showing"),
                ThemedWord("CREDITS", "Names at the end"),
                ThemedWord("TRAILER", "Movie preview"),
                ThemedWord("STUDIO", "Where films are made"),
            ],
            "food": [
                ThemedWord("CUISINE", "Style of cooking"),
                ThemedWord("RECIPE", "Cooking instructions"),
                ThemedWord("CHEF", "Professional cook"),
                ThemedWord("SPICE", "Flavor enhancer"),
                ThemedWord("SAUTE", "Cook quickly in pan"),
                ThemedWord("PASTA", "Italian noodles"),
                ThemedWord("SAUCE", "Liquid condiment"),
                ThemedWord("BRAISE", "Slow cooking method"),
                ThemedWord("GRILL", "Cook over flames"),
                ThemedWord("APPETIZER", "Starter course"),
                ThemedWord("ENTREE", "Main course"),
                ThemedWord("DESSERT", "Sweet final course"),
                ThemedWord("MENU", "Restaurant offerings"),
                ThemedWord("GARNISH", "Decorative food topping"),
                ThemedWord("UMAMI", "Fifth taste sensation"),
            ],
            "default": [
                ThemedWord("PUZZLE", "Brain teaser"),
                ThemedWord("CLUE", "Hint to solve"),
                ThemedWord("ANSWER", "Solution to clue"),
                ThemedWord("GRID", "Crossword pattern"),
                ThemedWord("ACROSS", "Horizontal direction"),
                ThemedWord("DOWN", "Vertical direction"),
            ]
        }
        
        # Find matching topic or use default
        topic_lower = topic.lower()
        for key, words in topic_banks.items():
            if key in topic_lower or topic_lower in key:
                return words
        
        return topic_banks["default"]
    
    def _create_grid(self):
        """Create a grid with a valid black square pattern."""
        self.grid = Grid(size=self.config.size)
        
        # Use a standard crossword pattern
        # This is a simplified pattern generator
        # A real implementation would have more sophisticated pattern generation
        
        if self.config.size == 15:
            # Standard 15x15 pattern (similar to NYT)
            self._apply_standard_15x15_pattern()
        elif self.config.size == 5:
            # Mini crossword pattern
            self._apply_mini_pattern()
        else:
            # Generate a symmetric pattern
            self._generate_symmetric_pattern()
        
        # Find all word slots
        self.grid.find_word_slots()
    
    def _apply_standard_15x15_pattern(self):
        """Apply a standard 15x15 crossword pattern."""
        # This is a simplified pattern - real patterns are more complex
        blocks = [
            # Row 0
            (0, 4), (0, 10),
            # Row 1  
            (1, 4), (1, 10),
            # Row 2
            (2, 4), (2, 10),
            # Row 3
            (3, 0), (3, 1), (3, 7), (3, 13), (3, 14),
            # Row 4
            (4, 6), (4, 8),
            # Row 5
            (5, 3), (5, 11),
            # Row 6
            (6, 3), (6, 7), (6, 11),
            # Row 7
            (7, 0), (7, 1), (7, 2), (7, 12), (7, 13), (7, 14),
        ]
        
        for row, col in blocks:
            self.grid.set_block(row, col)  # Also sets symmetric block
    
    def _apply_mini_pattern(self):
        """Apply a 5x5 mini crossword pattern."""
        blocks = [
            (1, 1), (1, 3),
            (3, 1), (3, 3),
        ]
        for row, col in blocks:
            self.grid.set_block(row, col)
    
    def _generate_symmetric_pattern(self):
        """Generate a random symmetric pattern."""
        size = self.config.size
        target_blocks = int(size * size * self.config.max_black_ratio * 0.8)
        placed = 0
        
        attempts = 0
        while placed < target_blocks // 2 and attempts < 1000:
            row = random.randint(0, size // 2)
            col = random.randint(0, size - 1)
            
            # Don't place in corners or create isolated areas
            if (row, col) not in [(0, 0), (0, size-1)]:
                self.grid.set_block(row, col)
                placed += 1
            
            attempts += 1
    
    def _solve_grid(self) -> bool:
        """Use CSP solver to fill the grid."""
        # Create word request function for dynamic word generation
        def request_words(pattern: str, count: int) -> List[str]:
            """Request words matching a pattern."""
            # In production, this would call AI API
            # For now, search the word list
            from models import matches_pattern
            matches = [
                w for w in self.word_list 
                if matches_pattern(w, pattern)
            ]
            return matches[:count]
        
        # Create and run CSP solver
        csp = CrosswordCSP(
            self.grid, 
            self.word_list,
            word_generator=request_words
        )
        
        self.solution = csp.solve(use_inference=True)
        
        if self.solution:
            # Apply solution to grid
            csp.apply_solution(self.solution)
            
            # Print stats
            print(f"   Backtracks: {csp.stats['backtracks']}")
            print(f"   AC-3 revisions: {csp.stats['ac3_revisions']}")
            if csp.stats['words_requested'] > 0:
                print(f"   Dynamic word requests: {csp.stats['words_requested']}")
            
            return True
        
        return False
    
    def _generate_clues(self) -> Dict[str, List[Tuple[int, str, int]]]:
        """Generate clues for all words."""
        across_clues = []
        down_clues = []
        
        for slot, word in self.solution.items():
            # Check if we have a themed clue
            if word in self.themed_words:
                clue = self.themed_words[word].clue
            else:
                # Generate a simple clue (AI would generate better ones)
                clue = self._generate_simple_clue(word)
            
            if slot.direction == Direction.ACROSS:
                across_clues.append((slot.number, clue, len(word)))
            else:
                down_clues.append((slot.number, clue, len(word)))
        
        # Sort by clue number
        across_clues.sort(key=lambda x: x[0])
        down_clues.sort(key=lambda x: x[0])
        
        return {"across": across_clues, "down": down_clues}
    
    def _generate_simple_clue(self, word: str) -> str:
        """Generate a simple clue for a word."""
        # Very basic clue generation - AI would do much better
        simple_clues = {
            "THE": "Definite article",
            "AND": "Plus",
            "FOR": "In favor of",
            "ARE": "Exist",
            "BUT": "However",
            "NOT": "Negative",
            "YOU": "Second person pronoun",
            "ALL": "Everything",
            "CAN": "Is able to",
            "HER": "Belonging to she",
            "WAS": "Past tense of 'is'",
            "ONE": "Single unit",
            "OUR": "Belonging to us",
            "OUT": "Not in",
            "DAY": "24 hours",
            "HAD": "Possessed",
            "HOT": "High temperature",
            "OLD": "Not new",
            "SEE": "Observe",
            "NOW": "At this moment",
            "WAY": "Path",
            "MAY": "Might",
            "SAY": "Speak",
            "SHE": "Female pronoun",
            "TWO": "Pair",
            "HOW": "In what manner",
            "ITS": "Belonging to it",
            "LET": "Allow",
            "PUT": "Place",
            "TOO": "Also",
            "GOT": "Obtained",
        }
        
        if word in simple_clues:
            return simple_clues[word]
        
        return f"Word meaning (clue needed for {word})"
    
    def _create_crossword_data(
        self, 
        topic: str, 
        author: str,
        clue_data: Dict
    ) -> CrosswordData:
        """Create CrosswordData for rendering."""
        # Build grid representation
        grid_chars = []
        for row in range(self.config.size):
            row_chars = []
            for col in range(self.config.size):
                cell = self.grid.get_cell(row, col)
                if cell.is_block():
                    row_chars.append('#')
                elif cell.letter:
                    row_chars.append(cell.letter)
                else:
                    row_chars.append('.')
            grid_chars.append(row_chars)
        
        # Build numbers dict
        numbers = {}
        for row in range(self.config.size):
            for col in range(self.config.size):
                cell = self.grid.get_cell(row, col)
                if cell.number:
                    numbers[(row, col)] = cell.number
        
        return CrosswordData(
            title=f"{topic.title()} Crossword",
            author=author,
            size=self.config.size,
            grid=grid_chars,
            numbers=numbers,
            across_clues=clue_data["across"],
            down_clues=clue_data["down"],
            theme=topic,
            difficulty=self.config.difficulty.title()
        )


def main():
    parser = argparse.ArgumentParser(
        description="Generate AI-powered crossword puzzles"
    )
    parser.add_argument(
        "--topic", "-t",
        default="General Knowledge",
        help="Theme topic for the puzzle"
    )
    parser.add_argument(
        "--size", "-s",
        type=int,
        default=15,
        choices=[5, 7, 9, 11, 13, 15, 17, 19, 21],
        help="Grid size (default: 15)"
    )
    parser.add_argument(
        "--difficulty", "-d",
        default="medium",
        choices=["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"],
        help="Difficulty level"
    )
    parser.add_argument(
        "--output", "-o",
        default="./output",
        help="Output directory"
    )
    parser.add_argument(
        "--author", "-a",
        default="AI Generator",
        help="Author name"
    )
    
    args = parser.parse_args()
    
    config = GeneratorConfig(
        size=args.size,
        difficulty=args.difficulty
    )
    
    generator = CrosswordGenerator(config)
    files = generator.generate(
        topic=args.topic,
        author=args.author,
        output_dir=args.output
    )
    
    if files:
        print("\n📁 Output files:")
        for name, path in files.items():
            print(f"   {name}: {path}")


if __name__ == "__main__":
    main()
