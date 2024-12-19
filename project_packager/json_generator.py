import json
import base64
from pathlib import Path
from datetime import datetime
import logging
import mimetypes
from typing import List, Tuple, Dict
import os
from .mime_types import get_mime_type, get_file_content

def build_directory_structure(files: List[Path], root_dir: Path) -> List[Dict]:
    """Build directory structure with file counts."""
    directories = {}
    
    for file_path in files:
        try:
            rel_path = file_path.relative_to(root_dir)
            for parent in rel_path.parents:
                if parent.as_posix() != '.':
                    dir_path = parent.as_posix()
                    directories[dir_path] = directories.get(dir_path, 0) + 1
        except ValueError:
            logging.warning(f"Could not determine relative path for {file_path}")
            continue
            
    return [{"path": path, "file_count": count} for path, count in sorted(directories.items())]

def create_metadata(root_dir: Path, files: List[Path], part: int = None) -> Dict:
    """Create metadata section of JSON document."""
    metadata = {
        "root_directory": str(root_dir),
        "file_count": len(files),
        "total_size": sum(f.stat().st_size for f in files),
        "creation_date": datetime.now().isoformat()
    }
    
    if part is not None:
        metadata["part"] = part
        
    return metadata

def create_files_section(root_dir: Path, files: List[Path]) -> List[Dict]:
    """Create files section of JSON document."""
    file_list = []
    
    for idx, file_path in enumerate(sorted(files), 1):
        try:
            rel_path = file_path.relative_to(root_dir)
            stats = file_path.stat()
            mime_type = get_mime_type(file_path)
            
            file_data = {
                "index": idx,
                "directory": str(rel_path.parent),
                "name": rel_path.name,
                "path": rel_path.as_posix(),
                "size": stats.st_size,
                "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                "extension": rel_path.suffix[1:] if rel_path.suffix else "",
                "mime_type": mime_type
            }
            
            content, is_base64, error = get_file_content(file_path, mime_type)
            if error:
                logging.warning(f"Issue with {file_path}: {error}")
                file_data["error"] = error
            elif is_base64:
                file_data["content_base64"] = content
            else:
                file_data["content"] = content
                
            file_list.append(file_data)
                
        except Exception as e:
            logging.error(f"Error processing {file_path}: {e}")
            continue
            
    return file_list

def create_json_document(root_dir: Path, files: List[Path], ignored_files: List[Tuple[str, str]], 
                       output_file: Path, part: int = None) -> Path:
    """Create JSON document containing file contents and directory structure."""
    try:
        data = {
            "metadata": create_metadata(root_dir, files, part),
            "directory_structure": build_directory_structure(files, root_dir),
            "files": create_files_section(root_dir, files)
        }
        
        # Create output filename
        if part is not None:
            output_path = output_file.with_suffix(f'.part{part}.json')
        else:
            output_path = output_file.with_suffix('.json')
            
        # Write JSON to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return output_path
        
    except Exception as e:
        logging.error(f"Failed to create JSON document: {e}")
        raise