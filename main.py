import atexit
import os
import sys
import asyncio
from colorama import init, Fore, Style
import json

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.completion import WordCompleter

# Import from our new modules
from config import SYSTEM_PROMPT, EDITOR_PROMPT, DEFAULT_MODEL, EDITOR_MODEL
from utils import clear_console, print_colored, print_welcome_message
from models import get_streaming_response
from commands import (
    handle_add_command, handle_edit_command, handle_new_command, 
    handle_search_command, handle_clear_command, handle_reset_command,
    toggle_diff, handle_history_command, handle_save_command, handle_load_command,
    handle_undo_command, show_current_model, change_model, show_file_content,
    print_files_and_searches_in_memory, handle_ls_command
)

init(autoreset=True)
command_history = FileHistory('.aiconsole_history.txt')
commands = ['/add', '/edit', '/new', '/search', '/clear', '/reset', '/diff', 
            '/history', '/save', '/load', '/undo', '/help', '/model', 
            '/change_model', '/show', '/ls', 'exit']
command_completer = WordCompleter(commands, ignore_case=True)
force_exit = False
interrupt_output = False

# SmartCompleter class removed as it's no longer needed

def delete_history_file():
    """Delete the history file on exit."""
    history_file = '.aiconsole_history.txt'
    if os.path.exists(history_file):
        try:
            os.remove(history_file)
            print_colored("History file deleted.", Fore.GREEN)
        except Exception as e:
            print_colored(f"Error deleting history file: {e}", Fore.RED)

async def main():
    """Main application loop."""
    global interrupt_output, force_exit
    atexit.register(delete_history_file)
    
    # Initialize chat histories
    default_chat_history = [{"role": "system", "content": SYSTEM_PROMPT}]
    editor_chat_history = [{"role": "system", "content": EDITOR_PROMPT}]
    current_model = DEFAULT_MODEL
    
    clear_console()
    print_welcome_message()
    print_files_and_searches_in_memory()

    session = PromptSession(
        history=command_history,
        enable_suspend=True,
        completer=command_completer  # Using simple command completer instead
    )

    while True:
        try:
            if force_exit:
                print_colored("Gracefully exiting...", Fore.YELLOW)
                break
             
            prompt = await session.prompt_async(HTML(f"<ansired>\n\nYou:</ansired> "),
                auto_suggest=AutoSuggestFromHistory(),
                refresh_interval=0.5,
            )

            if interrupt_output:
                print_colored("\nOperation interrupted by user.", Fore.YELLOW)
                interrupt_output = False
                continue

            if prompt is None or prompt.strip() == "":
                continue

            print_files_and_searches_in_memory()

            if prompt.lower() == "exit":
                print_colored(
                    "Thank you for using the Developer Console. Goodbye!", Fore.MAGENTA
                )
                break

            if prompt.startswith("/ls"):
                parts = prompt.split(' ', 1)
                directory = parts[1].strip() if len(parts) > 1 else '.'
                await handle_ls_command(directory)
                continue

            if prompt.startswith("/add "):
                filepaths = prompt.split("/add ", 1)[1].strip().split()
                default_chat_history = await handle_add_command(default_chat_history, *filepaths)
                continue

            if prompt.startswith("/edit "):
                filepaths = prompt.split("/edit ", 1)[1].strip().split()
                default_chat_history, editor_chat_history = await handle_edit_command(
                    default_chat_history, editor_chat_history, filepaths, current_model, EDITOR_MODEL
                )
                continue

            if prompt.startswith("/new "):
                filepaths = prompt.split("/new ", 1)[1].strip().split()
                default_chat_history, editor_chat_history = await handle_new_command(
                    default_chat_history, editor_chat_history, filepaths, current_model, EDITOR_MODEL
                )
                continue

            if prompt.startswith("/search"):
                default_chat_history = await handle_search_command(default_chat_history)
                continue

            if prompt.startswith("/clear"):
                await handle_clear_command()
                continue

            if prompt.startswith("/reset"):
                default_chat_history, editor_chat_history = await handle_reset_command(
                    SYSTEM_PROMPT, EDITOR_PROMPT
                )
                continue

            if prompt.startswith("/diff"):
                toggle_diff()
                continue

            if prompt.startswith("/history"):
                handle_history_command(default_chat_history)
                continue

            if prompt.startswith("/save"):
                await handle_save_command(default_chat_history)
                continue

            if prompt.startswith("/load"):
                loaded_history = await handle_load_command()
                if loaded_history:
                    default_chat_history = loaded_history
                continue

            if prompt.startswith("/undo "):
                filepath = prompt.split("/undo ", 1)[1].strip()
                await handle_undo_command(filepath)
                continue

            if prompt.startswith("/help"):
                await handle_help_command()
                continue

            if prompt.startswith("/model"):
                show_current_model()
                continue

            if prompt.startswith("/change_model"):
                await change_model()
                continue

            if prompt.startswith("/show "):
                filepath = prompt.split("/show ", 1)[1].strip()
                await show_file_content(filepath)
                continue

            print_colored("\n🤖 Assistant:", Fore.BLUE)
            try:
                default_chat_history.append({"role": "user", "content": prompt})
                response = get_streaming_response(default_chat_history, current_model)
                if response is not None:
                    default_chat_history.append({"role": "assistant", "content": response})
                else:
                    print_colored("\nResponse was interrupted and not saved to chat history.", Fore.YELLOW)
            except Exception as e:
                print_colored(f"Error in assistant response: {e}", Fore.RED)
                continue
        except Exception as e:
            print_colored(f"An unexpected error occurred: {e}", Fore.RED)

if __name__ == "__main__":
    asyncio.run(main())
