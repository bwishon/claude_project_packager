import mimetypes
from pathlib import Path
from typing import List, Tuple
import logging
from .core import MAX_FILE_SIZE
from .gitignore import batch_check_ignore

# Create a verbose logger that uses the special VERBOSE level
def log_verbose(message):
    logging.log(15, message)  # 15 is our custom VERBOSE level

def is_binary_file(file_path: str) -> Tuple[bool, bool, str]:
    """Check if file is binary and if it's a type that Claude can process."""
    processable_binary_extensions = {
        '.png', '.jpg', '.jpeg', '.gif',  # Images
        '.mp3', '.wav', '.ogg',  # Audio
        '.mp4', '.avi', '.mov'  # Video
    }
    
    # Check if it's a binary file type that Claude can process
    if Path(file_path).suffix.lower() in processable_binary_extensions:
        return True, True, f"Binary file type understood by Claude: {Path(file_path).suffix}"
    
    # Check if it's a binary file using the existing logic
    try:
        with open(file_path, 'tr') as f:
            f.read(1024)
        return False, True, "Text file"
    except:
        return True, False, "Unprocessable binary file"

def scan_directory(root_dir: Path, very_verbose: bool = False) -> Tuple[List[Path], List[Tuple[str, str]], List[Tuple[str, str]]]:
    """Scan directory and categorize files."""
    all_files = []
    claude_files = []
    binary_files = []
    explicit_ignores = []
    
    log_verbose("\n=== Starting Directory Scan ===")
    log_verbose(f"Root dir: {root_dir}")
    log_verbose(f"Root dir (absolute): {root_dir.absolute()}")
    
    # First collect all files except .git directory and .gitignore
    for path in root_dir.rglob('*'):
        if path.is_file():
            if '.git' in path.parts:
                continue
            if path.name == '.gitignore':
                explicit_ignores.append((str(path.relative_to(root_dir)), "Configuration file"))
                continue
            if path.name.startswith('project-bundle') and path.suffix == '.json':
                explicit_ignores.append((str(path.relative_to(root_dir)), "Project packager output"))
                continue
            all_files.append(path)
    
    log_verbose(f"\nCollected {len(all_files)} files initially")
    if very_verbose:
        logging.debug("First 5 files collected:")
        for f in all_files[:5]:
            logging.debug(f"  {f} (relative to root: {f.relative_to(root_dir)})")
            
    # Use git check-ignore to find ignored files
    ignored_files = batch_check_ignore(root_dir, all_files)
    ignored_paths = {path for path, _ in ignored_files}
    
    log_verbose(f"\nFound {len(ignored_paths)} ignored paths")
    if very_verbose:
        logging.debug("First 5 ignored paths:")
        for p in list(ignored_paths)[:5]:
            logging.debug(f"  {p}")
    
    # Combine git-ignored files with our explicit ignores
    ignored_files.extend(explicit_ignores)
    
    # Filter out ignored files and check remaining for binary content
    included_files = []
    for path in all_files:
        rel_path = path.relative_to(root_dir)
        abs_path = path.absolute()
        
        if very_verbose:
            logging.debug(f"\nChecking path: {path}")
            logging.debug(f"  Relative path: {rel_path}")
            logging.debug(f"  Absolute path: {abs_path}")
        
        # Check if path is in ignored_paths
        should_ignore = False
        path_matches = [
            path in ignored_paths,
            rel_path in ignored_paths,
            abs_path in ignored_paths,
            str(path) in ignored_paths,
            str(rel_path) in ignored_paths,
            str(abs_path) in ignored_paths
        ]
        
        if any(path_matches):
            if very_verbose:
                logging.debug("  Path matched ignored paths:")
                logging.debug(f"    Raw path match: {path_matches[0]}")
                logging.debug(f"    Relative path match: {path_matches[1]}")
                logging.debug(f"    Absolute path match: {path_matches[2]}")
                logging.debug(f"    String path match: {path_matches[3]}")
                logging.debug(f"    String relative match: {path_matches[4]}")
                logging.debug(f"    String absolute match: {path_matches[5]}")
            log_verbose(f"  Skipping ignored file: {rel_path}")
            should_ignore = True
            
        if should_ignore:
            continue
            
        is_binary, claude_processable, reason = is_binary_file(str(path))
        if is_binary:
            if claude_processable:
                claude_files.append(path)
                log_verbose(f"  Including binary file processable by Claude: {rel_path} ({reason})")
            else:
                binary_files.append((str(rel_path), reason))
                log_verbose(f"  Skipping unprocessable binary file: {rel_path} ({reason})")
            continue
            
        included_files.append(path)
        log_verbose(f"  Including file: {rel_path}")
    
    log_verbose("\n=== Final Statistics ===")
    log_verbose(f"Total files found: {len(all_files)}")
    log_verbose(f"Files included: {len(included_files)}")
    log_verbose(f"Files ignored: {len(ignored_files)}")
    log_verbose(f"Binary files: {len(binary_files)}")
    
    return claude_files + included_files, ignored_files, binary_files

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
