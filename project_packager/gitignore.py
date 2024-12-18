#!/usr/bin/env python3

import subprocess
from pathlib import Path
import logging
from typing import List, Tuple

def get_repo_root(path: Path) -> Path:
    """Get the root directory of the git repository containing the given path."""
    try:
        logging.debug(f"\nGetting repo root for path: {path}")
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            cwd=path,
            capture_output=True,
            text=True,
            check=True
        )
        repo_root = Path(result.stdout.strip())
        logging.debug(f"Found repo root: {repo_root}")
        return repo_root
    except subprocess.SubprocessError as e:
        logging.warning(f"Not a git repository: {e}")
        logging.debug(f"Git command output: {e.output if hasattr(e, 'output') else 'No output'}")
        return path

def batch_check_ignore(root_dir: Path, files: List[Path], batch_size: int = 1000) -> List[Tuple[Path, str]]:
    """Check multiple files against gitignore patterns using git check-ignore."""
    ignored_files = []
    
    logging.debug("\n=== Git Check-Ignore Configuration ===")
    logging.debug(f"Target directory: {root_dir}")
    logging.debug(f"Total files to check: {len(files)}")
    
    # Process files in batches to avoid command line length limits
    for i in range(0, len(files), batch_size):
        batch = files[i:i + batch_size]
        
        # Make all paths relative to root_dir
        rel_paths = [str(f.relative_to(root_dir)) for f in batch]
        
        # Build the complete command for logging
        cmd = ['git', 'check-ignore', '-v', '--no-index', '--'] + rel_paths
        
        logging.debug("\n=== Git Command Execution ===")
        logging.debug(f"Working directory: {root_dir}")
        logging.debug("Command:")
        logging.debug(f"  {' '.join(cmd[:4])}  # Plus {len(rel_paths)} file paths")
        if len(rel_paths) <= 3:  # Show all paths if 3 or fewer
            logging.debug(f"Complete command: {' '.join(cmd)}")
        else:  # Show first 3 paths as example
            logging.debug(f"First 3 paths being checked:")
            for path in rel_paths[:3]:
                logging.debug(f"  {path}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=root_dir,
                capture_output=True,
                text=True
            )
            
            logging.debug("\n=== Command Results ===")
            logging.debug(f"Return code: {result.returncode}")
            if result.stderr:
                logging.debug(f"stderr output:")
                logging.debug(result.stderr)
            if result.stdout:
                lines = result.stdout.splitlines()
                logging.debug(f"Found {len(lines)} ignored files in this batch")
                if lines:
                    logging.debug("First few matches:")
                    for line in lines[:3]:
                        logging.debug(f"  {line}")
            
            # Parse output line by line
            for line in result.stdout.splitlines():
                if not line:
                    continue
                try:
                    pattern, rel_file = line.split('\t')
                    file_path = Path(rel_file)
                    ignored_files.append((file_path, f"Matches pattern: {pattern}"))
                except ValueError:
                    logging.warning(f"Unexpected git check-ignore output: {line}")
                    
        except subprocess.SubprocessError as e:
            logging.error(f"Git command failed: {e}")
            logging.debug(f"Error details: {e.output if hasattr(e, 'output') else 'No output available'}")
            break
    
    logging.debug("\n=== Final Summary ===")
    logging.debug(f"Total ignored files found: {len(ignored_files)}")
    
    return ignored_files
 
def should_ignore(path: str, root_dir: Path) -> Tuple[bool, str]:
    """Check if a single path should be ignored using git check-ignore."""
    repo_root = get_repo_root(root_dir)
    abs_path = Path(path).absolute()
    
    logging.debug(f"\nChecking single path: {abs_path}")
    logging.debug(f"Working directory: {root_dir}")
    logging.debug(f"Repository root: {repo_root}")
    
    try:
        cmd = ['git', 'check-ignore', '-v', '--', str(abs_path)]
        logging.debug(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=repo_root,
            capture_output=True,
            text=True
        )
        
        logging.debug(f"Command return code: {result.returncode}")
        if result.stderr:
            logging.debug(f"stderr: {result.stderr}")
        if result.stdout:
            logging.debug(f"stdout: {result.stdout}")
        
        if result.returncode == 0:  # File is ignored
            pattern = result.stdout.split('\t')[0]
            return True, f"Matches pattern: {pattern}"
            
        return False, ""
        
    except subprocess.SubprocessError as e:
        logging.error(f"Error checking ignore status: {e}")
        logging.debug(f"Full error: {e.output if hasattr(e, 'output') else 'No output'}")
        return False, ""