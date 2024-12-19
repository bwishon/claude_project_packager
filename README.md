# Project Packager

A Python utility for packaging project files into JSON format for analysis by large language models like Claude. The tool intelligently handles file scanning, content extraction, Git metadata collection, and batch processing while respecting `.gitignore` rules.

## Overview

Project Packager is designed to help you prepare your codebase for analysis by large language models. It:
- Scans your project directory and creates a structured JSON representation
- Handles both text and supported binary files (images, audio, video)
- Respects `.gitignore` patterns to exclude unnecessary files
- Preserves directory structure and file metadata
- Collects Git repository information including recent commits and branches
- Splits output into manageable chunks if needed

## Installation

### Using pip (Recommended)
```bash
pip install project-packager
```

### Using Poetry
```bash
git clone https://github.com/yourusername/project-packager.git
cd project-packager
poetry install
```

## Usage

### Basic Usage
```bash
project-packager [project_dir] [options]
```

If no directory is specified, the current directory will be used.

### Command Line Options
```
Arguments:
  project_dir            Project directory to package (default: current directory)

Options:
  -o, --output          Output JSON file name (default: claude_project.json)
  -v, --verbose         Enable verbose output
  -vv, --very-verbose   Enable very verbose debug output
  --log-file FILE       Write detailed logs to specified file
  --max-file-size BYTES Maximum size of individual files (default: 100000 bytes)
```

### Examples

Package the current directory:
```bash
project-packager
```

Package a specific project with custom output:
```bash
project-packager /path/to/project -o output.json
```

Enable verbose logging with file output:
```bash
project-packager . -v --log-file=packager.log
```

## Features

### Smart File Processing
- Uses Git's `check-ignore` for robust ignore pattern handling
- Intelligently processes binary files:
  - Base64 encodes supported formats (images, audio, video)
  - Automatically skips unsupported binary files
- Handles large files through efficient chunked reading
- Processes files in batches to respect token limits

### Git Integration
- Automatically detects Git repositories
- Collects recent commit history
- Includes branch information
- Captures repository metadata
- Works seamlessly without Git for non-repository directories

### Supported Binary Formats
The tool automatically detects and includes these binary formats:
- Images: .png, .jpg, .jpeg, .gif
- Audio: .mp3, .wav, .ogg
- Video: .mp4, .avi, .mov

These files are base64 encoded in the output JSON for compatibility with large language models.

### Comprehensive Metadata
- File system structure preservation
- File metadata (size, modification time, MIME type)
- Directory statistics and file counts
- Git repository information
- Detailed processing logs

### Robust Error Handling
- Graceful handling of encoding issues
- Safe file writing with atomic operations
- Detailed error reporting and logging
- JSON schema validation

## Output Format

The tool generates a JSON document with the following structure:

```json
{
  "metadata": {
    "root_directory": "/path/to/your/project",
    "file_count": 42,
    "total_size": 123456,
    "creation_date": "2024-12-18T11:22:00.357677",
    "git": {
      "repository_info": {
        "recent_commits": [
          {
            "hash": "abc123...",
            "author": "Developer Name",
            "author_email": "dev@example.com",
            "date": "2024-12-18T10:00:00",
            "subject": "Commit message",
            "body": "Full commit description"
          }
        ],
        "branches": {
          "current": "main",
          "remotes": ["origin/main", "origin/develop"]
        }
      }
    }
  },
  "directory_structure": [
    {
      "path": "src",
      "file_count": 15
    },
    {
      "path": "src/utils",
      "file_count": 5
    }
  ],
  "files": [
    {
      "index": 1,
      "directory": "src",
      "name": "main.py",
      "path": "src/main.py",
      "size": 1234,
      "modified": "2024-12-18T10:00:00",
      "extension": "py",
      "mime_type": "text/x-python",
      "content": "#!/usr/bin/env python3\n\ndef main():\n    print(\"Hello, World!\")\n\nif __name__ == \"__main__\":\n    main()"
    },
    {
      "index": 2,
      "directory": "assets",
      "name": "logo.png",
      "path": "assets/logo.png",
      "size": 5678,
      "modified": "2024-12-18T10:00:00",
      "extension": "png",
      "mime_type": "image/png",
      "content_base64": "iVBORw0KGgoAAAANSUhEUgAA..."
    }
  ]
}
```

Text files use the `content` field, while binary files use `content_base64` for their base64-encoded data.

## File Handling

The tool automatically:
- Respects `.gitignore` patterns using Git's native ignore checking
- Base64 encodes supported binary files (images, audio, video)
- Skips unsupported binary files
- Handles large files by reading in chunks
- Splits output into multiple files if needed to respect token limits
- Preserves file metadata and directory structure

### MIME Type Detection

The tool uses a sophisticated MIME type detection system to determine how to handle different files:

#### Core Text MIME Types
Automatically handles these non-standard text MIME types as text content:
- Data formats: application/json, application/x-yaml, application/yaml, application/toml, application/xml
- Web technologies: application/javascript, application/ecmascript, application/graphql
- Programming languages: application/x-httpd-php, application/x-sh, application/x-ruby, application/x-perl, application/x-python
- Config and documentation: application/x-config, application/x-markdown

#### Special Filename Handling
Recognizes common configuration files regardless of extension:
- Git files: .gitignore, .dockerignore
- Config files: .editorconfig, .eslintrc, .prettierrc, .babelrc
- Environment files: .env, .env.local, .env.development
- Project files: Makefile, Dockerfile, LICENSE, README
- Version files: .ruby-version, .python-version, .node-version

#### Extension-Based Detection
Maps specific extensions to appropriate MIME types:
- Data: .json, .jsonc, .yml, .yaml, .toml, .md
- Programming: .php, .sh, .rb, .pl, .py
- Config: .txt, .ini, .cfg, .conf, .properties, .lock, .env

#### Binary Detection
Implements a two-step binary file detection:
1. Checks against known binary extensions
2. Attempts UTF-8 decoding of the first chunk
   - If decoding succeeds: handles as text
   - If decoding fails: treats as binary

#### Customization
MIME type handling can be extended by:
1. Adding entries to CORE_TEXT_MIME_TYPES in mime_types.py
2. Updating EXACT_FILENAME_MAPPINGS for specific files
3. Adding new extensions to EXTENSION_MAPPINGS
4. Modifying the binary detection logic in get_file_content()

## Development

To contribute to the project:

1. Fork the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```
3. Install development dependencies:
   ```bash
   poetry install
   ```
4. Make your changes
5. Run tests:
   ```bash
   pytest
   ```
6. Submit a pull request

## Requirements

- Python 3.8 or higher
- Git (optional, for Git metadata and `.gitignore` support)

## License

```
Copyright 2024 William Wishon

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```