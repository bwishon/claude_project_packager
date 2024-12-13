import logging
import fnmatch
from pathlib import Path
from typing import List, Tuple, Set, Dict
import os

class GitignorePattern:
    """Class to handle gitignore pattern matching with caching."""
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
            
        # Convert pattern to regex for faster matching
        self._regex = self._pattern_to_regex(self.pattern)
        
    def _pattern_to_regex(self, pattern: str) -> str:
        """Convert gitignore pattern to regex pattern."""
        if not pattern:
            return r'^$'
            
        # Handle special characters
        regex = fnmatch.translate(pattern)
        
        # Handle directory matches
        if self.is_dir_only:
            regex = regex[:-7] + '(?:/|$)' + regex[-7:]
            
        # Handle absolute paths
        if self.is_absolute:
            regex = '^' + regex
        else:
            regex = '(?:^|/)' + regex
            
        return regex
        
    def matches(self, path: str) -> bool:
        """Check if path matches this pattern."""
        import re
        return bool(re.search(self._regex, path))

class GitignoreManager:
    """Class to manage gitignore patterns and matching."""
    def __init__(self, patterns: List[str]):
        self.patterns: List[GitignorePattern] = []
        self.cached_results: Dict[str, Tuple[bool, str]] = {}
        self.add_patterns(patterns)
        
    def add_patterns(self, patterns: List[str]) -> None:
        """Add new patterns to the manager."""
        for pattern in patterns:
            pattern = pattern.strip()
            if pattern and not pattern.startswith('#'):
                self.patterns.append(GitignorePattern(pattern))
                
    def should_ignore(self, path: str) -> Tuple[bool, str]:
        """Check if path should be ignored. Returns (should_ignore, reason)."""
        # Check cache first
        if path in self.cached_results:
            return self.cached_results[path]
            
        path = path.replace('\\', '/')
        result = self._check_patterns(path)
        self.cached_results[path] = result
        return result
        
    def _check_patterns(self, path: str) -> Tuple[bool, str]:
        """Internal method to check path against all patterns."""
        # Always ignore .git directory
        if '.git' in Path(path).parts:
            return True, "Git repository files"
        
        matched_pattern = None
        should_ignore = False
        
        for pattern in self.patterns:
            if pattern.matches(path):
                matched_pattern = pattern.original
                should_ignore = not pattern.is_negation
                
        if should_ignore and matched_pattern:
            return True, f"Matches pattern: {matched_pattern}"
            
        return False, ""

def parse_gitignore(gitignore_path: Path, include_defaults: bool = True) -> List[str]:
    """Parse .gitignore file and return list of patterns."""
    from core import DEFAULT_NODE_PATTERNS
    
    patterns = DEFAULT_NODE_PATTERNS.copy() if include_defaults else []
    
    if not gitignore_path.exists():
        logging.warning(f"No .gitignore found at {gitignore_path}, using default Node.js patterns")
        return patterns
        
    try:
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.split('#')[0].strip()
                if not line:
                    continue
                patterns.append(line)
                
        logging.debug(f"Parsed {len(patterns)} patterns "
                     f"({len(DEFAULT_NODE_PATTERNS) if include_defaults else 0} defaults + "
                     f"{len(patterns) - (len(DEFAULT_NODE_PATTERNS) if include_defaults else 0)} custom):")
        for pattern in patterns:
            logging.debug(f"  {pattern}")
            
    except Exception as e:
        logging.error(f"Error reading .gitignore: {e}")
        if not include_defaults:
            return []
            
    return patterns

def should_ignore(path: str, ignore_patterns: List[str]) -> Tuple[bool, str]:
    """Check if path matches any gitignore patterns. Returns (should_ignore, reason)."""
    # Use GitignoreManager for efficient pattern matching
    manager = GitignoreManager(ignore_patterns)
    return manager.should_ignore(path)