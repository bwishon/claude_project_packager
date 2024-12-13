import logging
import fnmatch
from pathlib import Path
from typing import List, Tuple, Dict

class GitignorePattern:
    """Class to handle gitignore pattern matching."""
    def __init__(self, pattern: str):
        self.original = pattern
        self.pattern = pattern.rstrip('/')
        self.is_dir_only = pattern.endswith('/')
        self.is_negation = pattern.startswith('!')
        self.is_absolute = pattern.startswith('/')
        
        if self.is_negation:
            self.pattern = self.pattern[1:]
        if self.is_absolute:
            self.pattern = self.pattern[1:]
            
    def matches(self, path: str) -> bool:
        """Check if path matches this pattern."""
        path = path.replace('\\', '/')
        
        # Handle directory-only patterns
        if self.is_dir_only and not path.endswith('/'):
            path = path + '/'
        
        # Log the exact pattern and path being checked
        logging.debug(f"  Checking '{path}' against pattern '{self.pattern}'")
        
        # Handle absolute paths
        if self.is_absolute:
            result = fnmatch.fnmatch(path, self.pattern)
            logging.debug(f"    Absolute path match: {result}")
            return result
        
        # Handle the path both with and without a leading slash
        normalized_path = path.lstrip('/')
        pattern_with_slash = f"**/{self.pattern}"
        
        match1 = fnmatch.fnmatch(normalized_path, self.pattern)
        match2 = fnmatch.fnmatch(normalized_path, pattern_with_slash)
        
        logging.debug(f"    Direct pattern match: {match1}")
        logging.debug(f"    With **/ prefix match: {match2}")
        
        return match1 or match2

def parse_gitignore(gitignore_path: Path) -> List[str]:
    """Parse .gitignore file and return list of patterns."""
    patterns = []
    
    if not gitignore_path.exists():
        logging.debug("No .gitignore found, only .git directory will be ignored")
        return patterns
        
    try:
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.split('#')[0].strip()
                if line:  # Skip empty lines and comments
                    patterns.append(line)
                    
        logging.debug(f"Parsed {len(patterns)} patterns from .gitignore:")
        for pattern in patterns:
            logging.debug(f"  {pattern}")
            
    except Exception as e:
        logging.error(f"Error reading .gitignore: {e}")
        
    return patterns

def should_ignore(path: str, ignore_patterns: List[str]) -> Tuple[bool, str]:
    """Check if path matches any gitignore patterns. Returns (should_ignore, reason)."""
    logging.debug(f"\nChecking if should ignore: {path}")
    
    # Always ignore .git directory
    if '.git' in Path(path).parts:
        logging.debug("  Ignoring .git directory")
        return True, "Git repository files"
    
    # Convert patterns to GitignorePattern objects
    patterns = [GitignorePattern(p) for p in ignore_patterns]
    path = str(path)
    
    # Keep track of matched patterns
    matching_pattern = None
    should_ignore = False
    
    logging.debug(f"  Testing against {len(patterns)} patterns:")
    for pattern in patterns:
        logging.debug(f"\n  Pattern: {pattern.original}")
        logging.debug(f"    Is dir only: {pattern.is_dir_only}")
        logging.debug(f"    Is absolute: {pattern.is_absolute}")
        logging.debug(f"    Is negation: {pattern.is_negation}")
        
        if pattern.matches(path):
            logging.debug(f"    MATCHED")
            matching_pattern = pattern.original
            should_ignore = not pattern.is_negation
        else:
            logging.debug(f"    Did not match")
    
    if should_ignore and matching_pattern:
        return True, f"Matches pattern: {matching_pattern}"
        
    return False, ""