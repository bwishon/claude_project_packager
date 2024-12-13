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

def create_file_batch(root_dir: Path, files: List[Path], start_idx: int, max_chars: int) -> Tuple[List[Path], int]:
    """Create a batch of files that fits within token limit."""
    current_chars = 0
    batch_files = []
    current_idx = start_idx
    
    while current_idx < len(files):
        file_path = files[current_idx]
        file_size = file_path.stat().st_size
        
        if file_size > MAX_FILE_SIZE:  # Make sure to import this from core
            logging.warning(f"Skipping {file_path} - too large ({file_size} bytes)")
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

def scan_directory(root_dir: Path, ignore_patterns: List[str]) -> Tuple[List[Path], List[Tuple[str, str]], List[Tuple[str, str]]]:
    """Scan directory and categorize files."""
    all_files = []
    ignored_files = []
    binary_files = []
    
    for path in root_dir.rglob('*'):
        if not path.is_file():
            continue
            
        rel_path = str(path.relative_to(root_dir))
        
        # Check gitignore patterns
        should_ignore_file, ignore_reason = should_ignore(rel_path, ignore_patterns)
        if should_ignore_file:
            ignored_files.append((rel_path, ignore_reason))
            continue
            
        # Check for binary files
        is_binary, binary_reason = is_binary_file(str(path))
        if is_binary:
            binary_files.append((rel_path, binary_reason))
            logging.debug(f"Skipping binary file: {rel_path} ({binary_reason})")
            continue
            
        all_files.append(path)
    
    return all_files, ignored_files, binary_files