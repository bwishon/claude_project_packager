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

def setup_logging(verbose: bool = False, log_file: str = None):
    """Setup logging to both console and file if specified."""
    log_level = logging.DEBUG if verbose else logging.INFO
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file, mode='w')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Package project files for Claude analysis',
        usage='%(prog)s [project_dir] [options]'
    )
    parser.add_argument('project_dir', nargs='?', default='.',
                       help='Project directory to package (default: current directory)')
    parser.add_argument('-o', '--output', default='claude_project.xml', 
                       help='Output XML file name (default: claude_project.xml)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--log-file', metavar='FILE',
                       help='Write detailed logs to specified file')
    parser.add_argument('--max-file-size', type=int, default=MAX_FILE_SIZE,
                       help=f'Maximum size of individual files to include (bytes, default: {MAX_FILE_SIZE})')
    return parser.parse_args()