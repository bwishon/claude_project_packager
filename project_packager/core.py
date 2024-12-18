#!/usr/bin/env python3

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Set, Tuple

# Constants for file processing
MAX_TOKENS_PER_MESSAGE = 100000
CHARS_PER_TOKEN = 4
MAX_FILE_SIZE = 100000

def setup_logging(verbose: bool = False, very_verbose: bool = False, log_file: str = None):
    """Setup logging to both console and file if specified."""
    if very_verbose:
        log_level = logging.DEBUG
    elif verbose:
        logging.addLevelName(15, "VERBOSE")
        log_level = 15
    else:
        log_level = logging.INFO

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Allow all logs through the root logger

    # Clear any existing handlers
    root_logger.handlers = []

    # Always set up console handler for INFO level and above
    # This ensures errors and critical messages still show
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Only show INFO and above on console
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    if log_file:
        # Add file handler for debug output
        file_handler = logging.FileHandler(log_file, mode='w')
        file_handler.setLevel(logging.DEBUG)  # Full debug to file
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    else:
        # If no log file, allow verbose/debug output to console
        console_handler.setLevel(log_level)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Package project files for Claude analysis',
        usage='%(prog)s [project_dir] [options]'
    )
    parser.add_argument('project_dir', nargs='?', default=os.getcwd(),
                       help='Project directory to package (default: current directory)')
    parser.add_argument('-o', '--output', default='claude_project.json', 
                       help='Output JSON file name (default: claude_project.json)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('-vv', '--very-verbose', action='store_true',
                       help='Enable very verbose debug output')
    parser.add_argument('--log-file', metavar='FILE',
                       help='Write detailed logs to specified file')
    parser.add_argument('--max-file-size', type=int, default=MAX_FILE_SIZE,
                       help=f'Maximum size of individual files to include (bytes, default: {MAX_FILE_SIZE})')
    
    args = parser.parse_args()
    
    # Always use absolute path for project directory
    args.project_dir = os.path.abspath(args.project_dir)
    
    return args
