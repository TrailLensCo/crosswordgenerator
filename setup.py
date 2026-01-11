#!/usr/bin/env python3
# Copyright (c) 2026 TrailLensCo
# All rights reserved.
#
# This file is proprietary and confidential.
# Unauthorized copying, distribution, or use of this file,
# via any medium, is strictly prohibited without the express
# written permission of TrailLensCo.

"""
Setup script for crossword generator package.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="crossword-generator",
    version="1.0.0",
    author="TrailLensCo",
    description="AI-powered crossword puzzle generator with NYT-style constraints",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/TrailLensCo/crosswordgenerator",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "anthropic>=0.75.0",
        "pyyaml>=6.0.2",
    ],
    package_data={
        "": [
            "data/*.json",
            "data/*.txt",
        ],
    },
    include_package_data=True,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "crossword-generator=crossword_generator:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Games/Entertainment :: Puzzle Games",
    ],
)
