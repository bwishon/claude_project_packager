"""
Project Packager - A tool for packaging Node.js projects into XML format for analysis.

This package provides functionality to:
- Parse .gitignore patterns
- Process project files while respecting ignore rules
- Generate structured XML output with file contents and metadata
- Handle large projects through batch processing
"""

from . import core
from . import gitignore
from . import file_processing
from . import xml_generator
from .main import main

__version__ = "0.1.0"
__author__ = "Your Name"

__all__ = [
    "core",
    "gitignore",
    "file_processing",
    "xml_generator",
    "main"
]