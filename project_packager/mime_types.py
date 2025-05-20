"""MIME type handling and text content detection."""

from pathlib import Path
from typing import Set, Dict

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
    'application/typescript',
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
    'application/x-markdown',
    # Document formats that Claude can understand
    'application/pdf',
    'application/epub+zip',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # docx
    'application/msword',  # doc
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # xlsx
    'application/vnd.ms-excel',  # xls
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',  # pptx
    'application/vnd.ms-powerpoint',  # ppt
    'application/vnd.oasis.opendocument.text',  # odt
    'application/rtf'  # rtf
}

# Files that must match exactly (case-insensitive)
EXACT_FILENAME_MAPPINGS: Dict[str, str] = {
    # Common config files
    '.gitignore': 'text/plain',
    '.dockerignore': 'text/plain',
    '.editorconfig': 'text/plain',
    '.nvmrc': 'text/plain',
    '.npmrc': 'text/plain',
    '.eslintrc': 'text/plain',
    '.prettierrc': 'text/plain',
    '.babelrc': 'text/plain',
    '.browserslistrc': 'text/plain',
    '.dev.vars': 'text/plain',
    '.env.local': 'text/plain',
    '.env.development': 'text/plain',
    '.env.test': 'text/plain',
    '.env.production': 'text/plain',
    # Special files
    'Makefile': 'text/plain',
    'Dockerfile': 'text/plain',
    'LICENSE': 'text/plain',
    'LICENCE': 'text/plain',
    'COPYING': 'text/plain',
    'README': 'text/plain',
    'CHANGELOG': 'text/plain',
    'CHANGES': 'text/plain',
    'NEWS': 'text/plain',
    '.ruby-version': 'text/plain',
    '.python-version': 'text/plain',
    '.node-version': 'text/plain',
    'requirements.txt': 'text/plain',
    'Pipfile': 'text/plain',
    '.prettierignore': 'text/plain',
}

# Extensions to match (without leading dot)
EXTENSION_MAPPINGS: Dict[str, str] = {
    # Data formats
    'json': 'application/json',
    'jsonc': 'application/json',
    'yml': 'application/x-yaml',
    'yaml': 'application/x-yaml',
    'toml': 'application/toml',
    'md': 'application/x-markdown',
    # Document formats
    'pdf': 'application/pdf',
    'epub': 'application/epub+zip', 
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'doc': 'application/msword',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'xls': 'application/vnd.ms-excel',
    'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'ppt': 'application/vnd.ms-powerpoint',
    'odt': 'application/vnd.oasis.opendocument.text',
    'rtf': 'application/rtf',
    # Programming languages
    'php': 'application/x-httpd-php',
    'sh': 'application/x-sh',
    'rb': 'application/x-ruby',
    'pl': 'application/x-perl',
    'py': 'application/x-python',
    # Web technologies
    'js': 'application/javascript',
    'ts': 'application/typescript',
    'tsx': 'application/typescript',
    'jsx': 'application/javascript',
    'es': 'application/ecmascript',
    'graphql': 'application/graphql',
    'svelte': 'application/javascript',
    'mermaid': 'text/mermaid',  
    # Common text files
    'txt': 'text/plain',
    'ini': 'text/plain',
    'cfg': 'text/plain',
    'conf': 'text/plain',
    'config': 'text/plain',
    'properties': 'text/plain',
    'lock': 'text/plain',
    'env': 'text/plain',
    'req': 'text/plain',
    'vars': 'text/plain',
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
        
    # Register extensions
    for ext, mime_type in EXTENSION_MAPPINGS.items():
        mimetypes.add_type(mime_type, f'.{ext}')

def get_mime_type(file_path: Path) -> str:
    """Get MIME type for a file with enhanced detection."""
    import mimetypes
    setup_mime_types()
    
    # First check for exact filename matches (case-insensitive)
    lower_name = file_path.name.lower()
    for pattern, mime_type in EXACT_FILENAME_MAPPINGS.items():
        if lower_name == pattern.lower():
            return mime_type
            
    # Then check extension-based mapping
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if not mime_type:
        # Check single extension
        ext = file_path.suffix.lower().lstrip('.')
        if ext in EXTENSION_MAPPINGS:
            return EXTENSION_MAPPINGS[ext]
            
    return mime_type or 'application/octet-stream'

def get_file_content(file_path: Path, mime_type: str) -> tuple[str, bool, str]:
    """Read file content with smart encoding detection."""
    import base64
    
    # List of document MIME types that should always be treated as binary
    document_binary_types = {
        'application/pdf', 
        'application/epub+zip',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'application/vnd.ms-powerpoint',
        'application/vnd.oasis.opendocument.text',
        'application/rtf'
    }
    
    # Always handle document formats as binary, regardless of is_text_mime_type result
    if mime_type in document_binary_types or not is_text_mime_type(mime_type):
        try:
            with open(file_path, 'rb') as f:
                content = base64.b64encode(f.read()).decode('ascii')
            return content, True, ""
        except Exception as e:
            return "", True, f"Error reading binary file: {str(e)}"
            
    # Try to read as text first
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read(), False, ""
    except UnicodeDecodeError:
        # Silently fall back to binary for text files with encoding issues
        try:
            with open(file_path, 'rb') as f:
                content = base64.b64encode(f.read()).decode('ascii')
            return content, True, ""  # No error message for fallback
        except Exception as e:
            return "", True, f"Error in base64 fallback: {str(e)}"
    except Exception as e:
        return "", False, f"Error reading text file: {str(e)}"