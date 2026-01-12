#!/usr/bin/env python3
# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.
# Unauthorized copying, distribution, or use of this file,
# via any medium, is strictly prohibited without the express
# written permission of TrailLensCo.

"""
AI-Powered Crossword Generator

Generates NYT-style crossword puzzles using:
1. AI (Claude API) for themed word lists, pattern matching, and clues
2. CSP solver with AC-3 for grid filling
3. Validation to ensure puzzle is completeable
4. Multi-page SVG/HTML output
5. YAML intermediate format for puzzle data

Usage:
    # With YAML configuration:
    python crossword_generator.py --config config/sample_configs/newfoundland.yaml

    # With command-line arguments:
    python crossword_generator.py --topic "Space Exploration" --size 11

    # Or pass API key directly:
    python crossword_generator.py --topic "Movies" --api-key "your-key"
"""

import json
import logging
import os
import signal
import sys
import time
from typing import List, Dict, Optional
from copy import deepcopy

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Grid, WordSlot, Direction
from csp_solver import CrosswordCSP
from validator import validate_puzzle, ValidationResult
from grid_generator import GridGenerator
from page_renderer import CrosswordPageRenderer, CrosswordData
from ai_word_generator import (
    AIWordGenerator, WordWithClue, create_pattern_word_generator
)
from config import (
    PuzzleConfig, create_argument_parser, load_config,
    discover_api_key, get_model, ConfigValidationError
)
from ai_limiter import AICallbackLimiter
from logging_config import setup_logging

# Try to import optional modules
try:
    from prompt_loader import PromptLoader
    HAS_PROMPT_LOADER = True
except ImportError:
    HAS_PROMPT_LOADER = False
    PromptLoader = None

try:
    from yaml_exporter import YAMLExporter
    HAS_YAML_EXPORTER = True
except ImportError:
    HAS_YAML_EXPORTER = False
    YAMLExporter = None


class GenerationTimeoutError(Exception):
    """Raised when generation exceeds timeout limit."""
    pass


def _timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise GenerationTimeoutError("Generation exceeded time limit")


class CrosswordGenerator:
    """
    Complete crossword puzzle generator with AI integration.

    Workflow:
    1. Generate themed word list using AI
    2. Create valid grid pattern
    3. Validate grid structure
    4. Fill grid using CSP solver (with AI word requests when stuck)
    5. Validate fillability
    6. Generate clues using AI
    7. Render to multi-page output
    8. Export YAML intermediate format
    """

    def __init__(self, config: PuzzleConfig):
        """
        Initialize the crossword generator.

        Args:
            config: PuzzleConfig instance with all settings
        """
        self.config = config
        self.start_time = time.time()

        # Initialize logging
        self.log_file_path = setup_logging(
            output_dir=config.output.directory,
            log_level=config.output.log_level,
            log_file_prefix=config.output.log_file_prefix,
            enable_console=config.output.enable_console_logging,
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initialized CrosswordGenerator for topic: {config.topic}")
        self.logger.info(f"Grid size: {config.size}x{config.size}, Difficulty: {config.difficulty}")
        self.logger.info(f"Max word length: {config.get_max_word_length()}")
        self.logger.debug(f"Log file: {self.log_file_path}")

        # Initialize AI limiter
        self.limiter = AICallbackLimiter(
            max_total=config.generation.max_ai_callbacks,
            limits=config.generation.limits,
        )

        # Initialize prompt loader if available
        self.prompt_loader = None
        if HAS_PROMPT_LOADER:
            prompt_config_path = config.ai.prompt_config
            if os.path.exists(prompt_config_path):
                try:
                    self.prompt_loader = PromptLoader(prompt_config_path)
                except Exception as e:
                    self.logger.warning(f"Could not load prompts: {e}")

        # Discover API key (unless --no-ai is set)
        api_key = None if config.no_ai else discover_api_key(config)
        model = get_model(config)

        # Initialize AI word generator
        self.ai = AIWordGenerator(
            api_key=api_key,
            model=model,
            limiter=self.limiter,
            prompt_loader=self.prompt_loader,
            logger=self.logger,
        )

        # Enforce --require-ai flag
        if config.require_ai and not self.ai.is_available():
            raise ConfigValidationError(
                "AI generation is required (--require-ai) but API key not found.\n"
                "Please provide an API key via:\n"
                "  - .claude-apikey.txt file in repository root\n"
                "  - --api-key CLI argument\n"
                "  - ANTHROPIC_API_KEY environment variable"
            )

        self.word_list: List[str] = []
        self.themed_words: Dict[str, WordWithClue] = {}
        self.solution: Optional[Dict[WordSlot, str]] = None
        self._csp_stats: Dict = {}

    def generate(self) -> Optional[Dict[str, str]]:
        """
        Generate a complete crossword puzzle with optional timeout.

        Returns:
            Dict of output file paths, or None if generation failed
        """
        # Set up timeout if configured
        timeout_seconds = self.config.generation.timeout_seconds
        old_handler = None

        try:
            if timeout_seconds and timeout_seconds > 0:
                # Only set alarm on Unix systems (signal.alarm not available on Windows)
                if hasattr(signal, 'alarm'):
                    self.logger.info(f"Setting generation timeout: {timeout_seconds} seconds ({timeout_seconds/60:.1f} minutes)")
                    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
                    signal.alarm(timeout_seconds)
                else:
                    self.logger.warning("Timeout not supported on this platform (requires Unix/Linux/Mac)")

            # Run generation
            return self._generate_internal()

        except GenerationTimeoutError:
            elapsed = time.time() - self.start_time
            self.logger.error("=" * 60)
            self.logger.error("GENERATION TIMEOUT")
            self.logger.error("=" * 60)
            self.logger.error(f"Generation exceeded timeout limit of {timeout_seconds} seconds ({timeout_seconds/60:.1f} minutes)")
            self.logger.error(f"Elapsed time: {elapsed:.2f} seconds ({elapsed/60:.1f} minutes)")
            self.logger.error("Generation aborted to analyze what went wrong.")

            # Run log analysis even on timeout
            self._run_log_analysis()

            return None

        finally:
            # Cancel alarm and restore old handler
            if timeout_seconds and timeout_seconds > 0 and hasattr(signal, 'alarm'):
                signal.alarm(0)
                if old_handler:
                    signal.signal(signal.SIGALRM, old_handler)

    def _generate_internal(self) -> Optional[Dict[str, str]]:
        """
        Internal generation method (can be interrupted by timeout).

        Returns:
            Dict of output file paths, or None if generation failed
        """
        self.logger.info("=" * 60)
        self.logger.info("CROSSWORD GENERATOR")
        self.logger.info("=" * 60)
        self.logger.info(f"   Theme: {self.config.topic}")
        self.logger.info(f"   Size: {self.config.size}x{self.config.size}")
        self.logger.info(f"   Difficulty: {self.config.difficulty}")
        self.logger.info(f"   Puzzle Type: {self.config.puzzle_type}")
        self.logger.info(f"   AI Available: {self.ai.is_available()}")

        # Step 1: Generate word list
        self.logger.info("Step 1: Building word list...")
        self._build_word_list()
        self.logger.info(f"   - {len(self.word_list)} words available")
        self.logger.info(f"   - {len(self.themed_words)} themed words with clues")

        # Step 2: Create and validate grid
        self.logger.info("Step 2: Creating grid...")
        grid = self._create_grid()
        if grid is None:
            self.logger.error("   X Failed to create valid grid")
            return None
        self.logger.info("   - Grid created")

        # Step 3: Validate structure
        self.logger.info("Step 3: Validating structure...")
        validation = validate_puzzle(
            grid, self.word_list, check_fillability=False
        )
        if not validation.valid:
            self.logger.error("   X Invalid structure:")
            for error in validation.errors:
                self.logger.error(f"      - {error}")
            return None
        self.logger.info("   - Structure valid")
        self.logger.info(f"   - {validation.stats['total_words']} word slots")

        # Step 4: Fill grid using CSP
        self.logger.info("Step 4: Filling grid with CSP solver...")
        filled_grid, solution = self._fill_grid(grid)
        if solution is None:
            self.logger.error("   X Could not fill grid")
            return None
        self.logger.info("   - Grid filled successfully!")

        # Step 5: Validate fillability
        self.logger.info("Step 5: Validating solution...")
        self.logger.info(f"   - All {len(solution)} words placed")
        self.logger.info("   - Puzzle is completeable")

        # Step 6: Generate clues
        self.logger.info("Step 6: Generating clues...")
        clues = self._generate_clues(solution)
        self.logger.info(f"   - {len(clues['across'])} across clues")
        self.logger.info(f"   - {len(clues['down'])} down clues")

        # Step 7: Render output
        self.logger.info("Step 7: Rendering output...")
        output_files = self._render_output(filled_grid, solution, clues)
        self.logger.info(f"   - Generated {len(output_files)} files")

        # Step 8: Export YAML intermediate
        if 'yaml_intermediate' in self.config.output.formats and HAS_YAML_EXPORTER:
            self.logger.info("Step 8: Exporting YAML intermediate...")
            yaml_path = self._export_yaml(filled_grid, solution, clues)
            if yaml_path:
                output_files['yaml_intermediate'] = yaml_path
                self.logger.info(f"   - Exported to {yaml_path}")

        # Summary
        elapsed = time.time() - self.start_time
        self.logger.info("=" * 60)
        self.logger.info("GENERATION COMPLETE!")
        self.logger.info("=" * 60)
        self.logger.info("Output files:")
        for name, path in output_files.items():
            self.logger.info(f"   {name}: {path}")

        if self.ai.is_available():
            stats = self.ai.get_stats()
            self.logger.info("AI Stats:")
            self.logger.info(f"   API calls: {stats['api_calls']}")
            self.logger.info(f"   Words generated: {stats['words_generated']}")
            self.logger.info(f"   Cache hits: {stats['cache_hits']}")
            self.logger.info(f"   Tokens used: {stats.get('tokens_used', 0)}")

        if self._csp_stats:
            self.logger.info("CSP Stats:")
            self.logger.info(f"   Backtracks: {self._csp_stats.get('backtracks', 0)}")
            self.logger.info(f"   AC-3 revisions: {self._csp_stats.get('ac3_revisions', 0)}")
            self.logger.info(f"   AI words added: {self._csp_stats.get('ai_words_added', 0)}")

        # Word length distribution
        if solution:
            length_dist = {}
            for slot, word in solution.items():
                length = len(word)
                length_dist[length] = length_dist.get(length, 0) + 1

            max_word_length = self.config.get_max_word_length()
            self.logger.info("Word Length Distribution:")
            self.logger.info(f"   Max allowed: {max_word_length} letters")
            for length in sorted(length_dist.keys()):
                count = length_dist[length]
                bar = "█" * (count // 2)
                marker = " ⚠" if length > max_word_length else ""
                self.logger.debug(f"   {length:2d} letters: {count:3d} words {bar}{marker}")

        self.logger.info(f"Generation time: {elapsed:.2f} seconds")

        # Generate AI log analysis report if requested
        analysis_report = self._run_log_analysis()
        if analysis_report:
            output_files['analysis_report'] = analysis_report

        return output_files

    def _run_log_analysis(self) -> Optional[str]:
        """
        Run AI log analysis if configured.

        Returns:
            Path to analysis report, or None if not generated
        """
        if not self.config.output.analyze_log or not self.ai.is_available():
            return None

        self.logger.info("Generating AI log analysis report...")
        try:
            from log_analyzer import LogAnalyzer
            analyzer = LogAnalyzer(self.ai, logger=self.logger)
            report_path = analyzer.analyze_log(
                log_path=self.log_file_path,
                output_dir=self.config.output.directory
            )
            if report_path:
                self.logger.info(f"   - Analysis report saved to {report_path}")
                return report_path
        except Exception as e:
            self.logger.warning(f"Could not generate log analysis: {e}")

        return None

    def _build_word_list(self):
        """Build word list from AI and fallback sources."""
        max_word_length = self.config.get_max_word_length()

        # Get themed words from AI
        if self.ai.is_available():
            themed = self.ai.generate_themed_words(
                self.config.topic,
                count=150,
                min_length=3,
                max_length=max_word_length,  # Use recommended max, not grid size
                difficulty=self.config.difficulty,
                puzzle_type=self.config.puzzle_type,
                topic_aspects=self.config.topic_aspects,
            )
            for tw in themed:
                self.word_list.append(tw.word)
                self.themed_words[tw.word] = tw

        # Add base word list
        base_words = self._get_base_word_list()
        self.word_list.extend(base_words)

        # Deduplicate and filter - use max_word_length instead of grid size
        self.word_list = list(set(
            w.upper() for w in self.word_list
            if 3 <= len(w) <= max_word_length and w.isalpha()
        ))

        # Sort by length (longer words first for theme entries)
        self.word_list.sort(key=len, reverse=True)

    def _get_base_word_list(self) -> List[str]:
        """Get base crossword word list.

        First attempts to load from words_dictionary.json (dwyl/english-words).
        Falls back to hardcoded word list if JSON file is not available.

        Returns:
            List of uppercase English words suitable for crossword puzzles.
        """
        # Try to load from JSON file first
        json_words = self._load_words_from_json()
        if json_words:
            return json_words

        # Fall back to hardcoded list
        return self._get_hardcoded_word_list()

    def _load_words_from_json(self) -> Optional[List[str]]:
        """Load words from words_dictionary.json file.

        Returns:
            List of uppercase words if file exists and is valid, None otherwise.
        """
        # Get path to JSON file relative to this source file
        src_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(src_dir, "data", "words_dictionary.json")

        if not os.path.exists(json_path):
            return None

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                word_dict = json.load(f)

            # Filter words: only alphabetic, 3+ letters, uppercase
            words = [
                word.upper()
                for word in word_dict.keys()
                if word.isalpha() and len(word) >= 3
            ]

            # Sort by length (longer words first) for theme entries
            words.sort(key=len, reverse=True)

            self.logger.debug(f"   - Loaded {len(words)} words from words_dictionary.json")
            return words

        except (json.JSONDecodeError, IOError, OSError) as e:
            self.logger.warning(f"   - Could not load words_dictionary.json: {e}")
            return None

    def _get_hardcoded_word_list(self) -> List[str]:
        """Get fallback hardcoded word list.

        Returns:
            List of common crossword-friendly English words.
        """
        words = []

        # 3-letter words
        words.extend([
            "ACE", "ACT", "ADD", "AGE", "AID", "AIM", "AIR", "ALL", "AND", "ANT",
            "APE", "ARC", "ARE", "ARK", "ARM", "ART", "ATE", "AWE", "AXE", "BAD",
            "BAG", "BAN", "BAR", "BAT", "BED", "BEE", "BET", "BIG", "BIT", "BOW",
            "BOX", "BOY", "BUD", "BUG", "BUN", "BUS", "BUT", "BUY", "CAB", "CAN",
            "CAP", "CAR", "CAT", "COW", "CRY", "CUP", "CUT", "DAY", "DEN", "DEW",
            "DIG", "DIM", "DOC", "DOE", "DOG", "DOT", "DRY", "DUE", "DYE", "EAR",
            "EAT", "EGG", "ELM", "EMU", "END", "ERA", "EVE", "EYE", "FAN", "FAR",
            "FAT", "FED", "FEE", "FEW", "FIG", "FIN", "FIT", "FLY", "FOE", "FOG",
            "FOR", "FOX", "FUN", "FUR", "GAP", "GAS", "GEL", "GEM", "GET", "GNU",
            "GOD", "GOT", "GUM", "GUN", "GUT", "GUY", "GYM", "HAM", "HAS", "HAT",
            "HEN", "HID", "HIM", "HIP", "HIS", "HIT", "HOG", "HOP", "HOT", "HOW",
            "HUB", "HUE", "HUG", "ICE", "ICY", "ILL", "IMP", "INK", "INN", "ION",
            "IRE", "ITS", "JAB", "JAM", "JAR", "JAW", "JAY", "JET", "JIG", "JOB",
            "JOG", "JOT", "JOY", "JUG", "KEY", "KID", "KIN", "KIT", "LAB", "LAD",
            "LAP", "LAW", "LAY", "LED", "LEG", "LET", "LID", "LIE", "LIP", "LIT",
            "LOG", "LOT", "LOW", "MAD", "MAN", "MAP", "MAT", "MEN", "MET", "MIX",
            "MOB", "MOM", "MOP", "MUD", "MUG", "NAP", "NET", "NEW", "NIT", "NOD",
            "NOR", "NOT", "NOW", "NUT", "OAK", "OAR", "OAT", "ODD", "OIL", "OLD",
            "ONE", "OPT", "ORB", "ORE", "OUR", "OUT", "OWE", "OWL", "OWN", "PAD",
            "PAN", "PAT", "PAW", "PAY", "PEA", "PEG", "PEN", "PER", "PET", "PIE",
            "PIG", "PIN", "PIT", "PLY", "POD", "POP", "POT", "PRY", "PUB", "PUN",
            "PUP", "PUT", "RAG", "RAM", "RAN", "RAP", "RAT", "RAW", "RAY", "RED",
            "REF", "RIB", "RID", "RIG", "RIM", "RIP", "ROB", "ROD", "ROT", "ROW",
            "RUB", "RUG", "RUN", "RUT", "RYE", "SAD", "SAP", "SAT", "SAW", "SAY",
            "SEA", "SET", "SEW", "SHE", "SHY", "SIN", "SIP", "SIR", "SIS", "SIT",
            "SIX", "SKI", "SKY", "SLY", "SOB", "SOD", "SON", "SOP", "SOT", "SOW",
            "SOY", "SPA", "SPY", "STY", "SUB", "SUM", "SUN", "TAB", "TAD", "TAG",
            "TAN", "TAP", "TAR", "TAX", "TEA", "TEN", "THE", "TIE", "TIN", "TIP",
            "TOE", "TON", "TOP", "TOT", "TOW", "TOY", "TRY", "TUB", "TUG", "TWO",
            "URN", "USE", "VAN", "VAT", "VET", "VIA", "VIE", "VOW", "WAD", "WAR",
            "WAS", "WAX", "WAY", "WEB", "WED", "WET", "WHO", "WHY", "WIG", "WIN",
            "WIT", "WOE", "WOK", "WON", "WOO", "WOW", "YAK", "YAM", "YAP", "YAW",
            "YEA", "YES", "YET", "YEW", "YOU", "ZAP", "ZEN", "ZIP", "ZOO",
        ])

        # 4-letter words
        words.extend([
            "ABLE", "ACHE", "ACID", "AGED", "AIDE", "AREA", "ARMY", "AWAY", "BABY",
            "BACK", "BAKE", "BALL", "BAND", "BANK", "BARE", "BASE", "BATH", "BEAR",
            "BEAT", "BEEN", "BEER", "BELL", "BELT", "BEND", "BENT", "BEST", "BIRD",
            "BITE", "BLOW", "BLUE", "BOAT", "BODY", "BOLD", "BOLT", "BOMB", "BOND",
            "BONE", "BOOK", "BOOM", "BOOT", "BORE", "BORN", "BOSS", "BOTH", "BOWL",
            "BURN", "BUSY", "CAFE", "CAGE", "CAKE", "CALL", "CALM", "CAME", "CAMP",
            "CAPE", "CARD", "CARE", "CART", "CASE", "CASH", "CAST", "CAVE", "CELL",
            "CHIP", "CITY", "CLAP", "CLAY", "CLIP", "CLUB", "CLUE", "COAL", "COAT",
            "CODE", "COIL", "COIN", "COLD", "COME", "COOK", "COOL", "COPE", "COPY",
            "CORD", "CORE", "CORK", "CORN", "COST", "COZY", "CRAB", "CREW", "CROP",
            "CURE", "CUTE", "DALE", "DAME", "DAMP", "DARE", "DARK", "DART", "DASH",
            "DATA", "DATE", "DAWN", "DAYS", "DEAD", "DEAF", "DEAL", "DEAN", "DEAR",
            "DEBT", "DECK", "DEED", "DEEM", "DEEP", "DEER", "DEMO", "DENY", "DESK",
            "DIAL", "DICE", "DIED", "DIET", "DINE", "DIRT", "DISH", "DISK", "DIVE",
            "DOCK", "DOES", "DOLL", "DOME", "DONE", "DOOM", "DOOR", "DOSE", "DOWN",
            "DRAG", "DRAW", "DREW", "DRIP", "DROP", "DRUG", "DRUM", "DUAL", "DUDE",
            "DUEL", "DUES", "DUKE", "DULL", "DUMB", "DUMP", "DUNE", "DUSK", "DUST",
            "DUTY", "EACH", "EARL", "EARN", "EARS", "EASE", "EAST", "EASY", "ECHO",
            "EDGE", "EDIT", "ELSE", "EMIT", "ENDS", "ENVY", "EPIC", "EVEN", "EVER",
            "EVIL", "EXAM", "EXIT", "FACE", "FACT", "FADE", "FAIL", "FAIR", "FAKE",
            "FALL", "FAME", "FANS", "FARE", "FARM", "FAST", "FATE", "FEAR", "FEAT",
            "FEED", "FEEL", "FEES", "FEET", "FELL", "FELT", "FILE", "FILL", "FILM",
            "FIND", "FINE", "FIRE", "FIRM", "FISH", "FIST", "FLAG", "FLAT", "FLAW",
            "FLED", "FLEW", "FLIP", "FLOW", "FOAM", "FOLD", "FOLK", "FOOD", "FOOL",
            "FOOT", "FORD", "FORE", "FORK", "FORM", "FORT", "FOUR", "FREE", "FROM",
            "FUEL", "FULL", "FUND", "FUSE", "GAIN", "GALE", "GAME", "GANG", "GATE",
            "GAVE", "GAZE", "GEAR", "GENE", "GIFT", "GIRL", "GIVE", "GLAD", "GLOW",
            "GLUE", "GOAL", "GOAT", "GOES", "GOLD", "GOLF", "GONE", "GOOD", "GRAB",
            "GRAY", "GREW", "GREY", "GRID", "GRIM", "GRIN", "GRIP", "GROW", "GULF",
            "GURU", "GUST", "GUYS", "HAIR", "HALF", "HALL", "HALT", "HAND", "HANG",
            "HARD", "HARM", "HATE", "HAVE", "HEAD", "HEAL", "HEAR", "HEAT", "HEEL",
            "HELD", "HELL", "HELP", "HERO", "HIGH", "HIKE", "HILL", "HINT", "HIRE",
            "HOLD", "HOLE", "HOME", "HOOD", "HOOK", "HOPE", "HORN", "HOST", "HOUR",
            "HUGE", "HUNG", "HUNT", "HURT", "IDEA", "INCH", "INTO", "IRON", "ITEM",
            "JACK", "JAIL", "JAZZ", "JEAN", "JOBS", "JOIN", "JOKE", "JUMP", "JUNE",
            "JUNK", "JURY", "JUST", "KEEN", "KEEP", "KEPT", "KICK", "KIDS", "KILL",
            "KIND", "KING", "KISS", "KNEE", "KNEW", "KNIT", "KNOB", "KNOT", "KNOW",
            "LACK", "LAID", "LAKE", "LAMB", "LAMP", "LAND", "LANE", "LAST", "LATE",
            "LAWN", "LAWS", "LEAD", "LEAF", "LEAN", "LEAP", "LEFT", "LEND", "LENS",
            "LESS", "LIAR", "LICK", "LIES", "LIFE", "LIFT", "LIKE", "LIMB", "LIME",
            "LIMP", "LINE", "LINK", "LION", "LIPS", "LIST", "LIVE", "LOAD", "LOAN",
            "LOCK", "LOGO", "LONE", "LONG", "LOOK", "LOOP", "LORD", "LOSE", "LOSS",
            "LOST", "LOTS", "LOUD", "LOVE", "LUCK", "LUNG", "MADE", "MAIL", "MAIN",
            "MAKE", "MALE", "MALL", "MANY", "MAPS", "MARK", "MARS", "MASK", "MASS",
            "MATE", "MATH", "MAYO", "MAZE", "MEAL", "MEAN", "MEAT", "MEET", "MELT",
            "MEMO", "MENU", "MERE", "MESH", "MESS", "MILD", "MILE", "MILK", "MILL",
            "MIND", "MINE", "MINT", "MISS", "MODE", "MOOD", "MOON", "MORE", "MOST",
            "MOVE", "MUCH", "MUST", "NAME", "NAVY", "NEAR", "NEAT", "NECK", "NEED",
            "NEST", "NEWS", "NEXT", "NICE", "NINE", "NODE", "NONE", "NOON", "NORM",
            "NOSE", "NOTE", "NOUN", "ODDS", "OKAY", "ONCE", "ONES", "ONLY", "ONTO",
            "OPEN", "ORAL", "OVEN", "OVER", "OWED", "OWES", "OWNS", "PACE", "PACK",
            "PAGE", "PAID", "PAIN", "PAIR", "PALE", "PALM", "PANT", "PARK", "PART",
            "PASS", "PAST", "PATH", "PEAK", "PEEL", "PEER", "PICK", "PIER", "PILE",
            "PILL", "PINE", "PINK", "PIPE", "PITY", "PLAN", "PLAY", "PLEA", "PLOT",
            "PLUG", "PLUS", "POEM", "POET", "POLE", "POLL", "POND", "POOL", "POOR",
            "PORK", "PORT", "POSE", "POST", "POUR", "PRAY", "PREP", "PREY", "PROS",
            "PULL", "PUMP", "PURE", "PUSH", "QUIT", "RACE", "RACK", "RAGE", "RAID",
            "RAIL", "RAIN", "RAMP", "RANG", "RANK", "RARE", "RATE", "READ", "REAL",
            "REAR", "RELY", "RENT", "REST", "RICE", "RICH", "RIDE", "RING", "RIOT",
            "RISE", "RISK", "ROAD", "ROAR", "ROBE", "ROCK", "RODE", "ROLE", "ROLL",
            "ROOF", "ROOM", "ROOT", "ROPE", "ROSE", "ROWS", "RUDE", "RUIN", "RULE",
            "RUSH", "RUST", "SACK", "SAFE", "SAGE", "SAID", "SAIL", "SAKE", "SALE",
            "SALT", "SAME", "SAND", "SANE", "SANG", "SANK", "SAVE", "SCAN", "SEAL",
            "SEAM", "SEAT", "SEED", "SEEK", "SEEM", "SEEN", "SELF", "SELL", "SEND",
            "SENT", "SHED", "SHIP", "SHOP", "SHOT", "SHOW", "SHUT", "SICK", "SIDE",
            "SIGN", "SILK", "SING", "SINK", "SITE", "SIZE", "SKIP", "SLAM", "SLAP",
            "SLED", "SLID", "SLIM", "SLIP", "SLOT", "SLOW", "SNAP", "SNOW", "SOAK",
            "SOAP", "SOAR", "SOCK", "SOFT", "SOIL", "SOLD", "SOLE", "SOME", "SONG",
            "SOON", "SORE", "SORT", "SOUL", "SOUP", "SOUR", "SPAN", "SPIN", "SPIT",
            "SPOT", "STAR", "STAY", "STEM", "STEP", "STEW", "STOP", "STUB", "SUCH",
            "SUIT", "SUNG", "SUNK", "SURE", "SURF", "SWAN", "SWAP", "SWIM", "TABS",
            "TACT", "TAIL", "TAKE", "TALE", "TALK", "TALL", "TANK", "TAPE", "TASK",
            "TEAM", "TEAR", "TECH", "TEEN", "TELL", "TEMP", "TEND", "TENT", "TERM",
            "TEST", "TEXT", "THAN", "THAT", "THEM", "THEN", "THEY", "THIN", "THIS",
            "THUS", "TICK", "TIDE", "TIDY", "TIED", "TIER", "TIES", "TILE", "TILL",
            "TIME", "TINY", "TIRE", "TOAD", "TOLD", "TOLL", "TOMB", "TONE", "TOOK",
            "TOOL", "TOPS", "TORE", "TORN", "TOSS", "TOUR", "TOWN", "TOYS", "TRAP",
            "TRAY", "TREE", "TRIM", "TRIO", "TRIP", "TRUE", "TUBE", "TUNA", "TUNE",
            "TURN", "TWIN", "TYPE", "UGLY", "UNIT", "UPON", "URGE", "USED", "USER",
            "USES", "VAIN", "VARY", "VAST", "VEIN", "VERB", "VERY", "VEST", "VIEW",
            "VINE", "VISA", "VOID", "VOLT", "VOTE", "WADE", "WAGE", "WAIT", "WAKE",
            "WALK", "WALL", "WANT", "WARD", "WARM", "WARN", "WASH", "WAVE", "WEAK",
            "WEAR", "WEED", "WEEK", "WENT", "WERE", "WEST", "WHAT", "WHEN", "WHIP",
            "WHOM", "WIDE", "WIFE", "WILD", "WILL", "WIND", "WINE", "WING", "WIRE",
            "WISE", "WISH", "WITH", "WOKE", "WOLF", "WOMB", "WOOD", "WOOL", "WORD",
            "WORE", "WORK", "WORM", "WORN", "WRAP", "YARD", "YARN", "YEAH", "YEAR",
            "YELL", "YOUR", "ZERO", "ZONE", "ZOOM",
        ])

        # 5-letter words
        words.extend([
            "ABOUT", "ABOVE", "ABUSE", "ACTOR", "ACUTE", "ADMIT", "ADOPT", "ADULT",
            "AFTER", "AGAIN", "AGENT", "AGREE", "AHEAD", "ALARM", "ALBUM", "ALERT",
            "ALIEN", "ALIGN", "ALIKE", "ALIVE", "ALLOW", "ALONE", "ALONG", "ALTER",
            "AMONG", "ANGEL", "ANGER", "ANGLE", "ANGRY", "APART", "APPLE", "APPLY",
            "ARENA", "ARGUE", "ARISE", "ARMOR", "ARRAY", "ARROW", "ASIDE", "ASSET",
            "AVOID", "AWARD", "AWARE", "BADLY", "BASIC", "BASIS", "BEACH", "BEGAN",
            "BEGIN", "BEING", "BELOW", "BENCH", "BIRTH", "BLACK", "BLADE", "BLAME",
            "BLANK", "BLAST", "BLAZE", "BLEND", "BLESS", "BLIND", "BLINK", "BLOCK",
            "BLOOD", "BLOOM", "BLOWN", "BLUES", "BLUNT", "BOARD", "BONDS", "BONES",
            "BOOST", "BOOTH", "BOUND", "BRAIN", "BRAKE", "BRAND", "BRASS", "BRAVE",
            "BREAD", "BREAK", "BREED", "BRICK", "BRIDE", "BRIEF", "BRING", "BROAD",
            "BROKE", "BROOK", "BROOM", "BROWN", "BRUSH", "BUILD", "BUILT", "BUNCH",
            "BURST", "BUYER", "CABIN", "CABLE", "CAMEL", "CANAL", "CANDY", "CARDS",
            "CARGO", "CARRY", "CASES", "CATCH", "CAUSE", "CEASE", "CHAIN", "CHAIR",
            "CHAOS", "CHARM", "CHART", "CHASE", "CHEAP", "CHEAT", "CHECK", "CHEEK",
            "CHEER", "CHESS", "CHEST", "CHIEF", "CHILD", "CHINA", "CHIPS", "CHOIR",
            "CHORD", "CHOSE", "CIVIL", "CLAIM", "CLASH", "CLASS", "CLEAN", "CLEAR",
            "CLERK", "CLICK", "CLIFF", "CLIMB", "CLING", "CLOCK", "CLOSE", "CLOTH",
            "CLOUD", "CLUBS", "COACH", "COAST", "CORAL", "CORES", "COUCH", "COULD",
            "COUNT", "COURT", "COVER", "CRACK", "CRAFT", "CRANE", "CRASH", "CRAZY",
            "CREAM", "CREEK", "CREEP", "CREST", "CRIME", "CRISP", "CROSS", "CROWD",
            "CROWN", "CRUDE", "CRUSH", "CURVE", "CYCLE", "DAILY", "DANCE", "DATED",
            "DEALS", "DEALT", "DEATH", "DEBUT", "DECAY", "DELAY", "DELTA", "DENSE",
            "DEPTH", "DESKS", "DIARY", "DIRTY", "DITCH", "DOING", "DOUBT", "DOUGH",
            "DOZEN", "DRAFT", "DRAIN", "DRAMA", "DRANK", "DRAWN", "DREAD", "DREAM",
            "DRESS", "DRIED", "DRIFT", "DRILL", "DRINK", "DRIVE", "DROPS", "DROWN",
            "DRUGS", "DRUNK", "DYING", "EAGER", "EARLY", "EARTH", "EASED", "EATEN",
            "EDGES", "EIGHT", "ELBOW", "ELDER", "ELECT", "ELITE", "EMPTY", "ENDED",
            "ENEMY", "ENJOY", "ENTER", "ENTRY", "EQUAL", "ERROR", "ESSAY", "EVENT",
            "EVERY", "EXACT", "EXIST", "EXTRA", "FACED", "FACTS", "FAITH", "FALSE",
            "FANCY", "FARMS", "FATAL", "FAULT", "FAVOR", "FEAST", "FENCE", "FEWER",
            "FIBER", "FIELD", "FIFTH", "FIFTY", "FIGHT", "FILED", "FINAL", "FINDS",
            "FIRED", "FIRES", "FIRMS", "FIRST", "FIXED", "FLAGS", "FLAME", "FLASH",
            "FLATS", "FLESH", "FLIES", "FLOAT", "FLOCK", "FLOOD", "FLOOR", "FLOUR",
            "FLOWS", "FLUID", "FLUSH", "FOCUS", "FOLKS", "FORCE", "FORMS", "FORTH",
            "FORTY", "FORUM", "FOUND", "FRAME", "FRANK", "FRAUD", "FRESH", "FRIED",
            "FRONT", "FROST", "FRUIT", "FULLY", "FUNDS", "FUNNY", "GAMES", "GATES",
            "GAUGE", "GENRE", "GHOST", "GIANT", "GIFTS", "GIRLS", "GIVEN", "GIVES",
            "GLASS", "GLOBE", "GLORY", "GLOVE", "GOALS", "GOING", "GOODS", "GOOSE",
            "GRACE", "GRADE", "GRAIN", "GRAND", "GRANT", "GRAPE", "GRAPH", "GRASP",
            "GRASS", "GRAVE", "GREAT", "GREEK", "GREEN", "GREET", "GRIEF", "GRILL",
            "GRIND", "GRIPS", "GROSS", "GROUP", "GROVE", "GROWN", "GROWS", "GUARD",
            "GUESS", "GUEST", "GUIDE", "GUILT", "HAPPY", "HARSH", "HASTE", "HAVEN",
            "HEADS", "HEARD", "HEART", "HEATS", "HEAVY", "HEDGE", "HEELS", "HELLO",
            "HELPS", "HENCE", "HERBS", "HINTS", "HOBBY", "HOLDS", "HOLES", "HONEY",
            "HONOR", "HOPED", "HOPES", "HORNS", "HORSE", "HOSTS", "HOTEL", "HOURS",
            "HOUSE", "HUMAN", "HUMOR", "HURRY", "IDEAL", "IDEAS", "IMAGE", "IMPLY",
            "INDEX", "INNER", "INPUT", "IRAQI", "IRISH", "IRONY", "ISSUE", "ITEMS",
            "JAPAN", "JEANS", "JEWEL", "JOINS", "JOINT", "JONES", "JUDGE", "JUICE",
            "KEEPS", "KINDS", "KINGS", "KNEES", "KNELT", "KNIFE", "KNOCK", "KNOWN",
            "KNOWS", "LABEL", "LABOR", "LACKS", "LAKES", "LANDS", "LANES", "LARGE",
            "LASER", "LATER", "LAUGH", "LAYER", "LEADS", "LEARN", "LEASE", "LEAST",
            "LEAVE", "LEGAL", "LEMON", "LEVEL", "LEWIS", "LIGHT", "LIKED", "LIKES",
            "LIMIT", "LINED", "LINES", "LINKS", "LISTS", "LIVED", "LIVER", "LIVES",
            "LOADS", "LOANS", "LOCAL", "LOCKS", "LODGE", "LOGIC", "LOOSE", "LORDS",
            "LOSES", "LOVED", "LOVER", "LOVES", "LOWER", "LOYAL", "LUCKY", "LUNCH",
            "LYING", "MAGIC", "MAJOR", "MAKER", "MALES", "MANOR", "MARCH", "MARKS",
            "MARSH", "MATCH", "MAYBE", "MAYOR", "MEALS", "MEANS", "MEANT", "MEDAL",
            "MEDIA", "MERIT", "METAL", "METER", "MIDST", "MIGHT", "MILES", "MILLS",
            "MINDS", "MINER", "MINOR", "MINUS", "MIXED", "MODEL", "MODES", "MONEY",
            "MONTH", "MORAL", "MOTOR", "MOTTO", "MOUNT", "MOUSE", "MOUTH", "MOVED",
            "MOVES", "MOVIE", "MUSIC", "NAMED", "NAMES", "NEEDS", "NERVE", "NEVER",
            "NEWER", "NEWLY", "NIGHT", "NINTH", "NOISE", "NORTH", "NOTED", "NOTES",
            "NOVEL", "NURSE", "OCCUR", "OCEAN", "OFFER", "OFTEN", "OLIVE", "ONSET",
            "OPERA", "OPTED", "ORBIT", "ORDER", "OTHER", "OUGHT", "OUTER", "OWNED",
            "OWNER", "OXIDE", "OZONE", "PACKS", "PAGES", "PAINT", "PAIRS", "PANEL",
            "PANIC", "PAPER", "PARKS", "PARTS", "PARTY", "PASTA", "PASTE", "PATCH",
            "PATHS", "PAUSE", "PEACE", "PEAKS", "PEARL", "PEERS", "PENNY", "PHASE",
            "PHONE", "PHOTO", "PIANO", "PICKS", "PIECE", "PILOT", "PINCH", "PITCH",
            "PIZZA", "PLACE", "PLAIN", "PLANE", "PLANS", "PLANT", "PLATE", "PLAYS",
            "PLAZA", "PLEAD", "PLOTS", "POEMS", "POINT", "POLAR", "POLES", "POLLS",
            "POOLS", "PORCH", "PORTS", "POSED", "POSTS", "POUND", "POWER", "PRESS",
            "PRICE", "PRIDE", "PRIME", "PRINT", "PRIOR", "PRIZE", "PROBE", "PROOF",
            "PROUD", "PROVE", "PULLS", "PULSE", "PUMPS", "PUNCH", "PUPIL", "PURSE",
            "QUEEN", "QUEST", "QUEUE", "QUICK", "QUIET", "QUITE", "QUOTA", "QUOTE",
            "RACES", "RADAR", "RADIO", "RAGED", "RAIDS", "RAILS", "RAISE", "RALLY",
            "RANCH", "RANGE", "RANKS", "RAPID", "RATED", "RATES", "RATIO", "REACH",
            "REACT", "READS", "READY", "REALM", "REBEL", "REFER", "REIGN", "RELAX",
            "REPLY", "RESET", "RESIN", "RESTS", "RIDER", "RIDGE", "RIFLE", "RIGHT",
            "RIGID", "RINGS", "RISEN", "RISES", "RISKS", "RISKY", "RIVAL", "RIVER",
            "ROADS", "ROBOT", "ROCKS", "ROCKY", "ROLES", "ROMAN", "ROOMS", "ROOTS",
            "ROUGH", "ROUND", "ROUTE", "ROYAL", "RUGBY", "RUINS", "RULED", "RULER",
            "RULES", "RURAL", "SADLY", "SAFER", "SAINT", "SALAD", "SALES", "SANDY",
            "SAUCE", "SAVED", "SAVES", "SCALE", "SCENE", "SCOPE", "SCORE", "SEATS",
            "SEEDS", "SEEKS", "SEEMS", "SEIZE", "SELLS", "SENDS", "SENSE", "SERUM",
            "SERVE", "SETUP", "SEVEN", "SHADE", "SHAKE", "SHALL", "SHAME", "SHAPE",
            "SHARE", "SHARP", "SHEEP", "SHEER", "SHEET", "SHELF", "SHELL", "SHIFT",
            "SHINE", "SHIPS", "SHIRT", "SHOCK", "SHOES", "SHOOK", "SHOOT", "SHOPS",
            "SHORE", "SHORT", "SHOTS", "SHOWN", "SHOWS", "SIDES", "SIGHT", "SIGMA",
            "SIGNS", "SILLY", "SIMON", "SINCE", "SITES", "SIXTH", "SIXTY", "SIZED",
            "SIZES", "SKILL", "SKINS", "SLAVE", "SLEEP", "SLICE", "SLIDE", "SLOPE",
            "SLOWS", "SMALL", "SMART", "SMELL", "SMILE", "SMITH", "SMOKE", "SNAKE",
            "SOLID", "SOLVE", "SONGS", "SORRY", "SORTS", "SOULS", "SOUND", "SOUTH",
            "SPACE", "SPARE", "SPARK", "SPEAK", "SPEED", "SPELL", "SPEND", "SPENT",
            "SPILL", "SPINE", "SPLIT", "SPOKE", "SPORT", "SPOTS", "SPRAY", "SQUAD",
            "STACK", "STAFF", "STAGE", "STAKE", "STAMP", "STAND", "STARK", "STARS",
            "START", "STATE", "STAYS", "STEAL", "STEAM", "STEEL", "STEEP", "STEMS",
            "STEPS", "STICK", "STIFF", "STILL", "STOCK", "STONE", "STOOD", "STOPS",
            "STORE", "STORM", "STORY", "STOVE", "STRAP", "STRAW", "STRIP", "STUCK",
            "STUFF", "STYLE", "SUGAR", "SUITE", "SUITS", "SUPER", "SURGE", "SWEET",
            "SWEPT", "SWIFT", "SWING", "SWISS", "SWORD", "SWUNG", "TABLE", "TAKEN",
            "TAKES", "TALES", "TALKS", "TANKS", "TAPES", "TASKS", "TASTE", "TAXES",
            "TEACH", "TEAMS", "TEARS", "TEETH", "TELLS", "TEMPO", "TENDS", "TENTH",
            "TERMS", "TESTS", "TEXAS", "TEXTS", "THANK", "THEFT", "THEME", "THERE",
            "THESE", "THICK", "THIEF", "THING", "THINK", "THIRD", "THOSE", "THREE",
            "THREW", "THROW", "THUMB", "TIGER", "TIGHT", "TIMES", "TIRED", "TITLE",
            "TODAY", "TOKEN", "TONES", "TOOLS", "TOOTH", "TOPIC", "TOTAL", "TOUCH",
            "TOUGH", "TOURS", "TOWER", "TOWNS", "TRACE", "TRACK", "TRADE", "TRAIL",
            "TRAIN", "TRAIT", "TRASH", "TREAT", "TREES", "TREND", "TRIAL", "TRIBE",
            "TRICK", "TRIED", "TRIES", "TRIPS", "TROOP", "TRUCK", "TRULY", "TRUNK",
            "TRUST", "TRUTH", "TUBES", "TUMOR", "TUNED", "TURNS", "TWICE", "TWINS",
            "TWIST", "TYPES", "UNCLE", "UNDER", "UNION", "UNITS", "UNITY", "UNTIL",
            "UPPER", "UPSET", "URBAN", "URGED", "USAGE", "USERS", "USING", "USUAL",
            "VALID", "VALUE", "VALVE", "VAPOR", "VAULT", "VENUE", "VERGE", "VIDEO",
            "VIEWS", "VIRUS", "VISIT", "VITAL", "VOCAL", "VOICE", "VOTES", "WAGES",
            "WAGON", "WAIST", "WALKS", "WALLS", "WANTS", "WASTE", "WATCH", "WATER",
            "WAVES", "WEEKS", "WEIGH", "WEIRD", "WELLS", "WHALE", "WHEAT", "WHEEL",
            "WHERE", "WHICH", "WHILE", "WHITE", "WHOLE", "WHOSE", "WIDER", "WIDTH",
            "WINDS", "WINES", "WINGS", "WIRED", "WIRES", "WITCH", "WIVES", "WOMAN",
            "WOMEN", "WOODS", "WORDS", "WORKS", "WORLD", "WORRY", "WORSE", "WORST",
            "WORTH", "WOULD", "WOUND", "WRIST", "WRITE", "WRONG", "WROTE", "YARDS",
            "YEARS", "YIELD", "YOUNG", "YOURS", "YOUTH", "ZONES",
        ])

        return words

    def _create_grid(self) -> Optional[Grid]:
        """Create a valid grid pattern."""
        max_word_length = self.config.get_max_word_length()
        generator = GridGenerator(size=self.config.size, max_word_length=max_word_length, logger=self.logger)

        # Try predefined patterns first
        num_patterns = generator.list_available_patterns()

        for i in range(max(num_patterns, 1)):
            if num_patterns > 0:
                grid = generator.generate(pattern_index=i)
            else:
                grid = generator.generate_random()

            if grid:
                return grid

        return None

    def _fill_grid(
        self,
        grid: Grid
    ) -> tuple[Grid, Optional[Dict[WordSlot, str]]]:
        """Fill grid using CSP solver with AI word requests."""
        # Create word generator function for CSP
        word_gen = None
        if self.ai.is_available():
            word_gen = create_pattern_word_generator(
                self.ai,
                self.config.topic,
                set()
            )

        # Create and run CSP solver
        csp = CrosswordCSP(grid, self.word_list, word_generator=word_gen, logger=self.logger)

        solution = csp.solve(use_inference=True)

        if solution:
            # Apply solution to grid
            csp.apply_solution(solution)

            # Store stats
            self._csp_stats = csp.stats

            return grid, solution

        return grid, None

    def _generate_clues(
        self,
        solution: Dict[WordSlot, str]
    ) -> Dict[str, List]:
        """Generate clues for all words using AI."""
        across_clues = []
        down_clues = []

        # Get all words
        words = list(solution.values())

        # Generate clues in batch if AI is available
        if self.ai.is_available():
            # Separate themed words (already have clues) from others
            needs_clues = [w for w in words if w not in self.themed_words]
            clues = self.ai.generate_clues_batch(
                needs_clues,
                self.config.difficulty,
                self.config.topic
            )
        else:
            clues = {}

        # Build clue lists
        for slot, word in solution.items():
            if word in self.themed_words:
                clue = self.themed_words[word].clue
            elif word in clues:
                clue = clues[word]
            else:
                clue = f"Clue for {word}"

            if slot.direction == Direction.ACROSS:
                across_clues.append((slot.number, clue, len(word)))
            else:
                down_clues.append((slot.number, clue, len(word)))

        # Sort by clue number
        across_clues.sort(key=lambda x: x[0])
        down_clues.sort(key=lambda x: x[0])

        return {"across": across_clues, "down": down_clues}

    def _render_output(
        self,
        grid: Grid,
        solution: Dict[WordSlot, str],
        clues: Dict
    ) -> Dict[str, str]:
        """Render multi-page output."""
        # Build grid characters
        grid_chars = []
        for row in range(self.config.size):
            row_chars = []
            for col in range(self.config.size):
                cell = grid.get_cell(row, col)
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
                cell = grid.get_cell(row, col)
                if cell.number:
                    numbers[(row, col)] = cell.number

        # Create CrosswordData
        data = CrosswordData(
            title=f"{self.config.topic} Crossword",
            author=self.config.author,
            size=self.config.size,
            grid=grid_chars,
            numbers=numbers,
            across_clues=clues["across"],
            down_clues=clues["down"],
            theme=self.config.topic,
            difficulty=self.config.difficulty.title()
        )

        # Render
        output_dir = self.config.output.directory
        os.makedirs(output_dir, exist_ok=True)

        renderer = CrosswordPageRenderer()
        base_name = self.config.topic.lower().replace(" ", "_")[:20]

        return renderer.render_all_pages(data, output_dir, base_name)

    def _export_yaml(
        self,
        grid: Grid,
        solution: Dict[WordSlot, str],
        clues: Dict
    ) -> Optional[str]:
        """Export puzzle to YAML intermediate format."""
        if not HAS_YAML_EXPORTER:
            return None

        try:
            exporter = YAMLExporter()

            output_dir = self.config.output.directory
            base_name = self.config.topic.lower().replace(" ", "_")[:20]
            yaml_path = os.path.join(output_dir, f"{base_name}_puzzle.yaml")

            # Build stats
            elapsed = time.time() - self.start_time
            stats = {
                'total_ai_calls': self.ai.stats.get('api_calls', 0),
                'pattern_match_calls': self._csp_stats.get('words_requested', 0),
                'clue_generation_calls': 0,  # TODO: Track separately
                'word_list_calls': 1 if self.ai.is_available() else 0,
                'theme_development_calls': 0,
                'generation_time_seconds': elapsed,
                'backtracks': self._csp_stats.get('backtracks', 0),
                'ac3_revisions': self._csp_stats.get('ac3_revisions', 0),
            }

            return exporter.save(
                grid=grid,
                solution=solution,
                clues=clues,
                title=self.config.topic,
                author=self.config.author,
                path=yaml_path,
                difficulty=self.config.difficulty,
                puzzle_type=self.config.puzzle_type,
                stats=stats,
            )
        except Exception as e:
            self.logger.warning(f"Could not export YAML: {e}")
            return None


def main():
    """Main entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()

    try:
        # Load configuration
        config = load_config(args)

        # Handle dry-run
        if hasattr(args, 'dry_run') and args.dry_run:
            print("Configuration valid:")
            print(f"  Topic: {config.topic}")
            print(f"  Size: {config.size}")
            print(f"  Difficulty: {config.difficulty}")
            print(f"  Puzzle Type: {config.puzzle_type}")
            print(f"  Max AI Callbacks: {config.generation.max_ai_callbacks}")
            print(f"  Output Directory: {config.output.directory}")
            return

        # Generate puzzle
        generator = CrosswordGenerator(config)
        generator.generate()

    except ConfigValidationError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nGeneration cancelled.")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
