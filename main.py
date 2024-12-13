#!/usr/bin/env python3

from pathlib import Path
import logging
import sys
import os
import xml.etree.ElementTree as ET
from multiprocessing import Pool
from tqdm import tqdm
from typing import Set

from core import (
    setup_logging,
    parse_arguments,
    MAX_TOKENS_PER_MESSAGE,
    CHARS_PER_TOKEN
)
from gitignore import parse_gitignore, should_ignore
from file_processing import scan_directory, create_file_batch
from xml_generator import create_xml_document

def scan_files_parallel(root_dir: Path, chunk: Path, ignore_patterns: list, exclude_types: Set[str] = None) -> tuple:
    """Scan a chunk of the directory in parallel."""
    try:
        return scan_directory(root_dir, ignore_patterns, start_dir=chunk, exclude_types=exclude_types)
    except Exception as e:
        logging.error(f"Error scanning {chunk}: {e}")
        return [], [], []

def get_file_statistics(files: list) -> tuple:
    """Generate statistics about the files to be processed."""
    file_types = {}
    total_size = 0
    
    for f in files:
        ext = f.suffix.lower()
        file_types[ext] = file_types.get(ext, 0) + 1
        total_size += f.stat().st_size
        
    return file_types, total_size

def validate_output(output_path: Path) -> None:
    """Validate the generated XML file."""
    if not output_path.exists():
        raise ValueError(f"Output file not created: {output_path}")
        
    if output_path.stat().st_size == 0:
        raise ValueError(f"Created file is empty: {output_path}")
        
    try:
        ET.parse(output_path)
    except ET.ParseError as e:
        raise ValueError(f"Created XML is invalid: {e}")

def process_file_batch(root_dir: Path, batch_files: list, ignored_files: list, 
                      output_file: Path, batch_num: int = None) -> Path:
    """Process a batch of files and create XML document."""
    try:
        output_path = create_xml_document(
            root_dir,
            batch_files,
            ignored_files,
            output_file,
            batch_num
        )
        validate_output(output_path)
        return output_path
    except Exception as e:
        logging.error(f"Failed to create XML document: {e}")
        raise

def main() -> int:
    """Main execution flow for project packaging."""
    try:
        # Use current directory if no directory specified
        if len(sys.argv) == 1:
            sys.argv.append('.')
        
        # Parse command line arguments
        args = parse_arguments()

        # Setup logging
        setup_logging(args.verbose, args.log_file)

        # Convert exclude_types to set with dots
        exclude_types = {f'.{ext.lstrip(".")}' for ext in args.exclude_types} if args.exclude_types else set()

        # Validate and resolve project directory
        root_dir = Path(args.project_dir).resolve()
        output_file = Path(args.output)
        
        if not root_dir.is_dir():
            logging.error(f"Error: {root_dir} is not a directory")
            return 1
            
        # Parse gitignore patterns
        gitignore = root_dir / '.gitignore'
        ignore_patterns = parse_gitignore(gitignore, not args.no_defaults)
        
        logging.info(f"Scanning directory: {root_dir}")
        
        # Scan directory in parallel
        with Pool(args.workers) as pool:
            chunks = list(root_dir.iterdir())
            results = pool.starmap(
                scan_files_parallel,
                [(root_dir, chunk, ignore_patterns, exclude_types) for chunk in chunks]
            )
        
        # Combine results
        all_files = []
        ignored_files = []
        binary_files = []
        for r in results:
            all_files.extend(r[0])
            ignored_files.extend(r[1])
            binary_files.extend(r[2])
        
        # Get file statistics
        file_types, total_size = get_file_statistics(all_files)
        
        # Log summary
        logging.info(f"\nSummary:")
        logging.info(f"Found {len(all_files):,} files to include")
        logging.info(f"Ignored {len(ignored_files):,} files based on patterns")
        logging.info(f"Skipped {len(binary_files):,} binary files")
        logging.info(f"Total size to process: {total_size / (1024*1024):.2f} MB")
        
        logging.info("\nFile type distribution:")
        for ext, count in sorted(file_types.items()):
            logging.info(f"  {ext or 'no extension'}: {count:,} files")
        
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
        
        with tqdm(total=len(all_files), desc="Processing files") as pbar:
            while start_idx < len(all_files):
                try:
                    batch_files, new_idx = create_file_batch(
                        root_dir,
                        all_files,
                        start_idx,
                        max_chars,
                        args.max_file_size
                    )
                    
                    if not batch_files:
                        if new_idx == start_idx:
                            logging.error("Failed to process any files in batch - stopping")
                            return 1
                        start_idx = new_idx
                        pbar.update(new_idx - start_idx)
                        continue
                        
                    # Check for duplicates
                    batch_set = {str(f.relative_to(root_dir)) for f in batch_files}
                    overlap = batch_set & processed_files
                    if overlap:
                        logging.warning(f"Duplicate files detected: {overlap}")
                        start_idx = new_idx
                        pbar.update(new_idx - start_idx)
                        continue
                    
                    # Generate XML for this batch
                    if new_idx < len(all_files):
                        # More files to come, create numbered batch
                        output_path = process_file_batch(
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
                        output_path = process_file_batch(
                            root_dir,
                            batch_files,
                            ignored_files,
                            output_file
                        )
                        logging.info(f"Created: {output_path}")
                    
                    # Track processed files
                    processed_files.update(batch_set)
                    
                except Exception as e:
                    logging.error(f"Error processing batch: {e}")
                    if args.verbose:
                        logging.exception("Full traceback:")
                    return 1
                
                start_idx = new_idx
                pbar.update(new_idx - start_idx)
        
        return 0
        
    except KeyboardInterrupt:
        logging.info("\nOperation cancelled by user")
        return 0
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        if args.verbose:
            logging.exception("Full traceback:")
        return 1

if __name__ == '__main__':
    sys.exit(main())