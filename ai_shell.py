#!/usr/bin/env python3
import os
import sys
import asyncio
import pickle
from colorama import init, Fore, Style

# Import the necessary modules
from utils import print_colored, read_file_content, clear_console, print_welcome_message
from config import SYSTEM_PROMPT, EDITOR_PROMPT, DEFAULT_MODEL, EDITOR_MODEL
from models import get_streaming_response
import commands

init(autoreset=True)

# File to store persistent state between shell invocations
STATE_FILE = os.path.expanduser("~/.ai_shell_state")

def save_state():
    """Save the current state to a file."""
    state = {
        'added_files': commands.added_files,
        'stored_searches': commands.stored_searches,
        'undo_history': commands.undo_history
    }
    try:
        with open(STATE_FILE, 'wb') as f:
            pickle.dump(state, f)
    except Exception as e:
        print_colored(f"Error saving state: {e}", Fore.RED)

def load_state():
    """Load state from file."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'rb') as f:
                state = pickle.load(f)
                # Update the global state variables
                commands.added_files.clear()
                commands.added_files.extend(state.get('added_files', []))
                commands.stored_searches.clear()
                commands.stored_searches.update(state.get('stored_searches', {}))
                commands.undo_history.clear()
                commands.undo_history.update(state.get('undo_history', {}))
        except Exception as e:
            print_colored(f"Error loading state: {e}", Fore.RED)

async def main():
    # Load the previous state (if any)
    load_state()
    
    # Initialize chat history with system prompt
    chat_history = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Get all arguments after the script name as one string
    command = " ".join(sys.argv[1:])
    
    if not command:
        print_welcome_message()
        return
    
    # Process commands
    if command.startswith("/add "):
        filepath = command.split("/add ", 1)[1].strip()
        if filepath:
            commands.handle_add_command(filepath)
            save_state()
        else:
            print_colored("Please specify a file to add. Usage: /add <filepath>", Fore.YELLOW)
    
    elif command.startswith("/edit "):
        filepath = command.split("/edit ", 1)[1].strip()
        if filepath and os.path.exists(filepath):
            # For simplicity, we're just showing that we recognized the command
            print_colored(f"Edit command recognized for {filepath}", Fore.CYAN)
            print_colored("Implement full edit functionality as needed", Fore.CYAN)
            # The actual implementation would involve opening the file, allowing edits, etc.
        else:
            print_colored("Please specify a valid file to edit. Usage: /edit <filepath>", Fore.YELLOW)
    
    elif command.startswith("/new "):
        filepath = command.split("/new ", 1)[1].strip()
        if filepath:
            # For simplicity, we're just showing that we recognized the command
            print_colored(f"New file command recognized for {filepath}", Fore.CYAN)
            print_colored("Implement full new file functionality as needed", Fore.CYAN)
            # The actual implementation would involve prompting for content and creating the file
        else:
            print_colored("Please specify a filepath for the new file. Usage: /new <filepath>", Fore.YELLOW)
    
    elif command.startswith("/search "):
        search_term = command.split("/search ", 1)[1].strip()
        if search_term:
            # Update chat history with search query
            chat_history.append({"role": "user", "content": f"Search for: {search_term}"})
            updated_history = await commands.handle_search_command(chat_history)
            if updated_history:
                chat_history = updated_history
            save_state()
        else:
            print_colored("Please provide a search term.", Fore.YELLOW)
    
    elif command.strip() == "/model":
        commands.show_current_model(DEFAULT_MODEL)
    
    elif command.strip() == "/files" or command.strip() == "/list":
        commands.print_files_and_searches_in_memory()
    
    elif command.strip() == "/clear":
        commands.handle_clear_command()
        save_state()
    
    elif command.strip() == "/reset":
        commands.handle_reset_command()
        # Reset chat history
        chat_history = [{"role": "system", "content": SYSTEM_PROMPT}]
        save_state()
    
    elif command.strip() == "/diff":
        commands.toggle_diff()
    
    elif command.strip() == "/history":
        commands.handle_history_command()
    
    elif command.startswith("/save"):
        commands.handle_save_command()
    
    elif command.startswith("/load"):
        path = command.split("/load ", 1)[1].strip() if " " in command else None
        commands.handle_load_command(path if path else None)
    
    elif command.startswith("/undo"):
        commands.handle_undo_command()
        save_state()
    
    elif command.startswith("/show"):
        # Split to check if there's a filepath provided
        parts = command.split(' ', 1)
        if len(parts) > 1 and parts[1].strip():
            filepath = parts[1].strip()
            commands.show_file_content(filepath)
        else:
            print_colored("Please specify a file to show. Usage: /show <filepath>", Fore.YELLOW)
            if commands.added_files:
                print_colored("\nFiles in memory that you can show:", Fore.CYAN)
                for idx, file in enumerate(commands.added_files, 1):
                    print_colored(f"  {idx}. {file}", Fore.GREEN)
    
    elif command.strip() == "/help":
        print_welcome_message()
    
    else:
        # Treat as a question to the AI
        print_colored("🤖 Assistant:", Fore.BLUE)
        
        # If the command is a question about a file that exists
        if command.startswith("what does ") and " file do" in command:
            potential_file = command.split("what does ")[1].split(" file do")[0].strip()
            if os.path.isfile(potential_file):
                content = read_file_content(potential_file)
                question = f"What does this {potential_file} file do? Here's the content:\n\n{content}"
                chat_history.append({"role": "user", "content": question})
            else:
                chat_history.append({"role": "user", "content": command})
        else:
            chat_history.append({"role": "user", "content": command})
            
        response = get_streaming_response(chat_history, DEFAULT_MODEL)
        if response is not None:
            chat_history.append({"role": "assistant", "content": response})
    
    # Always print a newline at the end to separate from shell prompt
    print()

if __name__ == "__main__":
    asyncio.run(main())
