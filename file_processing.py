import mimetypes
from pathlib import Path
from typing import List, Tuple
import logging
from gitignore import should_ignore
from core import MAX_FILE_SIZE

def is_binary_file(file_path: str) -> Tuple[bool, str]:
    """Check if file is binary. Returns (is_binary, reason)."""
    binary_extensions = {
        '.pyc', '.pyo', '.so', '.o', '.dll', '.lib', '.dylib', '.exe',
        '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.ico', '.class',
        '.bin', '.obj', '.jar', '.pkl', '.pyd', '.wasm', '.br', '.gz'
    }
    
    # Check extension
    if Path(file_path).suffix.lower() in binary_extensions:
        return True, f"Binary extension: {Path(file_path).suffix}"
        
    # Check if it's a minified file
    if Path(file_path).name.endswith('.min.js') or Path(file_path).name.endswith('.min.css'):
        return True, "Minified file"
        
    # Check for source maps
    if Path(file_path).name.endswith('.map'):
        return True, "Source map file"

    # Check content
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            if b'\0' in chunk:
                return True, "Contains null bytes"
    except Exception as e:
        return True, f"Error reading file: {e}"

    return False, ""

def create_file_batch(root_dir: Path, files: List[Path], start_idx: int, max_chars: int, max_file_size: int) -> Tuple[List[Path], int]:
    """Create a batch of files that fits within token limit."""
    current_chars = 0
    batch_files = []
    current_idx = start_idx
    
    while current_idx < len(files):
        file_path = files[current_idx]
        file_size = file_path.stat().st_size
        
        if file_size > max_file_size:
            logging.warning(f"Skipping {file_path} - too large ({file_size:,} bytes)")
            current_idx += 1
            continue
            
        if current_chars + file_size > max_chars and batch_files:
            break
        elif current_chars + file_size > max_chars:
            logging.warning(f"Skipping {file_path} - would exceed batch size limit")
            current_idx += 1
            continue
            
        batch_files.append(file_path)
        current_chars += file_size
        current_idx += 1
        
    return batch_files, current_idx

def scan_directory(root_dir: Path, ignore_patterns: List[str], start_dir: Path = None) -> Tuple[List[Path], List[Tuple[str, str]], List[Tuple[str, str]]]:
    """Scan directory and categorize files."""
    all_files = []
    ignored_files = []
    binary_files = []
    
    logging.debug("\nStarting directory scan...")
    logging.debug(f"Root dir: {root_dir}")
    logging.debug(f"Start dir: {start_dir if start_dir else 'same as root'}")
    logging.debug("Found files before filtering:")
    
    # First, just list all files found
    scan_root = start_dir if start_dir else root_dir
    all_found_files = list(scan_root.rglob('*'))
    for path in all_found_files:
        if path.is_file():
            logging.debug(f"Found file: {path}")
            
    # Now process each file
    for path in all_found_files:
        if not path.is_file():
            continue
            
        try:
            rel_path = str(path.relative_to(root_dir))
            logging.debug(f"\nProcessing file: {rel_path}")
            logging.debug(f"Absolute path: {path}")
            
            # Check gitignore patterns
            logging.debug("Checking gitignore patterns:")
            should_ignore_file, ignore_reason = should_ignore(rel_path, ignore_patterns)
            if should_ignore_file:
                ignored_files.append((rel_path, ignore_reason))
                logging.debug(f"IGNORED: {rel_path} ({ignore_reason})")
                continue
            else:
                logging.debug(f"Not ignored by any pattern")
            
            # Check for binary files
            logging.debug("Checking if binary:")
            is_binary, binary_reason = is_binary_file(str(path))
            if is_binary:
                binary_files.append((rel_path, binary_reason))
                logging.debug(f"BINARY: {rel_path} ({binary_reason})")
                continue
            else:
                logging.debug("Not binary")
            
            # If we get here, the file should be included
            logging.debug(f"INCLUDING: {rel_path}")
            all_files.append(path)
            
        except Exception as e:
            logging.error(f"Error processing {path}: {e}")
            logging.exception("Full traceback:")
            continue
    
    logging.debug(f"\nScan complete.")
    logging.debug(f"Found {len(all_found_files)} total files")
    logging.debug(f"Including {len(all_files)} files")
    logging.debug(f"Ignored {len(ignored_files)} files")
    logging.debug(f"Binary {len(binary_files)} files")
    return all_files, ignored_files, binary_files