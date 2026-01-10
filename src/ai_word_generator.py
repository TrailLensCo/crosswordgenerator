"""
AI Word Generator using Claude API

Provides dynamic word generation for crossword puzzles:
- Generate themed word lists with clues
- Request words matching specific letter patterns
- Generate clues for solved words

Uses the Anthropic Claude API.
"""

import os
import json
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import time

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    print("Warning: anthropic package not installed. Run: pip install anthropic")


@dataclass
class WordWithClue:
    """A word with its clue."""
    word: str
    clue: str
    
    def __post_init__(self):
        self.word = self.word.upper().replace(" ", "").replace("-", "")


class AIWordGenerator:
    """
    Generates crossword words and clues using Claude API.
    
    Features:
    - Generate themed word lists
    - Request words matching specific patterns (e.g., "A__LE" -> "APPLE")
    - Generate clues for words
    - Caching to reduce API calls
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize the AI word generator.
        
        Args:
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
            model: Claude model to use
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model
        
        if HAS_ANTHROPIC and self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None
        
        # Cache for words and clues
        self._word_cache: Dict[str, List[str]] = {}  # pattern -> words
        self._clue_cache: Dict[str, str] = {}  # word -> clue
        self._theme_cache: Dict[str, List[WordWithClue]] = {}  # theme -> words
        
        # Stats
        self.stats = {
            "api_calls": 0,
            "cache_hits": 0,
            "words_generated": 0
        }
    
    def is_available(self) -> bool:
        """Check if AI generation is available."""
        return self.client is not None
    
    def generate_themed_words(
        self, 
        theme: str, 
        count: int = 30,
        min_length: int = 3,
        max_length: int = 15
    ) -> List[WordWithClue]:
        """
        Generate themed words with clues.
        
        Args:
            theme: Topic/theme for words (e.g., "Space Exploration")
            count: Number of words to generate
            min_length: Minimum word length
            max_length: Maximum word length
            
        Returns:
            List of WordWithClue objects
        """
        cache_key = f"{theme}:{count}:{min_length}:{max_length}"
        if cache_key in self._theme_cache:
            self.stats["cache_hits"] += 1
            return self._theme_cache[cache_key]
        
        if not self.client:
            return self._fallback_themed_words(theme)
        
        prompt = f"""Generate {count} crossword-worthy words related to the theme: "{theme}"

Requirements:
- Word lengths between {min_length} and {max_length} letters
- Mix of lengths (some short fill words 3-5 letters, some longer theme entries 7-15 letters)
- Real, common English words or well-known proper nouns
- No spaces, hyphens, or special characters
- Provide an engaging, concise crossword clue for each

Respond with ONLY a JSON array, no other text:
[
  {{"word": "APOLLO", "clue": "NASA Moon program"}},
  {{"word": "MARS", "clue": "Red planet"}},
  ...
]"""

        try:
            self.stats["api_calls"] += 1
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )
            
            text = response.content[0].text
            
            # Parse JSON
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                words = []
                for item in data:
                    word = item.get("word", "").upper().replace(" ", "")
                    clue = item.get("clue", "")
                    if min_length <= len(word) <= max_length and word.isalpha():
                        words.append(WordWithClue(word=word, clue=clue))
                        self._clue_cache[word] = clue
                
                self.stats["words_generated"] += len(words)
                self._theme_cache[cache_key] = words
                return words
                
        except Exception as e:
            print(f"AI word generation error: {e}")
        
        return self._fallback_themed_words(theme)
    
    def get_words_matching_pattern(
        self, 
        pattern: str, 
        count: int = 10,
        theme: Optional[str] = None
    ) -> List[str]:
        """
        Get words matching a letter pattern.
        
        Args:
            pattern: Pattern with dots for unknown letters (e.g., "A..LE" for 5-letter word starting with A, ending with LE)
            count: Maximum number of words to return
            theme: Optional theme to prefer themed words
            
        Returns:
            List of matching words
        """
        pattern = pattern.upper()
        
        # Check cache
        cache_key = f"{pattern}:{theme or ''}"
        if cache_key in self._word_cache:
            self.stats["cache_hits"] += 1
            return self._word_cache[cache_key][:count]
        
        if not self.client:
            return []
        
        # Build prompt
        length = len(pattern)
        known_letters = [(i, c) for i, c in enumerate(pattern) if c != '.']
        
        constraint_desc = f"{length}-letter word"
        if known_letters:
            constraints = [f"letter {i+1} is '{c}'" for i, c in known_letters]
            constraint_desc += " where " + ", ".join(constraints)
        
        theme_hint = f' related to "{theme}"' if theme else ""
        
        prompt = f"""List {count} common English words that are {constraint_desc}{theme_hint}.

Pattern: {pattern} (dots are unknown letters)

Requirements:
- Real, common words (no obscure words)
- Exactly {length} letters
- Must match the pattern exactly

Respond with ONLY the words, one per line, no numbering or explanation:"""

        try:
            self.stats["api_calls"] += 1
            response = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}]
            )
            
            text = response.content[0].text
            words = []
            
            for line in text.strip().split('\n'):
                word = line.strip().upper()
                word = re.sub(r'[^A-Z]', '', word)  # Remove non-letters
                
                if len(word) == length and self._matches_pattern(word, pattern):
                    words.append(word)
            
            self.stats["words_generated"] += len(words)
            self._word_cache[cache_key] = words
            return words[:count]
            
        except Exception as e:
            print(f"AI pattern matching error: {e}")
            return []
    
    def generate_clue(self, word: str, difficulty: str = "medium") -> str:
        """
        Generate a clue for a word.
        
        Args:
            word: The word to clue
            difficulty: easy, medium, or hard
            
        Returns:
            Clue string
        """
        word = word.upper()
        
        # Check cache
        if word in self._clue_cache:
            self.stats["cache_hits"] += 1
            return self._clue_cache[word]
        
        if not self.client:
            return f"Clue for {word}"
        
        difficulty_guidance = {
            "easy": "straightforward definition",
            "medium": "slightly clever or requiring some thought",
            "hard": "cryptic, punny, or requiring wordplay knowledge"
        }
        
        prompt = f"""Write a {difficulty_guidance.get(difficulty, 'medium')} crossword clue for the word: {word}

Requirements:
- Concise (under 50 characters ideally)
- No direct use of the word or obvious derivatives
- Suitable for a newspaper crossword

Respond with ONLY the clue, nothing else:"""

        try:
            self.stats["api_calls"] += 1
            response = self.client.messages.create(
                model=self.model,
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}]
            )
            
            clue = response.content[0].text.strip()
            clue = clue.strip('"\'')  # Remove quotes if present
            
            self._clue_cache[word] = clue
            return clue
            
        except Exception as e:
            print(f"AI clue generation error: {e}")
            return f"Clue for {word}"
    
    def generate_clues_batch(self, words: List[str], difficulty: str = "medium") -> Dict[str, str]:
        """
        Generate clues for multiple words in one API call.
        
        Args:
            words: List of words to clue
            difficulty: Difficulty level
            
        Returns:
            Dict mapping words to clues
        """
        # Check which words need clues
        needed = [w.upper() for w in words if w.upper() not in self._clue_cache]
        
        if not needed:
            return {w.upper(): self._clue_cache[w.upper()] for w in words}
        
        if not self.client:
            return {w.upper(): f"Clue for {w.upper()}" for w in words}
        
        word_list = ", ".join(needed)
        
        prompt = f"""Write {difficulty} crossword clues for these words: {word_list}

Requirements:
- Concise clues (under 50 characters each)
- No direct use of the word
- Suitable for newspaper crossword

Respond with ONLY JSON, no other text:
{{"WORD1": "clue1", "WORD2": "clue2", ...}}"""

        try:
            self.stats["api_calls"] += 1
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            
            text = response.content[0].text
            
            # Parse JSON
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                clues = json.loads(json_match.group())
                for word, clue in clues.items():
                    self._clue_cache[word.upper()] = clue
            
        except Exception as e:
            print(f"AI batch clue error: {e}")
        
        # Return all clues (cached + new)
        result = {}
        for w in words:
            w_upper = w.upper()
            result[w_upper] = self._clue_cache.get(w_upper, f"Clue for {w_upper}")
        
        return result
    
    def _matches_pattern(self, word: str, pattern: str) -> bool:
        """Check if word matches pattern."""
        if len(word) != len(pattern):
            return False
        for w, p in zip(word, pattern):
            if p != '.' and w != p:
                return False
        return True
    
    def _fallback_themed_words(self, theme: str) -> List[WordWithClue]:
        """Fallback words when AI is unavailable."""
        # Generic crossword words
        fallback = [
            WordWithClue("AREA", "Region"),
            WordWithClue("IDEA", "Notion"),
            WordWithClue("STAR", "Celestial body"),
            WordWithClue("OPEN", "Not closed"),
            WordWithClue("TIME", "What clocks tell"),
            WordWithClue("NAME", "What you're called"),
            WordWithClue("EAST", "Sunrise direction"),
            WordWithClue("WEST", "Sunset direction"),
            WordWithClue("NORTH", "Arctic direction"),
            WordWithClue("SOUTH", "Antarctic direction"),
        ]
        return fallback
    
    def get_stats(self) -> Dict:
        """Get usage statistics."""
        return self.stats.copy()


def create_pattern_word_generator(ai_generator: AIWordGenerator, theme: Optional[str] = None):
    """
    Create a word generator function for use with CSP solver.
    
    Args:
        ai_generator: AIWordGenerator instance
        theme: Optional theme for word generation
        
    Returns:
        Function that takes (pattern, count) and returns list of words
    """
    def generator(pattern: str, count: int = 10) -> List[str]:
        return ai_generator.get_words_matching_pattern(pattern, count, theme)
    
    return generator


# Test the generator
if __name__ == "__main__":
    print("=" * 60)
    print("AI WORD GENERATOR TEST")
    print("=" * 60)
    
    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("\n⚠️  No ANTHROPIC_API_KEY found in environment.")
        print("   Set it with: export ANTHROPIC_API_KEY='your-key-here'")
        print("   Testing with fallback mode...\n")
    
    generator = AIWordGenerator(api_key=api_key)
    
    print(f"AI Available: {generator.is_available()}")
    
    if generator.is_available():
        # Test themed words
        print("\n📝 Testing themed word generation...")
        words = generator.generate_themed_words("Space Exploration", count=10)
        print(f"   Generated {len(words)} words:")
        for w in words[:5]:
            print(f"     {w.word}: {w.clue}")
        
        # Test pattern matching
        print("\n🔍 Testing pattern matching...")
        pattern = "S...E"
        matches = generator.get_words_matching_pattern(pattern, count=5)
        print(f"   Pattern '{pattern}' matches: {matches}")
        
        # Test clue generation
        print("\n💡 Testing clue generation...")
        clue = generator.generate_clue("ROCKET")
        print(f"   ROCKET: {clue}")
        
        # Stats
        print(f"\n📊 Stats: {generator.get_stats()}")
    else:
        print("\n   Using fallback mode (no API)")
        words = generator.generate_themed_words("Test")
        print(f"   Fallback words: {[w.word for w in words[:5]]}")
