"""State management operations for the AI assistant."""

import json
import os
from colorama import Fore
import pickle
from datetime import datetime

from utils import print_colored
from . import added_files, stored_searches, undo_history

def print_files_and_searches_in_memory():
    """Print the current files and searches stored in memory."""
    if added_files:
        print_colored("\n📁 Files in memory:", Fore.CYAN)
        for file_path in added_files:
            print_colored(f"  - {file_path}", Fore.WHITE)
    else:
        print_colored("\n📁 No files in memory.", Fore.CYAN)
    
    if stored_searches:
        print_colored("\n🔍 Searches in memory:", Fore.CYAN)
        for query in stored_searches:
            print_colored(f"  - {query}", Fore.WHITE)
    else:
        print_colored("\n🔍 No searches in memory.", Fore.CYAN)

def handle_clear_command():
    """Clear the added files and stored searches from memory."""
    global added_files, stored_searches
    added_files.clear()
    stored_searches.clear()
    print_colored("🧹 Cleared all files and searches from memory.", Fore.GREEN)

def handle_reset_command():
    """Reset the program state completely."""
    handle_clear_command()
    undo_history.clear()
    print_colored("🔄 Reset complete. All program state has been cleared.", Fore.GREEN)

def handle_history_command():
    """Show the undo history."""
    if not undo_history:
        print_colored("📜 No undo history available.", Fore.YELLOW)
        return
    
    print_colored("\n📜 Undo History:", Fore.CYAN)
    for timestamp, action in undo_history.items():
        formatted_time = datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
        print_colored(f"  - {formatted_time}: {action}", Fore.WHITE)

def handle_save_command():
    """Save the current state to a file."""
    save_state = {
        "added_files": added_files,
        "stored_searches": stored_searches,
        "undo_history": undo_history
    }
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    save_path = f"assistant_state_{timestamp}.pkl"
    
    try:
        with open(save_path, 'wb') as f:
            pickle.dump(save_state, f)
        print_colored(f"💾 State saved to {save_path}", Fore.GREEN)
    except Exception as e:
        print_colored(f"❌ Failed to save state: {str(e)}", Fore.RED)

def handle_load_command(file_path):
    """Load state from a file."""
    global added_files, stored_searches, undo_history
    
    if not os.path.exists(file_path):
        print_colored(f"❌ File {file_path} does not exist.", Fore.RED)
        return
    
    try:
        with open(file_path, 'rb') as f:
            load_state = pickle.load(f)
        
        added_files = load_state.get("added_files", [])
        stored_searches = load_state.get("stored_searches", {})
        undo_history = load_state.get("undo_history", {})
        
        print_colored(f"📂 State loaded from {file_path}", Fore.GREEN)
        print_files_and_searches_in_memory()
    except Exception as e:
        print_colored(f"❌ Failed to load state: {str(e)}", Fore.RED)
