#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import xml.dom.minidom
from pathlib import Path
from datetime import datetime
import logging
import mimetypes
from typing import List, Tuple, Dict
import os
from itertools import chain

class CDATATreeBuilder(ET.TreeBuilder):
    """Custom TreeBuilder that handles CDATA sections."""
    def __init__(self):
        super().__init__()
        self._data_parts = []

    def start(self, tag, attrs):
        self._data_parts = []  # Reset data parts for new element
        return super().start(tag, attrs)

    def data(self, data):
        self._data_parts.append(data)

    def end(self, tag):
        text = ''.join(self._data_parts)
        if text and tag == 'content':  # Only wrap content elements in CDATA
            elem = super().end(tag)
            elem.text = f'<![CDATA[{text}]]>'
            return elem
        return super().end(tag)

def get_mime_type(file_path: Path) -> str:
    """Get MIME type for file with enhanced detection."""
    if not mimetypes.inited:
        mimetypes.init()
        
    # Add common development file types
    mimetypes.add_type('text/markdown', '.md')
    mimetypes.add_type('text/x-python', '.py')
    mimetypes.add_type('text/javascript', '.js')
    mimetypes.add_type('text/typescript', '.ts')
    mimetypes.add_type('text/x-yaml', '.yml')
    mimetypes.add_type('text/x-yaml', '.yaml')
    
    mime_type, _ = mimetypes.guess_type(str(file_path))
    
    if not mime_type:
        ext = file_path.suffix.lower()
        if ext in {'.svelte', '.vue'}:
            mime_type = 'text/plain'
        elif ext in {'.json', '.jsonc'}:
            mime_type = 'application/json'
        elif ext in {'.tsx', '.jsx'}:
            mime_type = 'text/typescript'
    
    return mime_type or 'text/plain'

def build_directory_structure(files: List[Path], root_dir: Path) -> Dict[str, int]:
    """Build directory structure with file counts."""
    directories = {}
    
    for file_path in files:
        try:
            rel_path = file_path.relative_to(root_dir)
            for parent in chain([rel_path.parent], rel_path.parents):
                if parent.as_posix() != '.':
                    dir_path = parent.as_posix()
                    directories[dir_path] = directories.get(dir_path, 0) + 1
        except ValueError:
            logging.warning(f"Could not determine relative path for {file_path}")
            continue
            
    return directories

def create_metadata_element(root_dir: Path, files: List[Path], part: int = None) -> ET.Element:
    """Create metadata section of XML document."""
    metadata = ET.Element("metadata")
    
    try:
        total_size = sum(f.stat().st_size for f in files)
    except OSError as e:
        logging.error(f"Error calculating total size: {e}")
        total_size = 0
    
    ET.SubElement(metadata, "root_directory").text = str(root_dir)
    ET.SubElement(metadata, "file_count").text = str(len(files))
    ET.SubElement(metadata, "total_size").text = str(total_size)
    ET.SubElement(metadata, "creation_date").text = datetime.now().isoformat()
    
    if part is not None:
        ET.SubElement(metadata, "part").text = str(part)
        
    return metadata

def create_directory_element(directories: Dict[str, int]) -> ET.Element:
    """Create directory structure section of XML document."""
    structure = ET.Element("directory_structure")
    
    for dir_path, file_count in sorted(directories.items()):
        dir_elem = ET.SubElement(structure, "directory")
        dir_elem.set("path", dir_path)
        dir_elem.set("file_count", str(file_count))
        
    return structure

def create_files_element(root_dir: Path, files: List[Path]) -> ET.Element:
    """Create files section of XML document."""
    files_elem = ET.Element("files")
    
    for idx, file_path in enumerate(sorted(files), 1):
        try:
            rel_path = file_path.relative_to(root_dir)
            stats = file_path.stat()
            mime_type = get_mime_type(file_path)
            
            file_elem = ET.SubElement(files_elem, "file")
            file_elem.set("index", str(idx))
            file_elem.set("directory", str(rel_path.parent))
            file_elem.set("size", str(stats.st_size))
            file_elem.set("modified", datetime.fromtimestamp(stats.st_mtime).isoformat())
            file_elem.set("extension", rel_path.suffix[1:] if rel_path.suffix else '')
            file_elem.set("mime_type", mime_type)
            
            ET.SubElement(file_elem, "name").text = rel_path.name
            ET.SubElement(file_elem, "path").text = rel_path.as_posix()
            
            content_elem = ET.SubElement(file_elem, "content")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content_elem.text = f.read()
            except UnicodeDecodeError:
                logging.warning(f"Skipping content for {file_path} - unable to read as text")
                content_elem.set("error", "Unable to read file as text")
                continue
            except OSError as e:
                logging.error(f"Error reading {file_path}: {e}")
                content_elem.set("error", f"File read error: {str(e)}")
                continue
                
        except Exception as e:
            logging.error(f"Error processing {file_path}: {e}")
            continue
            
    return files_elem

def write_xml(root: ET.Element, output_path: Path) -> None:
    """Write XML to file with CDATA handling."""
    temp_path = output_path.with_suffix('.tmp')
    try:
        # Convert to string, keeping original text content
        xml_str = ET.tostring(root, encoding='unicode')
        
        # Create new tree with CDATA handling
        parser = ET.XMLParser(target=CDATATreeBuilder())
        new_root = ET.XML(xml_str, parser=parser)
        
        # Convert back to string with CDATA preserved
        final_xml = ET.tostring(new_root, encoding='unicode')
        
        # Pretty print
        dom = xml.dom.minidom.parseString(final_xml)
        pretty_xml = dom.toprettyxml(indent='  ', encoding='utf-8')
        
        # Write to temporary file first
        with open(temp_path, 'wb') as f:
            f.write(pretty_xml)
            
        # Rename temporary file to final output
        try:
            temp_path.replace(output_path)
        except OSError:
            if output_path.exists():
                output_path.unlink()
            temp_path.rename(output_path)
            
    except Exception as e:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        raise ValueError(f"Failed to write XML file: {e}")

def create_xml_document(root_dir: Path, files: List[Path], ignored_files: List[Tuple[str, str]], 
                       output_file: Path, part: int = None) -> Path:
    """Create XML document containing file contents and directory structure."""
    try:
        root = ET.Element("documents")
        
        # Add metadata section
        root.append(create_metadata_element(root_dir, files, part))
        
        # Build and add directory structure
        directories = build_directory_structure(files, root_dir)
        root.append(create_directory_element(directories))
        
        # Add files section
        root.append(create_files_element(root_dir, files))
        
        # Create output filename
        if part is not None:
            output_path = output_file.with_suffix(f'.part{part}.xml')
        else:
            output_path = output_file
            
        # Write XML to file
        write_xml(root, output_path)
        
        return output_path
        
    except Exception as e:
        logging.error(f"Failed to create XML document: {e}")
        raise