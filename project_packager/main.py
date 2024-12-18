#!/usr/bin/env python3

from pathlib import Path
import logging
import sys
import os

from .core import (
    setup_logging,
    parse_arguments,
    MAX_TOKENS_PER_MESSAGE,
    CHARS_PER_TOKEN
)
from .file_processing import scan_directory, create_file_batch
from .json_generator import create_json_document

def get_file_statistics(files: list) -> tuple:
    """Generate statistics about the files."""
    file_types = {}
    total_size = 0
    
    for f in files:
        ext = f.suffix.lower()
        file_types[ext] = file_types.get(ext, 0) + 1
        total_size += f.stat().st_size
        
    return file_types, total_size

def main() -> int:
    """Main execution flow for project packaging."""
    try:
        # Use current directory if no directory specified
        if len(sys.argv) == 1:
            sys.argv.append('.')
        
        # Parse command line arguments
        args = parse_arguments()

        # Setup logging
        setup_logging(args.verbose, args.very_verbose, args.log_file)

        # Validate and resolve project directory
        root_dir = Path(args.project_dir).resolve()
        
        # Make output path relative to the target directory, not the current directory
        if os.path.isabs(args.output):
            output_file = Path(args.output)
        else:
            output_file = root_dir / args.output
        
        if not root_dir.is_dir():
            logging.error(f"Error: {root_dir} is not a directory")
            return 1
            
        logging.info(f"Scanning directory: {root_dir}")
        logging.info(f"Output will be written to: {output_file}")
        
        # Create output directory if it doesn't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Scan directory for files
        logging.debug("\nStarting file scan...")
        all_files, ignored_files, binary_files = scan_directory(root_dir, args.very_verbose)        
        # Get file statistics
        file_types, total_size = get_file_statistics(all_files)
        
        # Log summary
        logging.info(f"\nSummary:")
        logging.info(f"Found {len(all_files):,} files to include")
        logging.info(f"Ignored {len(ignored_files):,} files")
        logging.info(f"Skipped {len(binary_files):,} binary files")
        logging.info(f"Total size to process: {total_size / (1024*1024):.2f} MB")
        
        logging.info("\nFile type distribution:")
        for ext, count in sorted(file_types.items()):
            logging.info(f"  {ext or 'no extension'}: {count:,} files")
        
        # Log detailed file lists if verbose
        if args.very_verbose:
            logging.debug("\nIncluded files:")
            for f in sorted(str(f.relative_to(root_dir)) for f in all_files):
                logging.debug(f"  {f}")
            logging.debug("\nIgnored files:")
            # Convert both elements to strings before sorting
            for path, reason in sorted((str(f), reason) for f, reason in ignored_files):
                logging.debug(f"  {path} ({reason})")
            logging.debug("\nBinary files:")
            for f, reason in sorted(binary_files):
                logging.debug(f"  {f} ({reason})")

        if not all_files:
            logging.error("No files found to include!")
            return 1

# Process files in batches if needed
        max_chars = MAX_TOKENS_PER_MESSAGE * CHARS_PER_TOKEN
        start_idx = 0
        batch_num = 1
        processed_files = set()
        
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
                    continue
                
                # Generate XML for this batch
                if new_idx < len(all_files):
                    output_path = create_json_document(
                        root_dir, 
                        batch_files, 
                        ignored_files, 
                        output_file, 
                        batch_num
                    )
                    logging.info(f"Created batch {batch_num}: {output_path}")
                    batch_num += 1
                else:
                    output_path = create_json_document(
                        root_dir, 
                        batch_files, 
                        ignored_files, 
                        output_file
                    )
                    logging.info(f"Created: {output_path}")
                
                start_idx = new_idx
                
            except Exception as e:
                logging.error(f"Error processing batch: {e}")
                if args.verbose:
                    logging.exception("Full traceback:")
                return 1
        
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