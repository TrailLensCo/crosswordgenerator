# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.
# Unauthorized copying, distribution, or use of this file,
# via any medium, is strictly prohibited without the express
# written permission of TrailLensCo.

"""
AI Word Generator using Claude API.

Provides dynamic word generation for crossword puzzles:
- Generate themed word lists with clues
- Request words matching specific letter patterns
- Generate clues for solved words

Uses the Anthropic Claude API with callback limiting and prompt templates.
"""

import logging
import os
import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Callable
from dataclasses import dataclass

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    anthropic = None

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None

from ai_limiter import AICallbackLimiter


@dataclass
class WordWithClue:
    """A word with its clue."""
    word: str
    clue: str
    category: str = "fill"
    difficulty_score: int = 2

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
    - Callback limiting to prevent runaway token usage
    - External prompt templates
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        limiter: Optional[AICallbackLimiter] = None,
        prompt_loader: Optional[object] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the AI word generator.

        Args:
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
            model: Claude model to use
            limiter: Optional AICallbackLimiter for tracking limits
            prompt_loader: Optional PromptLoader for external prompts
            logger: Logger instance (uses module logger if not provided)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model
        self.limiter = limiter or AICallbackLimiter()
        self.prompt_loader = prompt_loader
        self.logger = logger if logger else logging.getLogger(__name__)

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
            "words_generated": 0,
            "tokens_used": 0,
        }

    def is_available(self) -> bool:
        """Check if AI generation is available."""
        return self.client is not None

    def _make_request(
        self,
        prompt_type: str,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        model: Optional[str] = None
    ) -> Optional[str]:
        """
        Make an API request with rate limiting.

        Args:
            prompt_type: Type of prompt for tracking
            system_prompt: System message
            user_prompt: User message
            max_tokens: Max tokens in response
            temperature: Sampling temperature
            model: Optional model override

        Returns:
            Response text or None if limited/failed
        """
        if not self.client:
            return None

        # Check limit before calling
        if not self.limiter.can_call(prompt_type):
            self.logger.warning(f"   AI limit reached for {prompt_type}")
            return None

        try:
            self.stats["api_calls"] += 1

            response = self.client.messages.create(
                model=model or self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )

            text = response.content[0].text

            # Record the call
            tokens = response.usage.input_tokens + response.usage.output_tokens
            self.stats["tokens_used"] += tokens
            self.limiter.record_call(
                prompt_type,
                tokens_used=tokens,
                success=True
            )

            return text

        except Exception as e:
            self.logger.error(f"AI request error: {e}", exc_info=True)
            self.limiter.record_call(prompt_type, success=False)
            return None

    def generate_themed_words(
        self,
        theme: str,
        count: int = 30,
        min_length: int = 3,
        max_length: int = 15,
        difficulty: str = "wednesday",
        puzzle_type: str = "revealer",
        topic_aspects: Optional[List[str]] = None
    ) -> List[WordWithClue]:
        """
        Generate themed words with clues.

        Args:
            theme: Topic/theme for words (e.g., "Space Exploration")
            count: Number of words to generate
            min_length: Minimum word length
            max_length: Maximum word length
            difficulty: Puzzle difficulty level
            puzzle_type: Type of puzzle
            topic_aspects: Optional list of aspects to focus on

        Returns:
            List of WordWithClue objects
        """
        cache_key = f"{theme}:{count}:{min_length}:{max_length}"
        if cache_key in self._theme_cache:
            self.stats["cache_hits"] += 1
            return self._theme_cache[cache_key]

        if not self.client:
            return self._fallback_themed_words(theme)

        # Build prompts
        if self.prompt_loader:
            try:
                template = self.prompt_loader.get('themed_word_list')
                system_prompt, user_prompt = template.render(
                    topic=theme,
                    difficulty=difficulty,
                    puzzle_type=puzzle_type,
                    size=max_length,
                    target_word_count=count,
                    max_word_length=max_length,
                    topic_aspects=topic_aspects or [
                        f"General knowledge about {theme}"
                    ],
                )
            except Exception:
                # Fall back to inline prompts
                system_prompt, user_prompt = self._build_themed_prompts(
                    theme, count, min_length, max_length, difficulty
                )
        else:
            system_prompt, user_prompt = self._build_themed_prompts(
                theme, count, min_length, max_length, difficulty
            )

        response = self._make_request(
            'themed_word_list',
            system_prompt,
            user_prompt,
            max_tokens=4096,
            temperature=0.7
        )

        if not response:
            return self._fallback_themed_words(theme)

        # Parse response
        words = self._parse_word_list_response(response, min_length, max_length)

        if words:
            self.stats["words_generated"] += len(words)
            self._theme_cache[cache_key] = words
            for w in words:
                self._clue_cache[w.word] = w.clue

        return words if words else self._fallback_themed_words(theme)

    def _build_themed_prompts(
        self,
        theme: str,
        count: int,
        min_length: int,
        max_length: int,
        difficulty: str
    ) -> Tuple[str, str]:
        """Build themed word list prompts."""
        system_prompt = f"""You are an expert crossword puzzle constructor with deep knowledge of
{theme} and crossword conventions. Generate words that are:
- Factually accurate and culturally respectful
- Appropriate for crossword puzzles (no obscure abbreviations)
- Varied in length to fit different grid positions
- Interesting and educational for solvers"""

        user_prompt = f"""Generate {count} crossword-worthy words related to the theme: "{theme}"

Requirements:
- Word lengths between {min_length} and {max_length} letters
- CRITICAL Distribution: MOST (60-65%) should be SHORT (3-7 letters),
  SOME (25-30%) should be MEDIUM (8-12 letters), FEW (10%) should be LONG (up to {max_length} letters)
- Real, common English words or well-known proper nouns
- No spaces, hyphens, or special characters
- Provide an engaging, concise crossword clue for each

Difficulty: {difficulty}

Respond with ONLY a JSON array, no other text:
[
  {{"word": "APOLLO", "clue": "NASA Moon program", "category": "theme_entry", "difficulty": 3}},
  {{"word": "MARS", "clue": "Red planet", "category": "fill", "difficulty": 2}},
  ...
]"""

        return system_prompt, user_prompt

    def _parse_word_list_response(
        self,
        text: str,
        min_length: int,
        max_length: int
    ) -> List[WordWithClue]:
        """Parse JSON response from themed word generation."""
        words = []

        # Try JSON parsing first
        json_match = re.search(r'\[.*\]', text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                for item in data:
                    word = item.get("word", "").upper().replace(" ", "")
                    clue = item.get("clue", "")
                    category = item.get("category", "fill")
                    difficulty = item.get("difficulty", 2)

                    if min_length <= len(word) <= max_length and word.isalpha():
                        words.append(WordWithClue(
                            word=word,
                            clue=clue,
                            category=category,
                            difficulty_score=difficulty
                        ))
                return words
            except json.JSONDecodeError:
                pass

        # Try YAML parsing as fallback
        if HAS_YAML:
            try:
                data = yaml.safe_load(text)
                if isinstance(data, dict) and 'words' in data:
                    for item in data['words']:
                        word = item.get("word", "").upper().replace(" ", "")
                        clue = item.get("clue", "")
                        if min_length <= len(word) <= max_length and word.isalpha():
                            words.append(WordWithClue(word=word, clue=clue))
                    return words
            except yaml.YAMLError:
                pass

        return words

    def get_words_matching_pattern(
        self,
        pattern: str,
        count: int = 10,
        theme: Optional[str] = None,
        used_words: Optional[set] = None
    ) -> List[str]:
        """
        Get words matching a letter pattern.

        Args:
            pattern: Pattern with dots for unknown letters
            count: Maximum number of words to return
            theme: Optional theme to prefer themed words
            used_words: Set of already-used words to avoid

        Returns:
            List of matching words
        """
        pattern = pattern.upper()
        used_words = used_words or set()

        # Check cache
        cache_key = f"{pattern}:{theme or ''}"
        if cache_key in self._word_cache:
            cached = self._word_cache[cache_key]
            # Filter out used words from cache
            available = [w for w in cached if w.upper() not in used_words]
            if available:
                self.stats["cache_hits"] += 1
                return available[:count]

        if not self.client:
            return []

        # Build prompts
        length = len(pattern)
        known_letters = [(i, c) for i, c in enumerate(pattern) if c != '.']

        if self.prompt_loader:
            try:
                template = self.prompt_loader.get('pattern_word_generation')
                system_prompt, user_prompt = template.render(
                    pattern=pattern,
                    length=length,
                    topic=theme or "General",
                    difficulty="wednesday",
                    used_words=", ".join(list(used_words)[:20]) if used_words else "none",
                    count=count,
                )
                model = template.model
            except Exception:
                system_prompt, user_prompt = self._build_pattern_prompts(
                    pattern, length, theme, used_words, count
                )
                model = "claude-opus-4-5-20251101"  # Use Opus for semantic understanding (fallback)
        else:
            system_prompt, user_prompt = self._build_pattern_prompts(
                pattern, length, theme, used_words, count
            )
            model = "claude-opus-4-5-20251101"  # Use Opus for semantic understanding (fallback)

        response = self._make_request(
            'pattern_word_generation',
            system_prompt,
            user_prompt,
            max_tokens=1024,
            temperature=0.3,
            model=model
        )

        if not response:
            return []

        # Parse response
        words = self._parse_pattern_response(response, pattern, used_words)

        if words:
            self.stats["words_generated"] += len(words)
            self._word_cache[cache_key] = words

        return words[:count]

    def _build_pattern_prompts(
        self,
        pattern: str,
        length: int,
        theme: Optional[str],
        used_words: Optional[set],
        count: int
    ) -> Tuple[str, str]:
        """Build pattern matching prompts."""
        theme_hint = f' related to "{theme}"' if theme else ""

        system_prompt = f"""You are a crossword puzzle word expert. Given a letter pattern,
generate valid English words that match exactly. Focus on:
- Common, well-known words preferred
- Words appropriate for crossword puzzles{theme_hint}"""

        used_list = ", ".join(list(used_words)[:20]) if used_words else "none"

        user_prompt = f"""Find words matching this pattern for a crossword puzzle:

Pattern: {pattern}
(where '.' represents unknown letters)

Pattern length: {length} letters
Already used words (DO NOT repeat): {used_list}

Provide {count} words that:
1. Match the pattern EXACTLY
2. Are real English words or well-known proper nouns
3. Are NOT in the already-used list

Return words in order of preference (most common first), one per line:"""

        return system_prompt, user_prompt

    def _parse_pattern_response(
        self,
        text: str,
        pattern: str,
        used_words: Optional[set]
    ) -> List[str]:
        """Parse pattern matching response."""
        words = []
        used_words = used_words or set()

        # Try YAML parsing first
        if HAS_YAML:
            try:
                data = yaml.safe_load(text)
                if isinstance(data, dict) and 'matching_words' in data:
                    for item in data['matching_words']:
                        word = item.get('word', '').upper()
                        if (len(word) == len(pattern) and
                                self._matches_pattern(word, pattern) and
                                word not in used_words):
                            words.append(word)
                    if words:
                        return words
            except yaml.YAMLError:
                pass

        # Fall back to line-by-line parsing
        for line in text.strip().split('\n'):
            word = line.strip().upper()
            word = re.sub(r'[^A-Z]', '', word)

            if (len(word) == len(pattern) and
                    self._matches_pattern(word, pattern) and
                    word not in used_words):
                words.append(word)

        return words

    def generate_clue(
        self,
        word: str,
        difficulty: str = "wednesday"
    ) -> str:
        """
        Generate a clue for a word.

        Args:
            word: The word to clue
            difficulty: Difficulty level

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
            "monday": "straightforward definition",
            "tuesday": "straightforward definition",
            "wednesday": "slightly clever or requiring some thought",
            "thursday": "tricky, misdirection allowed",
            "friday": "cryptic, requires lateral thinking",
            "saturday": "cryptic, requires lateral thinking",
            "sunday": "medium difficulty with playful theme",
            "easy": "straightforward definition",
            "medium": "slightly clever or requiring some thought",
            "hard": "cryptic, punny, or requiring wordplay knowledge",
        }

        system_prompt = f"""Write crossword clues. Make them:
- Concise (under 50 characters ideally)
- {difficulty_guidance.get(difficulty.lower(), 'medium difficulty')}
- No direct use of the word
- Suitable for a newspaper crossword"""

        user_prompt = f"""Write a crossword clue for: {word}
Respond with ONLY the clue, nothing else:"""

        response = self._make_request(
            'clue_generation_single',
            system_prompt,
            user_prompt,
            max_tokens=100,
            temperature=0.8
        )

        if response:
            clue = response.strip().strip('"\'')
            self._clue_cache[word] = clue
            return clue

        return f"Clue for {word}"

    def generate_clues_batch(
        self,
        words: List[str],
        difficulty: str = "wednesday",
        theme: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate clues for multiple words in one API call.

        Args:
            words: List of words to clue
            difficulty: Difficulty level
            theme: Optional theme context

        Returns:
            Dict mapping words to clues
        """
        # Check which words need clues
        needed = [w.upper() for w in words if w.upper() not in self._clue_cache]

        if not needed:
            return {w.upper(): self._clue_cache[w.upper()] for w in words}

        if not self.client:
            return {w.upper(): f"Clue for {w.upper()}" for w in words}

        # Build prompts
        word_list = ", ".join(needed)
        theme_context = f"\nPuzzle topic: {theme}" if theme else ""

        if self.prompt_loader:
            try:
                template = self.prompt_loader.get('clue_generation_batch')
                system_prompt, user_prompt = template.render(
                    difficulty=difficulty,
                    word_list=word_list,
                    topic=theme or "General",
                )
            except Exception:
                system_prompt = f"""Write {difficulty} crossword clues.
Requirements:
- Concise (under 50 characters each)
- No direct use of the word
- Suitable for newspaper crossword"""

                user_prompt = f"""Generate clues for these words: {word_list}
{theme_context}

Respond with ONLY JSON, no other text:
{{"WORD1": "clue1", "WORD2": "clue2", ...}}"""
        else:
            system_prompt = f"""Write {difficulty} crossword clues.
Requirements:
- Concise (under 50 characters each)
- No direct use of the word
- Suitable for newspaper crossword"""

            user_prompt = f"""Generate clues for these words: {word_list}
{theme_context}

Respond with ONLY JSON, no other text:
{{"WORD1": "clue1", "WORD2": "clue2", ...}}"""

        response = self._make_request(
            'clue_generation_batch',
            system_prompt,
            user_prompt,
            max_tokens=2048,
            temperature=0.8
        )

        if response:
            # Try to parse JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    clues = json.loads(json_match.group())
                    for word, clue in clues.items():
                        self._clue_cache[word.upper()] = clue
                except json.JSONDecodeError:
                    pass

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
            WordWithClue("OCEAN", "Large body of water"),
            WordWithClue("RIVER", "Flowing waterway"),
            WordWithClue("TRAIL", "Hiking path"),
            WordWithClue("POINT", "Sharp end"),
            WordWithClue("COAST", "Shore area"),
        ]
        return fallback

    def get_stats(self) -> Dict:
        """Get usage statistics."""
        stats = self.stats.copy()
        stats['limiter'] = self.limiter.get_stats()
        return stats

    def get_limiter_stats(self) -> Dict:
        """Get limiter statistics."""
        return self.limiter.get_stats()


def create_pattern_word_generator(
    ai_generator: AIWordGenerator,
    theme: Optional[str] = None,
    used_words: Optional[set] = None
) -> Callable[[str, int], List[str]]:
    """
    Create a word generator function for use with CSP solver.

    Args:
        ai_generator: AIWordGenerator instance
        theme: Optional theme for word generation
        used_words: Optional set of already-used words

    Returns:
        Function that takes (pattern, count) and returns list of words
    """
    used = used_words or set()

    def generator(pattern: str, count: int = 10) -> List[str]:
        words = ai_generator.get_words_matching_pattern(pattern, count, theme, used)
        used.update(w.upper() for w in words)
        return words

    return generator


# Test the generator
if __name__ == "__main__":
    print("=" * 60)
    print("AI WORD GENERATOR TEST")
    print("=" * 60)

    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        print("\nNo ANTHROPIC_API_KEY found in environment.")
        print("Set it with: export ANTHROPIC_API_KEY='your-key-here'")
        print("Testing with fallback mode...\n")

    generator = AIWordGenerator(api_key=api_key)

    print(f"AI Available: {generator.is_available()}")

    if generator.is_available():
        print("\nTesting themed word generation...")
        words = generator.generate_themed_words("Space Exploration", count=10)
        print(f"Generated {len(words)} words:")
        for w in words[:5]:
            print(f"  {w.word}: {w.clue}")

        print("\nTesting pattern matching...")
        pattern = "S...E"
        matches = generator.get_words_matching_pattern(pattern, count=5)
        print(f"Pattern '{pattern}' matches: {matches}")

        print("\nTesting clue generation...")
        clue = generator.generate_clue("ROCKET")
        print(f"ROCKET: {clue}")

        print(f"\nStats: {generator.get_stats()}")
    else:
        print("\nUsing fallback mode (no API)")
        words = generator.generate_themed_words("Test")
        print(f"Fallback words: {[w.word for w in words[:5]]}")
