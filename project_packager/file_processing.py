import mimetypes
from pathlib import Path
from typing import List, Tuple
import logging
from .core import MAX_FILE_SIZE
from .gitignore import batch_check_ignore

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

def scan_directory(root_dir: Path) -> Tuple[List[Path], List[Tuple[str, str]], List[Tuple[str, str]]]:
    """Scan directory and categorize files."""
    all_files = []
    binary_files = []
    explicit_ignores = []
    
    logging.debug("\nStarting directory scan...")
    logging.debug(f"Root dir: {root_dir}")
    
    # First collect all files except .git directory and .gitignore
    for path in root_dir.rglob('*'):
        if path.is_file():
            if '.git' in path.parts:
                continue
            if path.name == '.gitignore':
                explicit_ignores.append((str(path.relative_to(root_dir)), "Configuration file"))
                continue
            all_files.append(path)
            
    # Use git check-ignore to find ignored files
    ignored_files = batch_check_ignore(root_dir, all_files)
    ignored_paths = {path for path, _ in ignored_files}
    
    # Combine git-ignored files with our explicit ignores
    ignored_files.extend(explicit_ignores)
    
    # Filter out ignored files and check remaining for binary content
    included_files = []
    for path in all_files:
        if path not in ignored_paths:
            is_binary, reason = is_binary_file(str(path))
            if is_binary:
                binary_files.append((str(path.relative_to(root_dir)), reason))
                continue
            included_files.append(path)
    
    logging.debug(f"\nScan complete.")
    logging.debug(f"Found {len(all_files)} total files")
    logging.debug(f"Including {len(included_files)} files")
    logging.debug(f"Ignored {len(ignored_files)} files")
    logging.debug(f"Binary {len(binary_files)} files")
    
    return included_files, ignored_files, binary_files