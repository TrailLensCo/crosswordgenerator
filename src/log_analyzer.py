"""
Log Analyzer for Crossword Generator.

Parses generation logs and uses AI to create comprehensive analysis reports.
"""
#
# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.
# Unauthorized copying, distribution, or use of this file,
# via any medium, is strictly prohibited without the express
# written permission of TrailLensCo.

import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from prompt_loader import PromptLoader
    HAS_PROMPT_LOADER = True
except ImportError:
    HAS_PROMPT_LOADER = False
    PromptLoader = None


class LogAnalyzer:
    """Analyzes crossword generation logs and creates AI-powered reports."""

    def __init__(self, ai_generator, logger: Optional[logging.Logger] = None):
        """
        Initialize the log analyzer.

        Args:
            ai_generator: AIWordGenerator instance with API access
            logger: Logger instance (uses module logger if not provided)
        """
        self.ai = ai_generator
        self.logger = logger if logger else logging.getLogger(__name__)

    def analyze_log(
        self,
        log_path: str,
        output_dir: str
    ) -> Optional[str]:
        """
        Analyze a log file and generate a markdown report.

        Args:
            log_path: Path to the log file to analyze
            output_dir: Directory where report will be saved

        Returns:
            Path to the generated report, or None if failed
        """
        if not self.ai.is_available():
            self.logger.warning("AI not available for log analysis")
            return None

        try:
            # Parse the log file
            metrics, events, warnings = self._parse_log(log_path)

            if not metrics and not events:
                self.logger.warning("No meaningful data extracted from log file")
                return None

            # Load prompt template if available
            prompt_data = self._get_prompt_template()

            # Generate analysis using AI
            report_content = self._generate_report(
                metrics=metrics,
                events=events,
                warnings=warnings,
                prompt_data=prompt_data
            )

            if not report_content:
                self.logger.error("Failed to generate report content")
                return None

            # Save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"generation_report_{timestamp}.md"
            report_path = os.path.join(output_dir, report_filename)

            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)

            self.logger.info(f"Analysis report saved to {report_path}")
            return report_path

        except Exception as e:
            self.logger.error(f"Error analyzing log: {e}", exc_info=True)
            return None

    def _parse_log(
        self,
        log_path: str
    ) -> Tuple[Dict[str, any], List[str], List[str]]:
        """
        Parse log file to extract metrics, events, and warnings.

        Args:
            log_path: Path to log file

        Returns:
            Tuple of (metrics dict, events list, warnings list)
        """
        metrics = {}
        events = []
        warnings = []

        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()

                    # Extract key metrics
                    if "Total Runtime" in line or "Generation time" in line:
                        match = re.search(r'([\d.]+)\s*seconds?', line)
                        if match:
                            metrics['runtime_seconds'] = float(match.group(1))

                    elif "AI Stats:" in line:
                        # Next lines contain AI stats
                        events.append(line)

                    elif "API calls:" in line:
                        match = re.search(r'(\d+)', line)
                        if match:
                            metrics['api_calls'] = int(match.group(1))

                    elif "Tokens used:" in line or "Token Usage:" in line:
                        match = re.search(r'(\d+)', line)
                        if match:
                            metrics['tokens_used'] = int(match.group(1))

                    elif "Backtracks:" in line:
                        match = re.search(r'(\d+)', line)
                        if match:
                            metrics['backtracks'] = int(match.group(1))

                    elif "AC-3 revisions:" in line:
                        match = re.search(r'(\d+)', line)
                        if match:
                            metrics['ac3_revisions'] = int(match.group(1))

                    elif "words available" in line:
                        match = re.search(r'(\d+)\s*words available', line)
                        if match:
                            metrics['words_available'] = int(match.group(1))

                    elif "word slots" in line:
                        match = re.search(r'(\d+)\s*word slots', line)
                        if match:
                            metrics['word_slots'] = int(match.group(1))

                    # Capture step events
                    elif re.match(r'Step \d+:', line):
                        events.append(line)

                    elif "GENERATION COMPLETE" in line:
                        events.append("✓ Generation completed successfully")

                    # Capture warnings and errors
                    elif "WARNING" in line or "WARNING -" in line:
                        warnings.append(line)

                    elif "ERROR" in line or "ERROR -" in line:
                        warnings.append(f"🔴 {line}")

                    elif "CRITICAL" in line:
                        warnings.append(f"🚨 {line}")

                    elif "X Failed" in line or "Could not" in line:
                        warnings.append(f"⚠️  {line}")

        except Exception as e:
            self.logger.error(f"Error parsing log file: {e}")

        return metrics, events, warnings

    def _get_prompt_template(self) -> Optional[Dict]:
        """Load prompt template from prompts.yaml if available."""
        if not HAS_PROMPT_LOADER or not hasattr(self.ai, 'prompt_loader'):
            return None

        try:
            if self.ai.prompt_loader:
                return self.ai.prompt_loader.get_prompt('log_analysis_report')
        except Exception as e:
            self.logger.debug(f"Could not load prompt template: {e}")

        return None

    def _generate_report(
        self,
        metrics: Dict[str, any],
        events: List[str],
        warnings: List[str],
        prompt_data: Optional[Dict]
    ) -> Optional[str]:
        """
        Generate analysis report using AI.

        Args:
            metrics: Extracted metrics dict
            events: List of key events
            warnings: List of warnings/errors
            prompt_data: Optional prompt template data

        Returns:
            Markdown report content or None if failed
        """
        # Format data for AI
        metrics_str = "\n".join([
            f"- {key.replace('_', ' ').title()}: {value}"
            for key, value in metrics.items()
        ])

        events_str = "\n".join(f"- {event}" for event in events if event)

        warnings_str = "\n".join(f"- {warning}" for warning in warnings if warning)
        if not warnings_str:
            warnings_str = "- No warnings or errors"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Use template if available, otherwise use inline prompt
        if prompt_data:
            system_prompt = prompt_data.get('system', '')
            user_prompt = prompt_data.get('user', '').format(
                metrics=metrics_str,
                events=events_str,
                warnings=warnings_str,
                timestamp=timestamp
            )
            model = prompt_data.get('model')
            temperature = prompt_data.get('temperature', 0.5)
            max_tokens = prompt_data.get('max_tokens', 4096)
        else:
            # Fallback inline prompt
            system_prompt = (
                "You are a technical analyst reviewing crossword puzzle generation logs. "
                "Provide clear, actionable analysis of the generation process."
            )
            user_prompt = f"""Analyze this crossword generation log and create a markdown report.

LOG METRICS:
{metrics_str}

KEY EVENTS:
{events_str}

WARNINGS AND ERRORS:
{warnings_str}

Create a structured markdown report with:
# Crossword Generation Report
Generated: {timestamp}

## Summary
[2-3 paragraph analysis]

## Performance Metrics
[Key metrics with interpretation]

## Key Events
[Chronological timeline]

## Issues Encountered
[List issues with severity]

## Recommendations
[Actionable improvements]
"""
            model = "claude-sonnet-4-5-20250929"
            temperature = 0.5
            max_tokens = 16384

        # Make AI request
        try:
            response = self.ai._make_request(
                prompt_type="log_analysis_report",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )

            return response

        except Exception as e:
            self.logger.error(f"Error generating report with AI: {e}")
            return None
