# Project Packager

A Python utility for packaging project files into XML format for analysis by large language models like Claude. The tool intelligently handles file scanning, content extraction, and batch processing while respecting `.gitignore` rules.

## Overview

Project Packager is designed to help you prepare your codebase for analysis by large language models. It:
- Scans your project directory and creates a structured XML representation
- Respects `.gitignore` patterns to exclude unnecessary files
- Handles binary files and large codebases intelligently
- Preserves directory structure and file metadata
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
  -o, --output          Output XML file name (default: claude_project.xml)
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
project-packager /path/to/project -o output.xml
```

Enable verbose logging with file output:
```bash
project-packager . -v --log-file=packager.log
```

## Features

### Smart File Processing
- Uses Git's `check-ignore` for robust ignore pattern handling
- Detects and skips binary files automatically
- Handles large files through efficient chunked reading
- Processes files in batches to respect token limits

### Comprehensive Metadata
- File system structure preservation
- File metadata (size, modification time, MIME type)
- Directory statistics and file counts
- Detailed processing logs

### Robust Error Handling
- Graceful handling of encoding issues
- Safe file writing with atomic operations
- Detailed error reporting and logging
- XML validation before output

## Output Format

The tool generates an XML document with the following structure:

```xml
<?xml version="1.0" encoding="utf-8"?>
<documents>
    <metadata>
        <root_directory>/path/to/your/project</root_directory>
        <file_count>42</file_count>
        <total_size>123456</total_size>
        <creation_date>2024-12-18T11:22:00.357677</creation_date>
    </metadata>
    <directory_structure>
        <directory path="src" file_count="15"/>
        <directory path="src/utils" file_count="5"/>
        <directory path="tests" file_count="8"/>
    </directory_structure>
    <files>
        <file index="1" directory="src" size="1234" modified="2024-12-18T10:00:00" extension="py" mime_type="text/x-python">
            <name>main.py</name>
            <path>src/main.py</path>
            <content>#!/usr/bin/env python3
                
def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()</content>
        </file>
        <!-- Additional files... -->
    </files>
</documents>
```

## File Handling

The tool automatically:
- Respects `.gitignore` patterns using Git's native ignore checking
- Skips binary files (executables, images, etc.)
- Handles large files by reading in chunks
- Splits output into multiple files if needed to respect token limits
- Preserves file metadata and directory structure

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
- Git (for `.gitignore` support)

## License

This project is licensed under the Apache License 2.0.

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