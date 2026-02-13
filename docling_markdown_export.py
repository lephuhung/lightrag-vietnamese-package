#!/usr/bin/env python3
"""
Custom Document Processor with Docling Markdown Export
Saves markdown files from Docling processing to a dedicated folder

Usage: This module patches the LightRAG document processing to save markdown files
"""

import os
from pathlib import Path
from typing import Optional

# Configuration
MARKDOWN_OUTPUT_DIR = "./docling_markdown"  # Folder to save markdown files


def ensure_markdown_dir():
    """Ensure markdown output directory exists"""
    Path(MARKDOWN_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


def save_docling_markdown(filename: str, markdown_content: str) -> str:
    """
    Save markdown content from Docling to file
    
    Args:
        filename: Original filename (e.g., "document.pdf")
        markdown_content: Markdown content from Docling
    
    Returns:
        Path to saved markdown file
    """
    ensure_markdown_dir()
    
    # Create markdown filename from original
    base_name = Path(filename).stem
    markdown_filename = f"{base_name}.md"
    output_path = Path(MARKDOWN_OUTPUT_DIR) / markdown_filename
    
    # Save content
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"   [DOC-LING] Markdown saved: {output_path}")
    return str(output_path)


def process_with_docling_save_markdown(file_path: str) -> str:
    """
    Process document with Docling and save markdown to file
    
    This function wraps the docling conversion and saves the output
    
    Args:
        file_path: Path to document file
    
    Returns:
        Markdown content (same as original)
    """
    from docling.document_converter import DocumentConverter
    
    # Convert with docling
    converter = DocumentConverter()
    result = converter.convert(file_path)
    markdown_content = result.document.export_to_markdown()
    
    # Save to file
    save_docling_markdown(file_path, markdown_content)
    
    return markdown_content


# Patch function for LightRAG
def patch_docling_processing():
    """
    Patch LightRAG's docling processing to save markdown files
    Call this before starting LightRAG server
    """
    try:
        # Import LightRAG's document routes
        from lightrag.api.routers import document_routes
        
        # Save original function
        document_routes._original_convert_with_docling = document_routes._convert_with_docling
        
        # Replace with our custom function
        def _convert_with_docling_patched(file_path: Path) -> str:
            """Patched version that saves markdown"""
            from docling.document_converter import DocumentConverter
            
            converter = DocumentConverter()
            result = converter.convert(file_path)
            markdown_content = result.document.export_to_markdown()
            
            # Save markdown file
            save_docling_markdown(str(file_path), markdown_content)
            
            return markdown_content
        
        document_routes._convert_with_docling = _convert_with_docling_patched
        
        print(f"✓ Docling processing patched")
        print(f"  Markdown files will be saved to: {os.path.abspath(MARKDOWN_OUTPUT_DIR)}")
        
    except Exception as e:
        print(f"⚠ Could not patch docling processing: {e}")
        print(f"  Markdown files will not be saved")


if __name__ == "__main__":
    # Test the patch
    print("Testing Docling markdown export...")
    ensure_markdown_dir()
    print(f"Markdown output directory: {os.path.abspath(MARKDOWN_OUTPUT_DIR)}")
    print("✓ Ready to save markdown files from Docling processing")
