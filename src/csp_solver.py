"""
Constraint Satisfaction Problem solver for crossword puzzles.
Uses AC-3 algorithm with backtracking and heuristics.
"""

import sys
import time
from typing import List, Dict, Set, Optional, Tuple, Callable
from copy import deepcopy
from collections import defaultdict

from models import Grid, WordSlot, Direction, matches_pattern, ThemedWord


class CrosswordCSP:
    """
    CSP solver for crossword puzzles.

    Variables: WordSlots (each slot where a word goes)
    Domains: Possible words for each slot
    Constraints:
        - Overlapping slots must have matching letters
        - All words must be different
    """

    def __init__(
        self,
        grid: Grid,
        word_list: List[str],
        word_generator: Optional[Callable[[str, int], List[str]]] = None,
        verbose: bool = True
    ):
        """
        Initialize the CSP solver.

        Args:
            grid: The crossword grid with black squares placed
            word_list: Initial list of available words
            word_generator: Optional function to generate words matching a pattern
                           Signature: (pattern: str, count: int) -> List[str]
                           This is called when a slot has no valid words.
            verbose: Whether to print progress information
        """
        self.grid = grid
        self.word_generator = word_generator
        self.verbose = verbose
        self._last_progress_time = time.time()
        self._progress_interval = 2.0  # Print progress every 2 seconds

        # Find all word slots
        self.variables = grid.find_word_slots()

        # Build word lists by length
        self.words_by_length: Dict[int, Set[str]] = defaultdict(set)
        for word in word_list:
            word = word.upper().strip()
            if len(word) >= 3:
                self.words_by_length[len(word)].add(word)

        # Initialize domains (possible words for each slot)
        self.domains: Dict[WordSlot, Set[str]] = {}
        for slot in self.variables:
            self.domains[slot] = set(self.words_by_length[slot.length])

        # Build constraint graph (which slots overlap)
        self.neighbors: Dict[WordSlot, List[Tuple[WordSlot, int, int]]] = defaultdict(list)
        self._build_constraint_graph()

        # Track used words (for uniqueness constraint)
        self.used_words: Set[str] = set()

        # Track statistics
        self.stats = {
            "backtracks": 0,
            "ac3_revisions": 0,
            "words_requested": 0,
            "ai_words_added": 0,
            "assignments_tried": 0,
            "start_time": time.time()
        }

        if self.verbose:
            self._log(f"CSP initialized: {len(self.variables)} slots, "
                     f"{sum(len(d) for d in self.domains.values())} total domain values")

    def _log(self, message: str):
        """Print a log message with timestamp."""
        if self.verbose:
            elapsed = time.time() - self.stats["start_time"]
            print(f"   [{elapsed:6.1f}s] {message}")
            sys.stdout.flush()

    def _maybe_log_progress(self, assignment: Dict[WordSlot, str]):
        """Log progress periodically during search."""
        now = time.time()
        if now - self._last_progress_time >= self._progress_interval:
            self._last_progress_time = now
            filled = len(assignment)
            total = len(self.variables)
            pct = (filled / total) * 100 if total > 0 else 0
            bt = self.stats["backtracks"]
            tried = self.stats["assignments_tried"]
            self._log(f"Progress: {filled}/{total} slots ({pct:.0f}%) | "
                     f"Tried: {tried} | Backtracks: {bt}")

    def _build_constraint_graph(self):
        """Build graph of overlapping word slots."""
        for i, slot1 in enumerate(self.variables):
            for slot2 in self.variables[i+1:]:
                overlap = slot1.overlaps_with(slot2)
                if overlap:
                    idx1, idx2 = overlap
                    self.neighbors[slot1].append((slot2, idx1, idx2))
                    self.neighbors[slot2].append((slot1, idx2, idx1))
    
    def enforce_node_consistency(self):
        """
        Enforce node consistency - remove words that don't match
        the current pattern in the grid.
        """
        for slot in self.variables:
            pattern = slot.get_pattern(self.grid)
            if '.' not in pattern:
                # Slot is already filled
                self.domains[slot] = {pattern}
            else:
                # Filter domain by pattern
                self.domains[slot] = {
                    word for word in self.domains[slot]
                    if matches_pattern(word, pattern)
                }
    
    def revise(self, slot_x: WordSlot, slot_y: WordSlot) -> bool:
        """
        Make slot_x arc-consistent with slot_y.
        Remove values from domain of slot_x that have no valid pairing in slot_y.
        
        Returns True if domain was revised.
        """
        revised = False
        
        # Find overlap between slots
        overlap = slot_x.overlaps_with(slot_y)
        if not overlap:
            return False
        
        idx_x, idx_y = overlap
        
        # Check each word in x's domain
        words_to_remove = set()
        for word_x in self.domains[slot_x]:
            # Check if there's any word in y's domain that's compatible
            char_needed = word_x[idx_x]
            has_support = any(
                word_y[idx_y] == char_needed 
                for word_y in self.domains[slot_y]
                if word_y != word_x  # Words must be different
            )
            
            if not has_support:
                words_to_remove.add(word_x)
                revised = True
        
        self.domains[slot_x] -= words_to_remove
        self.stats["ac3_revisions"] += len(words_to_remove)
        
        return revised
    
    def ac3(self, arcs: Optional[List[Tuple[WordSlot, WordSlot]]] = None, log_initial: bool = False) -> bool:
        """
        AC-3 algorithm to enforce arc consistency.

        Args:
            arcs: Initial queue of arcs to process. If None, use all arcs.
            log_initial: Whether to log initial AC-3 progress

        Returns:
            True if arc consistency achieved, False if domain became empty.
        """
        if arcs is None:
            # Start with all arcs
            queue = []
            for slot in self.variables:
                for neighbor, _, _ in self.neighbors[slot]:
                    queue.append((slot, neighbor))
            if log_initial and self.verbose:
                self._log(f"AC-3 starting with {len(queue)} arcs")
        else:
            queue = list(arcs)

        iterations = 0
        last_log = time.time()

        while queue:
            slot_x, slot_y = queue.pop(0)
            iterations += 1

            # Log progress every 2 seconds during initial AC-3
            if log_initial and self.verbose and time.time() - last_log > 2.0:
                last_log = time.time()
                total_domain = sum(len(d) for d in self.domains.values())
                self._log(f"AC-3: {len(queue)} arcs remaining, "
                         f"{total_domain} total domain values, "
                         f"{self.stats['ac3_revisions']} revisions")

            if self.revise(slot_x, slot_y):
                if len(self.domains[slot_x]) == 0:
                    # Try to get more words from AI if available
                    if self.word_generator:
                        pattern = slot_x.get_pattern(self.grid)
                        self.stats["words_requested"] += 1

                        if self.verbose:
                            self._log(f"Empty domain for {slot_x.direction.name} "
                                     f"{slot_x.number} ({slot_x.length} letters), "
                                     f"pattern: {pattern}")

                        new_words = self.word_generator(pattern, 20)

                        if new_words:
                            # Filter to words not already used
                            valid_new = [w for w in new_words
                                        if w.upper() not in self.used_words]

                            if valid_new:
                                self.domains[slot_x] = set(valid_new)
                                self.words_by_length[slot_x.length].update(valid_new)
                                self.stats["ai_words_added"] += len(valid_new)
                                if self.verbose:
                                    self._log(f"AI provided {len(valid_new)} new words")
                            else:
                                return False
                        else:
                            return False
                    else:
                        return False

                # Add arcs from neighbors back to queue
                for neighbor, _, _ in self.neighbors[slot_x]:
                    if neighbor != slot_y:
                        queue.append((neighbor, slot_x))

        if log_initial and self.verbose:
            total_domain = sum(len(d) for d in self.domains.values())
            self._log(f"AC-3 complete: {iterations} iterations, "
                     f"{total_domain} domain values remaining")

        return True
    
    def select_unassigned_variable(
        self, 
        assignment: Dict[WordSlot, str]
    ) -> Optional[WordSlot]:
        """
        Select next variable to assign using MRV heuristic.
        Ties broken by degree heuristic (most constraints).
        """
        unassigned = [v for v in self.variables if v not in assignment]
        
        if not unassigned:
            return None
        
        # Sort by: 1) smallest domain (MRV), 2) most neighbors (degree)
        return min(
            unassigned,
            key=lambda v: (len(self.domains[v]), -len(self.neighbors[v]))
        )
    
    def order_domain_values(
        self, 
        slot: WordSlot, 
        assignment: Dict[WordSlot, str]
    ) -> List[str]:
        """
        Order domain values using Least Constraining Value heuristic.
        Try values that rule out the fewest choices for neighbors first.
        """
        def count_conflicts(word: str) -> int:
            conflicts = 0
            for neighbor, idx_self, idx_neighbor in self.neighbors[slot]:
                if neighbor in assignment:
                    continue
                char = word[idx_self]
                # Count how many words in neighbor's domain would be eliminated
                for neighbor_word in self.domains[neighbor]:
                    if neighbor_word[idx_neighbor] != char:
                        conflicts += 1
            return conflicts
        
        return sorted(self.domains[slot], key=count_conflicts)
    
    def is_consistent(
        self, 
        slot: WordSlot, 
        word: str, 
        assignment: Dict[WordSlot, str]
    ) -> bool:
        """Check if assigning word to slot is consistent with current assignment."""
        # Check word isn't already used
        if word in assignment.values():
            return False
        
        # Check overlaps with assigned neighbors
        for neighbor, idx_self, idx_neighbor in self.neighbors[slot]:
            if neighbor in assignment:
                neighbor_word = assignment[neighbor]
                if word[idx_self] != neighbor_word[idx_neighbor]:
                    return False
        
        return True
    
    def backtrack(
        self,
        assignment: Optional[Dict[WordSlot, str]] = None,
        use_inference: bool = True
    ) -> Optional[Dict[WordSlot, str]]:
        """
        Backtracking search with optional AC-3 inference.

        Returns complete assignment if solution found, None otherwise.
        """
        if assignment is None:
            assignment = {}

        # Log progress periodically
        self._maybe_log_progress(assignment)

        # Check if complete
        if len(assignment) == len(self.variables):
            if self.verbose:
                self._log(f"Solution found! All {len(self.variables)} slots filled.")
            return assignment

        # Select next variable
        slot = self.select_unassigned_variable(assignment)
        if slot is None:
            return assignment

        domain_size = len(self.domains[slot])

        # Try each value in domain
        for word in self.order_domain_values(slot, assignment):
            self.stats["assignments_tried"] += 1

            if self.is_consistent(slot, word, assignment):
                # Make assignment
                assignment[slot] = word

                # Save domains for backtracking
                saved_domains = deepcopy(self.domains) if use_inference else None

                # Apply inference (AC-3) if enabled
                if use_inference:
                    self.domains[slot] = {word}
                    # Run AC-3 on arcs from neighbors to this slot
                    arcs = [(neighbor, slot) for neighbor, _, _ in self.neighbors[slot]]
                    inference_ok = self.ac3(arcs)
                else:
                    inference_ok = True

                if inference_ok:
                    result = self.backtrack(assignment, use_inference)
                    if result is not None:
                        return result

                # Backtrack
                self.stats["backtracks"] += 1
                del assignment[slot]

                if use_inference:
                    self.domains = saved_domains

        return None
    
    def solve(self, use_inference: bool = True) -> Optional[Dict[WordSlot, str]]:
        """
        Solve the crossword puzzle.

        Args:
            use_inference: Whether to use AC-3 inference during search

        Returns:
            Dictionary mapping WordSlots to words, or None if no solution
        """
        if self.verbose:
            self._log("Starting solve...")
            self._log("Enforcing node consistency...")

        # Initial constraint propagation
        self.enforce_node_consistency()

        if self.verbose:
            total_domain = sum(len(d) for d in self.domains.values())
            self._log(f"After node consistency: {total_domain} domain values")
            self._log("Running initial AC-3...")

        if not self.ac3(log_initial=True):
            if self.verbose:
                self._log("AC-3 failed - no solution possible")
            return None

        if self.verbose:
            total_domain = sum(len(d) for d in self.domains.values())
            self._log(f"Starting backtracking search...")
            # Show domain sizes for each slot
            for slot in sorted(self.variables, key=lambda s: len(self.domains[s])):
                d_size = len(self.domains[slot])
                if d_size < 100:  # Only show small domains
                    self._log(f"  {slot.direction.name} {slot.number} "
                             f"({slot.length} letters): {d_size} candidates")

        # Run backtracking search
        result = self.backtrack(use_inference=use_inference)

        if self.verbose:
            elapsed = time.time() - self.stats["start_time"]
            if result:
                self._log(f"Solved in {elapsed:.1f}s with "
                         f"{self.stats['backtracks']} backtracks, "
                         f"{self.stats['assignments_tried']} assignments tried")
            else:
                self._log(f"No solution found after {elapsed:.1f}s, "
                         f"{self.stats['backtracks']} backtracks")

        return result
    
    def apply_solution(self, solution: Dict[WordSlot, str]):
        """Apply a solution to the grid."""
        for slot, word in solution.items():
            for i, (row, col) in enumerate(slot.cells):
                self.grid.set_letter(row, col, word[i])


def create_sample_word_list() -> List[str]:
    """Create a sample word list for testing."""
    return [
        # 3-letter words
        "ACE", "ACT", "ADD", "AGE", "AID", "AIM", "AIR", "ALL", "AND", "ANT",
        "APE", "ARC", "ARE", "ARK", "ARM", "ART", "ASH", "ATE", "AWE", "AXE",
        "BAD", "BAG", "BAN", "BAR", "BAT", "BED", "BEE", "BET", "BIG", "BIT",
        "BOW", "BOX", "BOY", "BUD", "BUG", "BUN", "BUS", "BUT", "BUY", "CAB",
        "CAN", "CAP", "CAR", "CAT", "COW", "CRY", "CUP", "CUT", "DAY", "DEN",
        "DEW", "DID", "DIG", "DIM", "DOC", "DOE", "DOG", "DOT", "DRY", "DUE",
        "EAR", "EAT", "EEL", "EGG", "ELF", "ELK", "ELM", "EMU", "END", "ERA",
        "EVE", "EWE", "EYE", "FAN", "FAR", "FAT", "FAX", "FED", "FEE", "FEW",
        "FIG", "FIN", "FIT", "FIX", "FLY", "FOB", "FOE", "FOG", "FOR", "FOX",
        "FUN", "FUR", "GAP", "GAS", "GEL", "GEM", "GET", "GNU", "GOB", "GOD",
        
        # 4-letter words
        "ABLE", "ACID", "AGED", "ALSO", "AREA", "ARMY", "AWAY", "BABY", "BACK",
        "BALL", "BAND", "BANK", "BASE", "BATH", "BEAR", "BEAT", "BEEN", "BELL",
        "BELT", "BEND", "BENT", "BEST", "BIRD", "BLOW", "BLUE", "BOAT", "BODY",
        "BOLD", "BONE", "BOOK", "BORN", "BOSS", "BOTH", "BOWL", "BULK", "BURN",
        "BUSY", "CAKE", "CALL", "CALM", "CAME", "CAMP", "CARD", "CARE", "CASE",
        "CASH", "CAST", "CAVE", "CELL", "CHEF", "CITY", "CLUB", "COAL", "COAT",
        "CODE", "COLD", "COME", "COOK", "COOL", "COPE", "COPY", "CORE", "COST",
        "CREW", "CROP", "DARK", "DATA", "DATE", "DAWN", "DAYS", "DEAD", "DEAL",
        
        # 5-letter words
        "ABOUT", "ABOVE", "ACTOR", "ADAPT", "ADMIT", "ADOPT", "ADULT", "AFTER",
        "AGAIN", "AGENT", "AGREE", "AHEAD", "ALARM", "ALBUM", "ALERT", "ALIEN",
        "ALIGN", "ALIKE", "ALIVE", "ALLOW", "ALONE", "ALONG", "ALTER", "AMONG",
        "ANGEL", "ANGER", "ANGLE", "ANGRY", "APART", "APPLE", "APPLY", "ARENA",
        "ARGUE", "ARISE", "ARMOR", "ARRAY", "ARROW", "ASSET", "AWARD", "AWARE",
        "BADLY", "BASIC", "BASIS", "BEACH", "BEGAN", "BEGIN", "BEING", "BELOW",
        "BENCH", "BIRTH", "BLACK", "BLADE", "BLAME", "BLANK", "BLAST", "BLEND",
        "BLESS", "BLIND", "BLOCK", "BLOOD", "BOARD", "BOOST", "BOUND", "BRAIN",
        
        # 6-letter words
        "ACCEPT", "ACCESS", "ACROSS", "ACTION", "ACTIVE", "ACTUAL", "ADVICE",
        "AFFAIR", "AFFECT", "AFFORD", "AFRAID", "AGENCY", "AGENDA", "ALMOST",
        "ALWAYS", "AMOUNT", "ANIMAL", "ANNUAL", "ANSWER", "ANYONE", "ANYWAY",
        "APPEAL", "APPEAR", "AROUND", "ARTIST", "ASPECT", "ASSERT", "ASSESS",
        "ASSIGN", "ASSIST", "ASSUME", "ATTACK", "ATTEND", "AUTHOR", "BACKED",
        "BANKER", "BATTLE", "BEAUTY", "BECAME", "BECOME", "BEFORE", "BEHALF",
        "BEHIND", "BELIEF", "BELONG", "BERLIN", "BETTER", "BEYOND", "BORDER",
        "BORROW", "BOTTLE", "BOTTOM", "BOUGHT", "BRANCH", "BREATH", "BRIDGE",
        
        # 7+ letter words
        "ABILITY", "ABSENCE", "ACADEMY", "ACCOUNT", "ACHIEVE", "ACQUIRE",
        "ACTIVITY", "ACTUALLY", "ADDITION", "ADEQUATE", "ADVANCED", "ADVISORY",
        "ADVOCATE", "AFFECTED", "AFTERNOON", "AGREEMENT", "ALEXANDER", "ALLIANCE",
        "ALTHOUGH", "ALUMINUM", "ANALYSIS", "ANNOUNCE", "APPARENT", "APPROACH",
        "APPROVAL", "ARGUMENT", "ARTISTIC", "ASSEMBLY", "ASSUMING", "ATHLETIC",
        "ATTACHED", "ATTORNEY", "AUDIENCE", "AVAILABLE", "BACHELOR", "BACKWARD",
        "BACTERIA", "BALANCED", "BASEBALL", "BATHROOM", "BECOMING", "BEHAVIOR",
        "BELONGED", "BENEFITS", "BENJAMIN", "BILLION", "BIRTHDAY", "BOUNDARY",
    ]
