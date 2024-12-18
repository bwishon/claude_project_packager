"""
Project Packager - A tool for packaging projects into XML format for analysis.

This package provides functionality to:
- Use Git's check-ignore for robust ignore pattern handling
- Process project files efficiently in batches
- Generate structured XML output with file contents and metadata
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

# Export commonly used functions
from .gitignore import batch_check_ignore, should_ignore
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
    
    # Functions
    "batch_check_ignore",
    "should_ignore",
    "is_binary_file",
    "scan_directory",
    "create_xml_document"
]

# Default configuration
default_config = {
    'max_file_size': MAX_FILE_SIZE,
    'workers': None,  # Will use CPU count
    'chunk_size': 8192,  # For reading large files
    'validate_output': True
}