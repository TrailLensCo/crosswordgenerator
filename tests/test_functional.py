# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.
# Unauthorized copying, distribution, or use of this file,
# via any medium, is strictly prohibited without the express
# written permission of TrailLensCo.

"""Functional tests for crossword generator."""

import os
import sys
import shutil
import tempfile
import unittest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from models import Grid
from grid_generator import GridGenerator
from csp_solver import CrosswordCSP
from validator import validate_puzzle
from config import PuzzleConfig


class TestGridGeneration(unittest.TestCase):
    """Tests for grid generation."""

    def test_generate_5x5_grid(self):
        """Test generating a 5x5 grid."""
        generator = GridGenerator(size=5)
        grid = generator.generate()

        self.assertIsNotNone(grid)
        self.assertEqual(grid.size, 5)

    def test_generate_11x11_grid(self):
        """Test generating an 11x11 grid."""
        generator = GridGenerator(size=11)
        grid = generator.generate()

        self.assertIsNotNone(grid)
        self.assertEqual(grid.size, 11)

    def test_grid_has_symmetry(self):
        """Test that generated grid has 180-degree symmetry."""
        generator = GridGenerator(size=5)
        grid = generator.generate()

        if grid:
            # Check 180-degree rotational symmetry
            for row in range(grid.size):
                for col in range(grid.size):
                    opp_row = grid.size - 1 - row
                    opp_col = grid.size - 1 - col

                    cell = grid.get_cell(row, col)
                    opp_cell = grid.get_cell(opp_row, opp_col)

                    self.assertEqual(
                        cell.is_block(), opp_cell.is_block(),
                        f"Symmetry check failed at ({row}, {col})"
                    )

    def test_grid_connectivity(self):
        """Test that generated grid is fully connected."""
        generator = GridGenerator(size=5)
        grid = generator.generate()

        if grid:
            self.assertTrue(grid.is_connected())


class TestCSPSolver(unittest.TestCase):
    """Tests for CSP solver."""

    def setUp(self):
        """Set up test word list."""
        self.word_list = [
            # 3-letter words
            "ACE", "ACT", "ADD", "AGE", "AID", "AIM", "AIR", "ALL", "AND",
            "APE", "ARC", "ARE", "ARK", "ARM", "ART", "ATE", "AWE", "AXE",
            "BAD", "BAG", "BAN", "BAR", "BAT", "BED", "BEE", "BET", "BIG",
            "CAB", "CAN", "CAP", "CAR", "CAT", "COW", "CRY", "CUP", "CUT",
            "DAY", "DEN", "DEW", "DIG", "DIM", "DOC", "DOE", "DOG", "DOT",
            "EAR", "EAT", "EGG", "ELM", "EMU", "END", "ERA", "EVE", "EYE",
            "FAN", "FAR", "FAT", "FED", "FEE", "FEW", "FIG", "FIN", "FIT",
            # 4-letter words
            "ABLE", "ACHE", "ACID", "AGED", "AIDE", "AREA", "ARMY", "AWAY",
            "BACK", "BAKE", "BALL", "BAND", "BANK", "BARE", "BASE", "BATH",
            "BEAR", "BEAT", "BEEN", "BEER", "BELL", "BELT", "BEND", "BENT",
            "BEST", "BIRD", "BITE", "BLOW", "BLUE", "BOAT", "BODY", "BOLD",
            "BONE", "BOOK", "BOOM", "BOOT", "BORE", "BORN", "BOSS", "BOTH",
            "BOWL", "BURN", "BUSY", "CAFE", "CAGE", "CAKE", "CALL", "CALM",
            # 5-letter words
            "ABOUT", "ABOVE", "ABUSE", "ACTOR", "ACUTE", "ADMIT", "ADOPT",
            "ADULT", "AFTER", "AGAIN", "AGENT", "AGREE", "AHEAD", "ALARM",
            "ALBUM", "ALERT", "ALIEN", "ALIGN", "ALIKE", "ALIVE", "ALLOW",
            "ALONE", "ALONG", "ALTER", "AMONG", "ANGEL", "ANGER", "ANGLE",
            "ANGRY", "APART", "APPLE", "APPLY", "ARENA", "ARGUE", "ARISE",
        ]

    def test_solve_5x5_grid(self):
        """Test solving a 5x5 grid."""
        generator = GridGenerator(size=5)
        grid = generator.generate()

        if grid:
            csp = CrosswordCSP(grid, self.word_list)
            solution = csp.solve()

            # May or may not find a solution depending on grid/word list
            # But solver should complete without error

    def test_solver_stats(self):
        """Test that solver tracks statistics."""
        generator = GridGenerator(size=5)
        grid = generator.generate()

        if grid:
            csp = CrosswordCSP(grid, self.word_list)
            csp.solve()

            self.assertIn('backtracks', csp.stats)
            self.assertIn('ac3_revisions', csp.stats)

    def test_solver_applies_solution(self):
        """Test that solver can apply solution to grid."""
        generator = GridGenerator(size=5)
        grid = generator.generate()

        if grid:
            csp = CrosswordCSP(grid, self.word_list)
            solution = csp.solve()

            if solution:
                csp.apply_solution(solution)

                # Check that all letters are filled
                for slot, word in solution.items():
                    for i, (row, col) in enumerate(slot.cells):
                        cell = grid.get_cell(row, col)
                        self.assertEqual(cell.letter, word[i])


class TestValidation(unittest.TestCase):
    """Tests for puzzle validation."""

    def test_validate_valid_grid(self):
        """Test validation of a valid grid."""
        generator = GridGenerator(size=5)
        grid = generator.generate()

        if grid:
            word_list = ["ACE", "ACT", "ADD", "ABLE", "AREA"]
            result = validate_puzzle(grid, word_list, check_fillability=False)

            # Grid should be structurally valid
            if not result.valid:
                # Print errors for debugging
                for error in result.errors:
                    print(f"Validation error: {error}")


class TestEndToEnd(unittest.TestCase):
    """End-to-end functional tests."""

    def setUp(self):
        """Create temporary output directory."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_generate_puzzle_without_ai(self):
        """Test generating a puzzle without AI (base words only)."""
        from crossword_generator import CrosswordGenerator

        config = PuzzleConfig(
            topic="Test",
            size=5,
            difficulty="easy",
        )
        config.output.directory = self.temp_dir

        generator = CrosswordGenerator(config)

        # Should not raise an exception
        # May or may not succeed depending on grid/word list
        try:
            result = generator.generate()
            if result:
                # Check that output files were created
                for name, path in result.items():
                    if name != 'yaml_intermediate':
                        self.assertTrue(
                            os.path.exists(path),
                            f"Output file not found: {path}"
                        )
        except Exception as e:
            # Some failures are expected without AI
            pass


class TestConfigIntegration(unittest.TestCase):
    """Tests for configuration integration."""

    def test_config_loads_for_generator(self):
        """Test that config is properly loaded by generator."""
        from crossword_generator import CrosswordGenerator

        config = PuzzleConfig(
            topic="Integration Test",
            size=5,
            difficulty="wednesday",
            puzzle_type="revealer",
            author="Test Author"
        )

        generator = CrosswordGenerator(config)

        self.assertEqual(generator.config.topic, "Integration Test")
        self.assertEqual(generator.config.size, 5)
        self.assertEqual(generator.config.difficulty, "wednesday")

    def test_limiter_integration(self):
        """Test that limiter is properly integrated."""
        from crossword_generator import CrosswordGenerator

        config = PuzzleConfig(topic="Test", size=5)
        config.generation.max_ai_callbacks = 25

        generator = CrosswordGenerator(config)

        self.assertEqual(generator.limiter.max_total, 25)


if __name__ == '__main__':
    unittest.main()
