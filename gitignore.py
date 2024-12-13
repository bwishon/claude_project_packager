import logging
import fnmatch
from pathlib import Path
from typing import List, Tuple

def parse_gitignore(gitignore_path: Path, include_defaults: bool = True) -> List[str]:
    """Parse .gitignore file and return list of patterns."""
    from core import DEFAULT_NODE_PATTERNS  # Import from core module
    
    patterns = DEFAULT_NODE_PATTERNS if include_defaults else []
    
    if not gitignore_path.exists():
        logging.warning(f"No .gitignore found at {gitignore_path}, using default Node.js patterns")
        return patterns
    
    with open(gitignore_path, 'r') as f:
        for line in f:
            line = line.split('#')[0].strip()
            if not line:
                continue
                
            # Handle negation patterns (!)
            if line.startswith('!'):
                logging.debug(f"Found negation pattern: {line}")
                continue  # Skip for now, but could implement negation handling
                
            patterns.append(line)
            if line.endswith('/'):
                patterns.append(line[:-1])

    logging.debug(f"Parsed {len(patterns)} patterns ({len(DEFAULT_NODE_PATTERNS)} defaults + {len(patterns) - len(DEFAULT_NODE_PATTERNS)} custom):")
    for pattern in patterns:
        logging.debug(f"  {pattern}")
    return patterns

def should_ignore(path: str, ignore_patterns: List[str]) -> Tuple[bool, str]:
    """Check if path matches any gitignore patterns. Returns (should_ignore, reason)."""
    path = Path(path).as_posix()
    
    # Always ignore .git directory
    if '.git' in Path(path).parts:
        return True, "Git repository files"
        
    # Check against common binary and build files
    binary_exts = {'.wasm', '.min.js', '.min.css', '.map'}
    if Path(path).suffix in binary_exts:
        return True, f"Binary or build file ({Path(path).suffix})"

    for pattern in ignore_patterns:
        pattern = pattern.replace('\\', '/')
        
        # Handle exact matches
        if pattern in path:
            return True, f"Matches pattern: {pattern}"
            
        # Handle directory patterns
        if pattern.endswith('/'):
            base_pattern = pattern.rstrip('/')
            if path.startswith(base_pattern) or f"/{base_pattern}/" in path:
                return True, f"Matches directory pattern: {pattern}"
        
        # Handle glob patterns
        if '*' in pattern or '?' in pattern or '[' in pattern:
            if fnmatch.fnmatch(Path(path).name, pattern):
                return True, f"Matches glob pattern: {pattern}"
            if fnmatch.fnmatch(path, pattern):
                return True, f"Matches path glob pattern: {pattern}"
            if not pattern.startswith('/') and fnmatch.fnmatch(path, f"**/{pattern}"):
                return True, f"Matches **/ glob pattern: {pattern}"

    return False, ""