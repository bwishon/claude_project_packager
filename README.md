# Project Packager

A Python utility for packaging project files into XML format for analysis by large language models like Claude. The tool intelligently handles file scanning, content extraction, and batch processing while respecting `.gitignore` rules.

## Features

- **Smart File Processing**
  - Uses Git's `check-ignore` for robust ignore pattern handling
  - Detects and skips binary files automatically
  - Handles large files through efficient chunked reading
  - Processes files in batches to respect token limits

- **Comprehensive Metadata**
  - File system structure preservation
  - File metadata (size, modification time, MIME type)
  - Directory statistics and file counts
  - Detailed processing logs

- **Robust Error Handling**
  - Graceful handling of encoding issues
  - Safe file writing with atomic operations
  - Detailed error reporting and logging
  - XML validation before output

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd project-packager
```

2. Install dependencies:
```bash
pip install tqdm
```

## Usage

Basic usage:
```bash
python -m project_packager [project_dir] [options]
```

Command line options:
```
Arguments:
  project_dir            Project directory to package (default: current directory)

Options:
  -o, --output          Output XML file name (default: claude_project.xml)
  -v, --verbose         Enable verbose output
  --log-file FILE       Write detailed logs to specified file
  --max-file-size BYTES Maximum size of individual files (default: 100000 bytes)
```

## Output Format

The tool generates an XML document with the following structure:

```xml
<documents>
  <metadata>
    <root_directory>...</root_directory>
    <file_count>...</file_count>
    <total_size>...</total_size>
    <creation_date>...</creation_date>
  </metadata>
  <directory_structure>
    <directory path="..." file_count="..."/>
    ...
  </directory_structure>
  <files>
    <file index="..." directory="..." size="..." modified="..." extension="..." mime_type="...">
      <name>...</name>
      <path>...</path>
      <content>...</content>
    </file>
    ...
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

The project is structured into several modules:

- `core.py`: Core configuration and argument parsing
- `file_processing.py`: File scanning and batch processing
- `gitignore.py`: Git ignore pattern handling
- `xml_generator.py`: XML document generation
- `main.py`: Main execution flow

## Error Handling

The tool provides detailed error handling for common issues:
- Invalid file encodings
- File read/write errors
- Git command failures
- XML validation errors

Errors are logged appropriately with detailed messages when running in verbose mode.

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.
CopyCopyright 2024 William Wishon

```
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
