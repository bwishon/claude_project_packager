"""
Project Packager - A tool for packaging projects into XML format for analysis.

This package provides functionality to:
- Parse .gitignore patterns with robust pattern matching
- Process project files while respecting ignore rules
- Generate structured XML output with file contents and metadata
- Handle large projects through batch processing
- Parallel file processing for improved performance
- Memory-efficient handling of large files
"""

from . import core
from . import gitignore
from . import file_processing
from . import xml_generator
from .main import main
from .core import MAX_FILE_SIZE, MAX_TOKENS_PER_MESSAGE, CHARS_PER_TOKEN

__version__ = "0.2.0"
__author__ = "Your Name"

# Export commonly used functions and classes
from .gitignore import GitignoreManager, parse_gitignore, should_ignore
from .file_processing import is_binary_file, scan_directory
from .xml_generator import create_xml_document

__all__ = [
    # Modules
    "core",
    "gitignore",
    "file_processing",
    "xml_generator",
    "main",
    
    # Constants
    "MAX_FILE_SIZE",
    "MAX_TOKENS_PER_MESSAGE",
    "CHARS_PER_TOKEN",
    
    # Functions and classes
    "GitignoreManager",
    "parse_gitignore",
    "should_ignore",
    "is_binary_file",
    "scan_directory",
    "create_xml_document"
]

# Default configuration
default_config = {
    'max_file_size': MAX_FILE_SIZE,
    'workers': None,  # Will use CPU count
    'include_default_ignores': True,
    'chunk_size': 8192,  # For reading large files
    'validate_output': True
}