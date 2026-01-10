#!/usr/bin/env python3
"""
AI-Powered Crossword Generator

Generates NYT-style crossword puzzles using:
1. AI (Claude API) for themed word lists, pattern matching, and clues
2. CSP solver with AC-3 for grid filling
3. Validation to ensure puzzle is completeable
4. Multi-page SVG/HTML output

Usage:
    # With API key in environment:
    export ANTHROPIC_API_KEY='your-key'
    python crossword_generator.py --topic "Space Exploration" --size 5
    
    # Or pass API key directly:
    python crossword_generator.py --topic "Movies" --api-key "your-key"
"""

import os
import sys
import argparse
from typing import List, Dict, Optional
from dataclasses import dataclass
from copy import deepcopy

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import Grid, WordSlot, Direction
from csp_solver import CrosswordCSP
from validator import validate_puzzle, ValidationResult
from grid_generator import GridGenerator
from page_renderer import CrosswordPageRenderer, CrosswordData
from ai_word_generator import AIWordGenerator, WordWithClue, create_pattern_word_generator


@dataclass
class GeneratorConfig:
    """Configuration for crossword generation."""
    size: int = 5
    theme: str = "General"
    difficulty: str = "medium"
    author: str = "AI Generator"
    api_key: Optional[str] = None
    max_attempts: int = 3
    output_dir: str = "./output"


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
    """
    
    def __init__(self, config: GeneratorConfig):
        self.config = config
        self.ai = AIWordGenerator(api_key=config.api_key)
        self.word_list: List[str] = []
        self.themed_words: Dict[str, WordWithClue] = {}
        self.solution: Optional[Dict[WordSlot, str]] = None
        
    def generate(self) -> Optional[Dict[str, str]]:
        """
        Generate a complete crossword puzzle.
        
        Returns:
            Dict of output file paths, or None if generation failed
        """
        print("=" * 60)
        print(f"🎯 CROSSWORD GENERATOR")
        print("=" * 60)
        print(f"   Theme: {self.config.theme}")
        print(f"   Size: {self.config.size}x{self.config.size}")
        print(f"   AI Available: {self.ai.is_available()}")
        print()
        
        # Step 1: Generate word list
        print("📝 Step 1: Building word list...")
        self._build_word_list()
        print(f"   ✓ {len(self.word_list)} words available")
        print(f"   ✓ {len(self.themed_words)} themed words with clues")
        print()
        
        # Step 2: Create and validate grid
        print("🔲 Step 2: Creating grid...")
        grid = self._create_grid()
        if grid is None:
            print("   ❌ Failed to create valid grid")
            return None
        print(f"   ✓ Grid created")
        
        # Step 3: Validate structure
        print("\n🔍 Step 3: Validating structure...")
        validation = validate_puzzle(grid, self.word_list, check_fillability=False)
        if not validation.valid:
            print(f"   ❌ Invalid structure:")
            for error in validation.errors:
                print(f"      - {error}")
            return None
        print(f"   ✓ Structure valid")
        print(f"   ✓ {validation.stats['total_words']} word slots")
        print()
        
        # Step 4: Fill grid using CSP
        print("🧩 Step 4: Filling grid with CSP solver...")
        filled_grid, solution = self._fill_grid(grid)
        if solution is None:
            print("   ❌ Could not fill grid")
            return None
        print(f"   ✓ Grid filled successfully!")
        print()
        
        # Step 5: Validate fillability
        print("✅ Step 5: Validating solution...")
        # Solution is already found, just verify
        print(f"   ✓ All {len(solution)} words placed")
        print(f"   ✓ Puzzle is completeable")
        print()
        
        # Step 6: Generate clues
        print("💡 Step 6: Generating clues...")
        clues = self._generate_clues(solution)
        print(f"   ✓ {len(clues['across'])} across clues")
        print(f"   ✓ {len(clues['down'])} down clues")
        print()
        
        # Step 7: Render output
        print("🖼️  Step 7: Rendering output...")
        output_files = self._render_output(filled_grid, solution, clues)
        print(f"   ✓ Generated {len(output_files)} files")
        print()
        
        # Summary
        print("=" * 60)
        print("✨ GENERATION COMPLETE!")
        print("=" * 60)
        print("\n📁 Output files:")
        for name, path in output_files.items():
            print(f"   {name}: {path}")
        
        if self.ai.is_available():
            stats = self.ai.get_stats()
            print(f"\n📊 AI Stats:")
            print(f"   API calls: {stats['api_calls']}")
            print(f"   Words generated: {stats['words_generated']}")
            print(f"   Cache hits: {stats['cache_hits']}")
        
        return output_files
    
    def _build_word_list(self):
        """Build word list from AI and fallback sources."""
        # Get themed words from AI
        if self.ai.is_available():
            themed = self.ai.generate_themed_words(
                self.config.theme,
                count=50,
                min_length=3,
                max_length=self.config.size
            )
            for tw in themed:
                self.word_list.append(tw.word)
                self.themed_words[tw.word] = tw
        
        # Add base word list
        base_words = self._get_base_word_list()
        self.word_list.extend(base_words)
        
        # Deduplicate and filter
        self.word_list = list(set(
            w.upper() for w in self.word_list 
            if 3 <= len(w) <= self.config.size and w.isalpha()
        ))
        
        # Sort by length (longer words first for theme entries)
        self.word_list.sort(key=len, reverse=True)
    
    def _get_base_word_list(self) -> List[str]:
        """Get base crossword word list."""
        # Common crossword words organized by length
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
            "MOVES", "MOVIE", "MUSIC", "Myers", "NAMED", "NAMES", "NEEDS", "NERVE",
            "NEVER", "NEWER", "NEWLY", "NIGHT", "NINTH", "NOISE", "NORTH", "NOTED",
            "NOTES", "NOVEL", "NURSE", "OCCUR", "OCEAN", "OFFER", "OFTEN", "OLIVE",
            "ONSET", "OPERA", "OPTED", "ORBIT", "ORDER", "OTHER", "OUGHT", "OUTER",
            "OWNED", "OWNER", "OXIDE", "OZONE", "PACKS", "PAGES", "PAINT", "PAIRS",
            "PANEL", "PANIC", "PAPER", "PARKS", "PARTS", "PARTY", "PASTA", "PASTE",
            "PATCH", "PATHS", "PAUSE", "PEACE", "PEAKS", "PEARL", "PEERS", "PENNY",
            "PHASE", "PHONE", "PHOTO", "PIANO", "PICKS", "PIECE", "PILOT", "PINCH",
            "PITCH", "PIZZA", "PLACE", "PLAIN", "PLANE", "PLANS", "PLANT", "PLATE",
            "PLAYS", "PLAZA", "PLEAD", "PLOTS", "POEMS", "POINT", "POLAR", "POLES",
            "POLLS", "POOLS", "PORCH", "PORTS", "POSED", "POSTS", "POUND", "POWER",
            "PRESS", "PRICE", "PRIDE", "PRIME", "PRINT", "PRIOR", "PRIZE", "PROBE",
            "PROOF", "PROUD", "PROVE", "PULLS", "PULSE", "PUMPS", "PUNCH", "PUPIL",
            "PURSE", "QUEEN", "QUEST", "QUEUE", "QUICK", "QUIET", "QUITE", "QUOTA",
            "QUOTE", "RACES", "RADAR", "RADIO", "RAGED", "RAIDS", "RAILS", "RAISE",
            "RALLY", "RANCH", "RANGE", "RANKS", "RAPID", "RATED", "RATES", "RATIO",
            "REACH", "REACT", "READS", "READY", "REALM", "REBEL", "REFER", "REIGN",
            "RELAX", "REPLY", "REPUB", "RESET", "RESIN", "RESTS", "RIDER", "RIDGE",
            "RIFLE", "RIGHT", "RIGID", "RINGS", "RISEN", "RISES", "RISKS", "RISKY",
            "RIVAL", "RIVER", "ROADS", "ROBOT", "ROCKS", "ROCKY", "ROLES", "ROMAN",
            "ROOMS", "ROOTS", "ROUGH", "ROUND", "ROUTE", "ROYAL", "RUGBY", "RUINS",
            "RULED", "RULER", "RULES", "RURAL", "SADLY", "SAFER", "SAINT", "SALAD",
            "SALES", "SANDY", "SAUCE", "SAVED", "SAVES", "SCALE", "SCENE", "SCOPE",
            "SCORE", "SEATS", "SEEDS", "SEEKS", "SEEMS", "SEIZE", "SELLS", "SENDS",
            "SENSE", "SERUM", "SERVE", "SETUP", "SEVEN", "SHADE", "SHAKE", "SHALL",
            "SHAME", "SHAPE", "SHARE", "SHARP", "SHEEP", "SHEER", "SHEET", "SHELF",
            "SHELL", "SHIFT", "SHINE", "SHIPS", "SHIRT", "SHOCK", "SHOES", "SHOOK",
            "SHOOT", "SHOPS", "SHORE", "SHORT", "SHOTS", "SHOWN", "SHOWS", "SIDES",
            "SIGHT", "SIGMA", "SIGNS", "SILLY", "SIMON", "SINCE", "SITES", "SIXTH",
            "SIXTY", "SIZED", "SIZES", "SKILL", "SKINS", "SLAVE", "SLEEP", "SLICE",
            "SLIDE", "SLOPE", "SLOWS", "SMALL", "SMART", "SMELL", "SMILE", "SMITH",
            "SMOKE", "SNAKE", "SOLID", "SOLVE", "SONGS", "SORRY", "SORTS", "SOULS",
            "SOUND", "SOUTH", "SPACE", "SPARE", "SPARK", "SPEAK", "SPEED", "SPELL",
            "SPEND", "SPENT", "SPILL", "SPINE", "SPLIT", "SPOKE", "SPORT", "SPOTS",
            "SPRAY", "SQUAD", "STACK", "STAFF", "STAGE", "STAKE", "STAMP", "STAND",
            "STARK", "STARS", "START", "STATE", "STAYS", "STEAL", "STEAM", "STEEL",
            "STEEP", "STEMS", "STEPS", "STICK", "STIFF", "STILL", "STOCK", "STONE",
            "STOOD", "STOPS", "STORE", "STORM", "STORY", "STOVE", "STRAP", "STRAW",
            "STRIP", "STUCK", "STUFF", "STYLE", "SUGAR", "SUITE", "SUITS", "SUPER",
            "SURGE", "SWEET", "SWEPT", "SWIFT", "SWING", "SWISS", "SWORD", "SWUNG",
            "TABLE", "TAKEN", "TAKES", "TALES", "TALKS", "TANKS", "TAPES", "TASKS",
            "TASTE", "TAXES", "TEACH", "TEAMS", "TEARS", "TEETH", "TELLS", "TEMPO",
            "TENDS", "TENTH", "TERMS", "TESTS", "TEXAS", "TEXTS", "THANK", "THEFT",
            "THEME", "THERE", "THESE", "THICK", "THIEF", "THING", "THINK", "THIRD",
            "THOSE", "THREE", "THREW", "THROW", "THUMB", "TIGER", "TIGHT", "TIMES",
            "TINY", "TIRED", "TITLE", "TODAY", "TOKEN", "TONES", "TOOLS", "TOOTH",
            "TOPIC", "TOTAL", "TOUCH", "TOUGH", "TOURS", "TOWER", "TOWNS", "TRACE",
            "TRACK", "TRADE", "TRAIL", "TRAIN", "TRAIT", "TRASH", "TREAT", "TREES",
            "TREND", "TRIAL", "TRIBE", "TRICK", "TRIED", "TRIES", "TRIPS", "TROOP",
            "TRUCK", "TRULY", "TRUNK", "TRUST", "TRUTH", "TUBES", "TUMOR", "TUNED",
            "TURNS", "TWICE", "TWINS", "TWIST", "TYPES", "UNCLE", "UNDER", "UNION",
            "UNITS", "UNITY", "UNTIL", "UPPER", "UPSET", "URBAN", "URGED", "USAGE",
            "USERS", "USING", "USUAL", "VALID", "VALUE", "VALVE", "VAPOR", "VAULT",
            "VENUE", "VERGE", "VIDEO", "VIEWS", "VIRUS", "VISIT", "VITAL", "VOCAL",
            "VOICE", "VOTES", "WAGES", "WAGON", "WAIST", "WALKS", "WALLS", "WANTS",
            "WASTE", "WATCH", "WATER", "WAVES", "WEEKS", "WEIGH", "WEIRD", "WELLS",
            "WHALE", "WHEAT", "WHEEL", "WHERE", "WHICH", "WHILE", "WHITE", "WHOLE",
            "WHOSE", "WIDER", "WIDTH", "WINDS", "WINES", "WINGS", "WIRED", "WIRES",
            "WITCH", "WIVES", "WOMAN", "WOMEN", "WOODS", "WORDS", "WORKS", "WORLD",
            "WORRY", "WORSE", "WORST", "WORTH", "WOULD", "WOUND", "WRIST", "WRITE",
            "WRONG", "WROTE", "YARDS", "YEARS", "YIELD", "YOUNG", "YOURS", "YOUTH",
            "ZONES",
        ])
        
        return words
    
    def _create_grid(self) -> Optional[Grid]:
        """Create a valid grid pattern."""
        generator = GridGenerator(size=self.config.size)
        
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
    
    def _fill_grid(self, grid: Grid) -> tuple[Grid, Optional[Dict[WordSlot, str]]]:
        """Fill grid using CSP solver with AI word requests."""
        # Create word generator function for CSP
        word_gen = None
        if self.ai.is_available():
            word_gen = create_pattern_word_generator(self.ai, self.config.theme)
        
        # Create and run CSP solver
        csp = CrosswordCSP(grid, self.word_list, word_generator=word_gen)
        
        solution = csp.solve(use_inference=True)
        
        if solution:
            # Apply solution to grid
            csp.apply_solution(solution)
            
            # Store stats
            self._csp_stats = csp.stats
            
            return grid, solution
        
        return grid, None
    
    def _generate_clues(self, solution: Dict[WordSlot, str]) -> Dict[str, List]:
        """Generate clues for all words using AI."""
        across_clues = []
        down_clues = []
        
        # Get all words
        words = list(solution.values())
        
        # Generate clues in batch if AI is available
        if self.ai.is_available():
            # Separate themed words (already have clues) from others
            needs_clues = [w for w in words if w not in self.themed_words]
            clues = self.ai.generate_clues_batch(needs_clues, self.config.difficulty)
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
            title=f"{self.config.theme} Crossword",
            author=self.config.author,
            size=self.config.size,
            grid=grid_chars,
            numbers=numbers,
            across_clues=clues["across"],
            down_clues=clues["down"],
            theme=self.config.theme,
            difficulty=self.config.difficulty.title()
        )
        
        # Render
        os.makedirs(self.config.output_dir, exist_ok=True)
        
        renderer = CrosswordPageRenderer()
        base_name = self.config.theme.lower().replace(" ", "_")[:20]
        
        return renderer.render_all_pages(data, self.config.output_dir, base_name)


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
        default=5,
        choices=[3, 5, 7, 9, 11, 13, 15],
        help="Grid size (default: 5)"
    )
    parser.add_argument(
        "--difficulty", "-d",
        default="medium",
        choices=["easy", "medium", "hard"],
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
    parser.add_argument(
        "--api-key",
        default=None,
        help="Anthropic API key (or set ANTHROPIC_API_KEY env var)"
    )
    
    args = parser.parse_args()
    
    config = GeneratorConfig(
        size=args.size,
        theme=args.topic,
        difficulty=args.difficulty,
        author=args.author,
        api_key=args.api_key,
        output_dir=args.output
    )
    
    generator = CrosswordGenerator(config)
    generator.generate()


if __name__ == "__main__":
    main()
