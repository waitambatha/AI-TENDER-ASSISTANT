#!/usr/bin/env python
"""
Script to fix misplaced uploaded files and move them to the correct media directory.
Run this if files are uploaded to the wrong location.
"""

import os
import shutil
from pathlib import Path

def fix_upload_paths():
    """Move files from documents/ to media/documents/"""
    
    project_root = Path(__file__).parent
    wrong_dir = project_root / 'documents'
    correct_dir = project_root / 'media' / 'documents'
    
    # Ensure correct directory exists
    correct_dir.mkdir(parents=True, exist_ok=True)
    
    if wrong_dir.exists():
        moved_files = []
        for file_path in wrong_dir.glob('*.pdf'):
            if file_path.is_file():
                dest_path = correct_dir / file_path.name
                if not dest_path.exists():
                    shutil.move(str(file_path), str(dest_path))
                    moved_files.append(file_path.name)
                    print(f"Moved: {file_path.name}")
        
        if moved_files:
            print(f"Successfully moved {len(moved_files)} files to correct location")
        else:
            print("No files needed to be moved")
    else:
        print("No wrong directory found")

if __name__ == "__main__":
    fix_upload_paths()
