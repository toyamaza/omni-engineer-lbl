"""File operations for the AI assistant."""

import os
import re
import time
import fnmatch
from pathlib import Path
from colorama import Fore

from utils import print_colored, read_file_content
from . import added_files, undo_history, is_diff_on

# Patterns of files/directories to exclude
EXCLUDE_PATTERNS = [
    '.*', '*.pyc', '__pycache__', 'node_modules', 'venv',
    'build', 'dist', '*.egg-info', '*.o', '*.so', '*.dylib',
    '*.vscode', '*.idea', '*.git'
]

def should_include_file(file_path):
    """Check if a file should be included based on exclusion patterns."""
    file_name = os.path.basename(file_path)
    
    # Check if the file matches any exclusion pattern
    for pattern in EXCLUDE_PATTERNS:
        if fnmatch.fnmatch(file_name, pattern):
            return False
    
    # Check if any parent directory matches exclusion pattern
    path_parts = Path(file_path).parts
    for part in path_parts:
        for pattern in EXCLUDE_PATTERNS:
            if fnmatch.fnmatch(part, pattern):
                return False
    
    return True

def collect_files_recursively(directory_path):
    """Recursively collect files from a directory that match inclusion criteria."""
    collected_files = []
    
    try:
        for root, dirs, files in os.walk(directory_path):
            # Filter out directories that shouldn't be traversed
            dirs[:] = [d for d in dirs if should_include_file(os.path.join(root, d))]
            
            for file in files:
                file_path = os.path.join(root, file)
                if should_include_file(file_path) and os.path.isfile(file_path):
                    collected_files.append(file_path)
    except Exception as e:
        print_colored(f"❌ Error collecting files: {str(e)}", Fore.RED)
    
    return collected_files

def handle_add_command(file_path):
    """Add a file to the list of tracked files."""
    if not os.path.exists(file_path):
        print_colored(f"❌ File {file_path} does not exist.", Fore.RED)
        return

    if os.path.isdir(file_path):
        # If directory, add all files recursively
        files = collect_files_recursively(file_path)
        if not files:
            print_colored(f"❓ No suitable files found in {file_path}", Fore.YELLOW)
            return
        
        for f in files:
            if f not in added_files:
                added_files.append(f)
        
        print_colored(f"📚 Added {len(files)} files from directory {file_path}", Fore.GREEN)
    else:
        # Single file
        if file_path in added_files:
            print_colored(f"⚠️ File {file_path} already added.", Fore.YELLOW)
        else:
            added_files.append(file_path)
            print_colored(f"📄 Added {file_path}", Fore.GREEN)
            
            # Show file content
            show_file_content(file_path)

def handle_edit_command(file_path, new_content):
    """Edit a file's content and save the changes."""
    if not os.path.exists(file_path):
        print_colored(f"❌ File {file_path} does not exist.", Fore.RED)
        return
    
    # Backup original content for undo
    with open(file_path, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    # Save to undo history
    timestamp = str(time.time())
    undo_history[timestamp] = {
        "file_path": file_path,
        "content": original_content,
        "action": "edit"
    }
    
    # Write new content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print_colored(f"✅ File {file_path} updated successfully.", Fore.GREEN)

def handle_new_command(file_path, content):
    """Create a new file with the specified content."""
    # Check if directory exists
    dir_path = os.path.dirname(file_path)
    if dir_path and not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path)
            print_colored(f"📁 Created directory {dir_path}", Fore.BLUE)
        except Exception as e:
            print_colored(f"❌ Failed to create directory {dir_path}: {str(e)}", Fore.RED)
            return
    
    # Check if file already exists
    if os.path.exists(file_path):
        print_colored(f"⚠️ File {file_path} already exists. Use edit command instead.", Fore.YELLOW)
        return
    
    # Create the file
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Add to tracked files
        if file_path not in added_files:
            added_files.append(file_path)
        
        print_colored(f"✨ Created new file {file_path}", Fore.GREEN)
    except Exception as e:
        print_colored(f"❌ Failed to create file {file_path}: {str(e)}", Fore.RED)

def handle_undo_command():
    """Undo the most recent file operation."""
    if not undo_history:
        print_colored("❌ No actions to undo.", Fore.RED)
        return
    
    # Get the most recent action
    timestamp = max(undo_history.keys())
    action_data = undo_history[timestamp]
    
    file_path = action_data["file_path"]
    content = action_data["content"]
    action_type = action_data["action"]
    
    if action_type == "edit":
        # Restore previous content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print_colored(f"↩️ Undid edit to {file_path}", Fore.GREEN)
    
    elif action_type == "new":
        # Remove the file
        try:
            os.remove(file_path)
            if file_path in added_files:
                added_files.remove(file_path)
            print_colored(f"↩️ Undid creation of {file_path}", Fore.GREEN)
        except Exception as e:
            print_colored(f"❌ Failed to undo file creation for {file_path}: {str(e)}", Fore.RED)
    
    # Remove the action from history
    del undo_history[timestamp]

def show_file_content(file_path):
    """Display the content of a file with syntax highlighting."""
    if not os.path.exists(file_path):
        print_colored(f"❌ File {file_path} does not exist.", Fore.RED)
        return
    
    content = read_file_content(file_path)
    extension = os.path.splitext(file_path)[1].lower()
    
    print_colored(f"\n📄 Content of {file_path}:", Fore.CYAN)
    print(content)

def handle_ls_command(directory=None):
    """List files in the given directory."""
    if directory is None:
        directory = os.getcwd()
    
    if not os.path.exists(directory):
        print_colored(f"❌ Directory {directory} does not exist.", Fore.RED)
        return
    
    if not os.path.isdir(directory):
        print_colored(f"❌ {directory} is not a directory.", Fore.RED)
        return
    
    print_colored(f"\n📂 Contents of {directory}:", Fore.CYAN)
    
    try:
        entries = os.listdir(directory)
        
        # Sort: directories first, then files
        dirs = []
        files = []
        
        for entry in entries:
            full_path = os.path.join(directory, entry)
            if os.path.isdir(full_path):
                dirs.append(entry)
            else:
                files.append(entry)
        
        # Print directories
        for d in sorted(dirs):
            print_colored(f"  📁 {d}/", Fore.BLUE)
        
        # Print files
        for f in sorted(files):
            print_colored(f"  📄 {f}", Fore.WHITE)
            
    except Exception as e:
        print_colored(f"❌ Error listing directory: {str(e)}", Fore.RED)
