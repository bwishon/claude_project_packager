#!/usr/bin/env python3

from pathlib import Path
import logging
import sys
import os

from core import (
    setup_logging,
    parse_arguments,
    MAX_TOKENS_PER_MESSAGE,
    CHARS_PER_TOKEN
)
from gitignore import parse_gitignore, should_ignore
from file_processing import scan_directory, create_file_batch
from xml_generator import create_xml_document

def main():
    """Main execution flow for project packaging."""
    # Use current directory if no directory specified
    if len(sys.argv) == 1:
        sys.argv.append('.')
    
    # Parse command line arguments
    args = parse_arguments()

    # Setup logging
    setup_logging(args.verbose)

    # Validate and resolve project directory
    root_dir = Path(args.project_dir).resolve()
    output_file = Path(args.output)
    
    if not root_dir.is_dir():
        logging.error(f"Error: {root_dir} is not a directory")
        sys.exit(1)
        
    # Parse gitignore patterns
    gitignore = root_dir / '.gitignore'
    ignore_patterns = parse_gitignore(gitignore, not args.no_defaults)
    
    logging.info(f"Scanning directory: {root_dir}")
    
    # Scan directory and categorize files
    all_files, ignored_files, binary_files = scan_directory(root_dir, ignore_patterns)
    
    # Log summary
    logging.info(f"\nSummary:")
    logging.info(f"Found {len(all_files)} files to include")
    logging.info(f"Ignored {len(ignored_files)} files based on patterns")
    logging.info(f"Skipped {len(binary_files)} binary files")
    
    # Log detailed file lists if verbose
    if args.verbose:
        logging.debug("\nIncluded files:")
        for f in sorted(str(f.relative_to(root_dir)) for f in all_files):
            logging.debug(f"  {f}")
        logging.debug("\nIgnored files:")
        for f, reason in sorted(ignored_files):
            logging.debug(f"  {f} ({reason})")
        logging.debug("\nBinary files:")
        for f, reason in sorted(binary_files):
            logging.debug(f"  {f} ({reason})")
    
    # Sort files for consistent output
    all_files.sort()
    
    # Process files in batches if needed
    max_chars = MAX_TOKENS_PER_MESSAGE * CHARS_PER_TOKEN
    start_idx = 0
    batch_num = 1
    processed_files = set()
    
    while start_idx < len(all_files):
        batch_files, new_idx = create_file_batch(root_dir, all_files, start_idx, max_chars)
        
        if not batch_files:
            if new_idx == start_idx:
                logging.error("Failed to process any files in batch - stopping")
                break
            start_idx = new_idx
            continue
            
        # Check for duplicates
        batch_set = {str(f.relative_to(root_dir)) for f in batch_files}
        overlap = batch_set & processed_files
        if overlap:
            logging.warning(f"Duplicate files detected: {overlap}")
            start_idx = new_idx
            continue
        
        # Generate XML for this batch
        if new_idx < len(all_files):
            # More files to come, create numbered batch
            output_path = create_xml_document(
                root_dir, 
                batch_files, 
                ignored_files, 
                output_file, 
                batch_num
            )
            logging.info(f"Created batch {batch_num}: {output_path}")
            batch_num += 1
        else:
            # Last/only batch, create without number
            output_path = create_xml_document(
                root_dir, 
                batch_files, 
                ignored_files, 
                output_file
            )
            logging.info(f"Created: {output_path}")
        
        # Track processed files
        processed_files.update(batch_set)
        start_idx = new_idx

if __name__ == '__main__':
    main()