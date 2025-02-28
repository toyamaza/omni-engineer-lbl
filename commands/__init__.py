"""Commands module for the AI assistant."""

# Global state shared across modules
added_files = []
stored_searches = {}
undo_history = {}
is_diff_on = True

# Import and expose all command handlers
from .file_operations import (
    should_include_file,
    collect_files_recursively,
    handle_add_command,
    handle_edit_command,
    handle_new_command,
    handle_undo_command,
    show_file_content,
    handle_ls_command,
)

from .search_operations import handle_search_command

from .state_management import (
    handle_clear_command,
    handle_reset_command,
    handle_history_command,
    handle_save_command,
    handle_load_command,
    print_files_and_searches_in_memory,
)

from .ui_commands import (
    toggle_diff,
    show_current_model,
    change_model,
)

__all__ = [
    # Global state variables
    'added_files', 'stored_searches', 'undo_history', 'is_diff_on',
    
    # File operations
    'should_include_file', 'collect_files_recursively', 'handle_add_command',
    'handle_edit_command', 'handle_new_command', 'handle_undo_command',
    'show_file_content', 'handle_ls_command',
    
    # Search operations
    'handle_search_command',
    
    # State management
    'handle_clear_command', 'handle_reset_command', 'handle_history_command',
    'handle_save_command', 'handle_load_command', 'print_files_and_searches_in_memory',
    
    # UI commands
    'toggle_diff', 'show_current_model', 'change_model',
]
