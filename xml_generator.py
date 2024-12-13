import xml.etree.ElementTree as ET
import xml.dom.minidom
from pathlib import Path
from datetime import datetime
import logging
import mimetypes
from typing import List, Tuple

def create_xml_document(root_dir: Path, files: List[Path], ignored_files: List[Tuple[str, str]], output_file: Path, part: int = None):
    """Create XML document containing file contents and directory structure."""
    root = ET.Element("documents")
    
    # Project metadata
    metadata = ET.SubElement(root, "metadata")
    ET.SubElement(metadata, "root_directory").text = str(root_dir)
    ET.SubElement(metadata, "file_count").text = str(len(files))
    ET.SubElement(metadata, "total_size").text = str(sum(f.stat().st_size for f in files))
    ET.SubElement(metadata, "creation_date").text = datetime.now().isoformat()
    if part is not None:
        ET.SubElement(metadata, "part").text = str(part)

    # Directory structure
    structure = ET.SubElement(root, "directory_structure")
    directories = {}
    for file in files:
        rel_path = file.relative_to(root_dir)
        for parent in rel_path.parents:
            if parent.as_posix() != '.':
                if parent.as_posix() not in directories:
                    dir_elem = ET.SubElement(structure, "directory")
                    dir_elem.set("path", parent.as_posix())
                    dir_elem.set("file_count", "0")
                    directories[parent.as_posix()] = dir_elem
                directories[parent.as_posix()].set(
                    "file_count", 
                    str(int(directories[parent.as_posix()].get("file_count")) + 1)
                )
    
    # Files with contents and metadata
    files_elem = ET.SubElement(root, "files")
    for idx, file_path in enumerate(sorted(files), 1):
        rel_path = file_path.relative_to(root_dir)
        stats = file_path.stat()
        
        file_elem = ET.SubElement(files_elem, "file")
        file_elem.set("index", str(idx))
        file_elem.set("directory", str(rel_path.parent))
        file_elem.set("size", str(stats.st_size))
        file_elem.set("modified", datetime.fromtimestamp(stats.st_mtime).isoformat())
        file_elem.set("extension", rel_path.suffix[1:] if rel_path.suffix else '')
        
        name_elem = ET.SubElement(file_elem, "name")
        name_elem.text = rel_path.name
        
        path_elem = ET.SubElement(file_elem, "path")
        path_elem.text = rel_path.as_posix()
        
        # Try to detect file type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        file_elem.set("mime_type", mime_type or "text/plain")
        
        content_elem = ET.SubElement(file_elem, "content")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content_elem.text = f.read()
        except UnicodeDecodeError:
            logging.warning(f"Skipping content for {file_path} - unable to read as text")
            content_elem.set("error", "Unable to read file as text")
            continue

    # Pretty print XML
    xml_str = xml.dom.minidom.parseString(
        ET.tostring(root, encoding='unicode')
    ).toprettyxml()
    
    # Create output filename
    if part is not None:
        output_path = output_file.with_suffix(f'.part{part}.xml')
    else:
        output_path = output_file
        
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(xml_str)
        
    return output_path