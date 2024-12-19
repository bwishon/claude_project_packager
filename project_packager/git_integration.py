import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

class GitInfo:
    """Class to extract Git repository information."""
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self._verify_git_repo()

    def _verify_git_repo(self) -> None:
        """Verify the path is a Git repository."""
        if not (self.repo_path / '.git').exists():
            raise ValueError(f"{self.repo_path} is not a Git repository")

    def _run_git_command(self, command: List[str]) -> Tuple[str, Optional[str]]:
        """Run a Git command and return its output."""
        try:
            result = subprocess.run(
                ['git'] + command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip(), None
        except subprocess.CalledProcessError as e:
            return "", f"Git command failed: {e.stderr}"

    def get_recent_commits(self, limit: int = 10) -> List[Dict]:
        """Get recent commit information."""
        format_string = {
            'hash': '%H',
            'author': '%an',
            'author_email': '%ae',
            'date': '%aI',
            'subject': '%s',
            'body': '%b'
        }
        
        format_str = '%x1f'.join(f'%({k}){v}' for k, v in format_string.items())
        
        output, error = self._run_git_command([
            'log',
            f'-{limit}',
            f'--pretty=format:{format_str}',
            '--no-merges'
        ])
        
        if error:
            logging.error(error)
            return []

        commits = []
        for line in output.split('\n'):
            if not line:
                continue
            parts = line.split('\x1f')
            if len(parts) == len(format_string):
                commit = dict(zip(format_string.keys(), parts))
                commits.append(commit)

        return commits

    def get_branch_info(self) -> Dict:
        """Get branch information."""
        current, error = self._run_git_command(['rev-parse', '--abbrev-ref', 'HEAD'])
        if error:
            logging.error(error)
            return {}

        branches, error = self._run_git_command(['branch', '-r'])
        if error:
            logging.error(error)
            return {'current': current}

        return {
            'current': current,
            'remotes': [b.strip() for b in branches.split('\n') if b.strip()]
        }

    def get_file_history(self, file_path: Path) -> Dict:
        """Get history for a specific file."""
        relative_path = file_path.relative_to(self.repo_path)
        
        # Get last commit info
        last_commit, error = self._run_git_command([
            'log',
            '-1',
            '--pretty=format:%H|%an|%ae|%aI|%s',
            str(relative_path)
        ])
        
        if error:
            logging.error(error)
            return {}

        if not last_commit:
            return {}

        # Get blame info
        blame, error = self._run_git_command([
            'blame',
            '--porcelain',
            str(relative_path)
        ])
        
        if error:
            logging.error(error)
            blame_info = {}
        else:
            blame_info = self._parse_blame(blame)

        # Split last commit info
        commit_parts = last_commit.split('|')
        if len(commit_parts) == 5:
            hash, author, email, date, msg = commit_parts
        else:
            return {}

        return {
            'last_commit': {
                'hash': hash,
                'author': author,
                'email': email,
                'date': date,
                'message': msg
            },
            'blame': blame_info
        }

    def _parse_blame(self, blame_output: str) -> Dict:
        """Parse git blame output into a structured format."""
        authors = {}
        for line in blame_output.split('\n'):
            if line.startswith('author '):
                author = line[7:]
                authors[author] = authors.get(author, 0) + 1

        return {
            'line_counts': authors,
            'total_lines': sum(authors.values())
        }

def get_git_metadata(project_path: Path) -> Dict:
    """Get all Git metadata for a project."""
    try:
        git = GitInfo(project_path)
        
        metadata = {
            'repository_info': {
                'recent_commits': git.get_recent_commits(),
                'branches': git.get_branch_info()
            },
            'files': {}
        }

        return metadata

    except ValueError as e:
        logging.warning(f"Git metadata collection failed: {e}")
        return {}
    except Exception as e:
        logging.error(f"Unexpected error collecting Git metadata: {e}")
        return {}