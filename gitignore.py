#!/usr/bin/env python3

import subprocess
from pathlib import Path
import logging
from typing import List, Tuple

def batch_check_ignore(root_dir: Path, files: List[Path], batch_size: int = 1000) -> List[Tuple[Path, str]]:
    """Check multiple files against gitignore patterns using git check-ignore.
    Returns list of (path, reason) tuples for ignored files."""
    ignored_files = []
    
    # Convert root_dir to git repository root
    try:
        repo_root = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            cwd=root_dir,
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()
        root_dir = Path(repo_root)
    except subprocess.SubprocessError:
        logging.warning("Not a git repository root, using specified directory")
    
    # Process files in batches to avoid command line length limits
    for i in range(0, len(files), batch_size):
        batch = files[i:i + batch_size]
        rel_paths = [str(f.relative_to(root_dir)) for f in batch]
        
        try:
            # Use git check-ignore with -v for verbose output
            result = subprocess.run(
                ['git', 'check-ignore', '-v', '--no-index', '--'] + rel_paths,
                cwd=root_dir,
                capture_output=True,
                text=True
            )
            
            # Parse output: format is "pattern	file"
            for line in result.stdout.splitlines():
                if not line:
                    continue
                try:
                    pattern, file = line.split('\t')
                    ignored_files.append((Path(file), f"Matches pattern: {pattern}"))
                except ValueError:
                    logging.warning(f"Unexpected git check-ignore output: {line}")
                    
        except subprocess.SubprocessError as e:
            logging.error(f"Error running git check-ignore: {e}")
            break
    
    return ignored_files

def should_ignore(path: str, root_dir: Path) -> Tuple[bool, str]:
    """Check if a single path should be ignored using git check-ignore."""
    try:
        result = subprocess.run(
            ['git', 'check-ignore', '-v', '--no-index', '--', path],
            cwd=root_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:  # File is ignored
            pattern = result.stdout.split('\t')[0]
            return True, f"Matches pattern: {pattern}"
            
        return False, ""
        
    except subprocess.SubprocessError as e:
        logging.error(f"Error checking ignore status: {e}")
        return False, ""