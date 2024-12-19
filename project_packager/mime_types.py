"""MIME type handling and text content detection."""

from pathlib import Path
from typing import Set

# Core text MIME types that don't start with text/
CORE_TEXT_MIME_TYPES: Set[str] = {
    # Data formats
    'application/json',
    'application/ld+json',  # JSON-LD
    'application/x-yaml',
    'application/yaml',
    'application/toml',
    'application/xml',
    # Web technologies
    'application/javascript',
    'application/ecmascript',
    'application/graphql',
    # Programming languages
    'application/x-httpd-php',
    'application/x-sh',
    'application/x-ruby',
    'application/x-perl',
    'application/x-python',
    # Config and documentation
    'application/x-config',
    'application/x-markdown'
}

# Additional file extension to MIME type mappings
EXTRA_MIME_MAPPINGS = {
    '.json': 'application/json',
    '.jsonc': 'application/json',
    '.yml': 'application/x-yaml',
    '.yaml': 'application/x-yaml',
    '.toml': 'application/toml',
    '.md': 'application/x-markdown',
    '.php': 'application/x-httpd-php',
    '.sh': 'application/x-sh',
    '.rb': 'application/x-ruby',
    '.pl': 'application/x-perl',
    '.py': 'application/x-python'
}

def is_text_mime_type(mime_type: str, additional_types: Set[str] = None) -> bool:
    """Determine if a MIME type represents text content."""
    if mime_type.startswith('text/'):
        return True
    if mime_type in CORE_TEXT_MIME_TYPES:
        return True
    if additional_types and mime_type in additional_types:
        return True
    return False

def setup_mime_types() -> None:
    """Register additional MIME type mappings."""
    import mimetypes
    if not mimetypes.inited:
        mimetypes.init()
    for ext, mime_type in EXTRA_MIME_MAPPINGS.items():
        mimetypes.add_type(mime_type, ext)

def get_mime_type(file_path: Path) -> str:
    """Get MIME type for a file with enhanced detection."""
    import mimetypes
    setup_mime_types()
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if not mime_type:
        ext = file_path.suffix.lower()
        if ext in EXTRA_MIME_MAPPINGS:
            return EXTRA_MIME_MAPPINGS[ext]
    return mime_type or 'application/octet-stream'

def get_file_content(file_path: Path, mime_type: str) -> tuple[str, bool, str]:
    """Read file content with smart encoding detection."""
    import base64
    if not is_text_mime_type(mime_type):
        try:
            with open(file_path, 'rb') as f:
                content = base64.b64encode(f.read()).decode('ascii')
            return content, True, ""
        except Exception as e:
            return "", True, f"Error reading binary file: {str(e)}"
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read(), False, ""
    except UnicodeDecodeError:
        pass
    except Exception as e:
        return "", False, f"Error reading text file: {str(e)}"
    try:
        with open(file_path, 'rb') as f:
            content = base64.b64encode(f.read()).decode('ascii')
        return content, True, "Fallback to base64 due to encoding issues"
    except Exception as e:
        return "", True, f"Error in base64 fallback: {str(e)}"