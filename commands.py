import os
import json
import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from colorama import Fore, Style  # Added Style import here

from duckduckgo_search import AsyncDDGS
from utils import print_colored, read_file_content, write_file_content, is_text_file, display_diff
from config import FILE_TEMPLATES
from models import client, get_streaming_response

# Global variables for state management
added_files = []
stored_searches = {}
undo_history = {}
is_diff_on = True

# Replace the should_exclude_file function with this:
def should_include_file(filepath, explicitly_requested=False):
    """
    Check if a file should be included when adding.
    
    Args:
        filepath: Path to the file
        explicitly_requested: Whether this file was explicitly requested by the user
    
    Returns:
        True if the file should be included, False otherwise
    """
    # If the file was explicitly requested by the user, always include it
    if explicitly_requested:
        return True
    
    # Get the filename and extension
    filename = os.path.basename(filepath)
    _, ext = os.path.splitext(filepath)
    ext = ext.lower()
    
    # Exclude hidden files (starting with .)
    if filename.startswith('.'):
        return False
    
    # Special filenames to always include (regardless of extension)
    special_filenames = [
        'CMakeLists.txt', 'Makefile', 'makefile', 
        'Dockerfile', 'requirements.txt', 'package.json',
        'build.gradle', 'pom.xml', 'build.xml',
        'SConstruct', 'SConscript'
    ]
    
    if filename in special_filenames:
        return True
    
    # List of extensions to include (code files)
    included_extensions = [
        # C/C++
        '.c', '.cpp', '.cxx', '.cc', '.h', '.hpp', '.hxx', '.hh', '.ipp', '.C',
        # Python
        '.py', '.pyx', '.pyw', '.pyi',
        # Java/JVM languages
        '.java', '.kt', '.scala', '.groovy',
        # Web development
        '.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.vue', '.svelte',
        # Shell scripts
        '.sh', '.bash', '.zsh', '.fish',
        # Other common languages
        '.go', '.rs', '.swift', '.php', '.cs', '.rb',
        # Scientific/Data Science
        '.jl', '.r', '.R',
        # Build systems
        '.cmake', '.mk', '.mak',
        # Miscellaneous
        '.pl', '.pm', '.lua', '.f', '.f90', '.f95'
    ]
    
    return ext in included_extensions

def collect_files_recursively(directory, included_files=None, skipped_files=0):
    """
    Recursively collect files from directory and subdirectories.
    
    Args:
        directory: Path to the directory
        included_files: List to store tuples of (filepath, content)
        skipped_files: Counter for skipped files
    
    Returns:
        Tuple of (included_files, skipped_files, file_count)
    """
    if included_files is None:
        included_files = []
    
    file_count = 0
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_count += 1
            
            if is_text_file(file_path) and should_include_file(file_path):
                content = read_file_content(file_path)
                if not content.startswith("❌"):
                    included_files.append((file_path, content))
            else:
                skipped_files += 1
    
    return included_files, skipped_files, file_count

async def handle_add_command(chat_history, *paths):
    """Add file content to chat history."""
    global added_files
    contents = []
    new_context = ""
    skipped_files = 0
    total_file_count = 0

    # First, count files and collect explicitly requested files
    for path in paths:
        if os.path.isfile(path):  # File handling - explicitly requested
            content = read_file_content(path)
            if not content.startswith("❌"):
                contents.append((path, content))
                if path not in added_files:
                    added_files.append(path)
        elif os.path.isdir(path):  # Count files in directories first
            print_colored(f"📁 Scanning folder: {path}", Fore.CYAN)
            _, _, dir_file_count = collect_files_recursively(path)
            total_file_count += dir_file_count
        else:
            print_colored(f"❌ '{path}' is neither a valid file nor folder.", Fore.RED)

    # If too many files, ask for confirmation
    if total_file_count > 20:
        session = PromptSession()
        print_colored(f"⚠️ Found {total_file_count} files in the specified directories.", Fore.YELLOW)
        user_input = await session.prompt_async(HTML(f"<ansired>⚠️ Found {total_file_count} files in the specified directories. Adding all files might be slow. Do you want to proceed? (y/n):</ansired> "))
        
        while user_input.lower() not in ['y', 'n']:
            print_colored("❌ Invalid input. Please enter 'y' to proceed or 'n' to cancel.", Fore.RED)
            user_input = await session.prompt_async(HTML(f"<ansired>⚠️ Found {total_file_count} files in the specified directories. Adding all files might be slow. Do you want to proceed? (y/n):</ansired> "))
        
        if user_input.lower() != 'y':
            print_colored("❌ Operation cancelled by user. No files were added.", Fore.RED)
            return chat_history

    # Now process directories after confirmation
    for path in paths:
        if os.path.isdir(path):
            print_colored(f"📁 Processing folder recursively: {path}", Fore.CYAN)
            dir_contents, dir_skipped, _ = collect_files_recursively(path)
            skipped_files += dir_skipped
            
            for filepath, content in dir_contents:
                contents.append((filepath, content))
                if filepath not in added_files:
                    added_files.append(filepath)

    if contents:
        for fp, content in contents:
            new_context += f"""The following file has been added: {fp}:
\n{content}\n\n"""

        chat_history.append({"role": "user", "content": new_context})
        print_colored(f"✅ Successfully added {len(contents)} files to knowledge!", Fore.GREEN)
        if skipped_files > 0:
            print_colored(f"ℹ️ Skipped {skipped_files} hidden files or non-code files.", Fore.YELLOW)
    else:
        print_colored("❌ No valid files were added to knowledge.", Fore.YELLOW)

    return chat_history

async def handle_edit_command(default_chat_history, editor_chat_history, filepaths, default_model, editor_model):
    """Handle edit command to modify existing files."""
    all_contents = [read_file_content(fp) for fp in filepaths]
    valid_files, valid_contents = [], []

    for filepath, content in zip(filepaths, all_contents):
        if content.startswith("❌"):
            print_colored(content, Fore.RED)
        else:
            valid_files.append(filepath)
            valid_contents.append(content)

    if not valid_files:
        print_colored("❌ No valid files to edit.", Fore.YELLOW)
        return default_chat_history, editor_chat_history

    session = PromptSession()
    user_request = await session.prompt_async(HTML(f"<ansired>What would you like to change in {', '.join(valid_files)}?</ansired> "))

    instructions_prompt = "For these files:\n"
    instructions_prompt += "\n".join([f"File: {fp}\n```\n{content}\n```\n" for fp, content in zip(valid_files, valid_contents)])
    instructions_prompt += f"User wants: {user_request}\nProvide LINE-BY-LINE edit instructions for ALL files. Number each instruction and specify which file it applies to.\n"

    default_chat_history.append({"role": "user", "content": instructions_prompt})
    default_instructions = get_streaming_response(default_chat_history, default_model)
    default_chat_history.append({"role": "assistant", "content": default_instructions})

    print_colored("\n" + "=" * 50, Fore.MAGENTA)

    for idx, (filepath, content) in enumerate(zip(valid_files, valid_contents), 1):
        try:
            print_colored(f"📝 EDITING {filepath} ({idx}/{len(valid_files)}):", Fore.BLUE)
            result = ""

            edit_message = f"""
            Original code:

            {content}

            Instructions: {default_instructions}

            Follow only instructions applicable to {filepath}. Output ONLY the new code. No explanations. DO NOT ADD ANYTHING ELSE. no type of file at the beginning of the file like ```python etq. no ``` at the end of the file.

            Add an empty line symbol to the end.
            """

            editor_chat_history.append({"role": "user", "content": edit_message})
            current_content = read_file_content(filepath)
            if current_content.startswith("❌"):
                return default_chat_history, editor_chat_history

            lines = current_content.splitlines(keepends=True)
            buffer = ""
            edited_lines = lines.copy()  # Create a copy to store edited lines
            line_index = 0

            for chunk in client.chat.completions.create(
                model=editor_model,
                messages=editor_chat_history,
                stream=True,
            ):
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print_colored(content, end="")
                    buffer += content

                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        if line_index < len(edited_lines):
                            edited_lines[line_index] = line
                            print_colored(f"✏️ Updated Line {line_index+1}: {line[:50]}...", Fore.CYAN)
                            line_index += 1
                        else:
                            edited_lines.append(line)
                            print_colored(f"➕ NEW Line {line_index+1}: {line[:50]}...", Fore.YELLOW)
                            line_index += 1

            result = '\n'.join(edited_lines) + '\n'
            undo_history[filepath] = current_content   # Store undo
            editor_chat_history.append({"role": "assistant", "content": result})

            if is_diff_on:
                print("\n🔍 DIFF:")
                display_diff(current_content, result)  # Show final diff if it's on

            # Write the changes to the file only after the entire editing process
            if write_file_content(filepath, result):
                print_colored(f"✅ {filepath} successfully edited and saved!", Fore.GREEN)
            else:
                print_colored(f"❌ Failed to save changes to {filepath}", Fore.RED)

            print_colored("=" * 50, Fore.MAGENTA)
        except Exception as e:
            print_colored(f"❌ Error editing {filepath}: {e}", Fore.RED)

    return default_chat_history, editor_chat_history

async def handle_new_command(default_chat_history, editor_chat_history, filepaths, default_model, editor_model):
    """Create new files and optionally edit them."""
    if not filepaths:
        print_colored("❌ No file paths provided.", Fore.RED)
        return default_chat_history, editor_chat_history

    print_colored(f"🆕 Creating new files: {', '.join(filepaths)}", Fore.BLUE)
    created_files = []
    for filepath in filepaths:
        file_ext = os.path.splitext(filepath)[1][1:]
        template = FILE_TEMPLATES.get(file_ext, "")
        try:
            with open(filepath, 'x') as f:
                f.write(template)
            print_colored(f"✅ Created {filepath} with template", Fore.GREEN)
            created_files.append(filepath)
        except FileExistsError:
            print_colored(f"⚠️ {filepath} already exists. It will be edited, not overwritten.", Fore.YELLOW)
            created_files.append(filepath)
        except IOError as e:
            print_colored(f"❌ Could not create {filepath}: {e}", Fore.RED)

    if created_files:
        session = PromptSession()
        user_input = (await session.prompt_async(HTML(f"<ansired>Do you want to edit the newly created files? (y/n):</ansired> "))).lower()
        if user_input == 'y':
            default_chat_history, editor_chat_history = await handle_edit_command(
                default_chat_history, editor_chat_history, created_files, default_model, editor_model
            )

    return default_chat_history, editor_chat_history

async def handle_search_command(default_chat_history):
    """Perform a search and add results to chat history."""
    session = PromptSession()
    search_query = await session.prompt_async(HTML(f"<ansired>What would you like to search?</ansired> "))
    if not search_query.strip():
        print_colored("❌ Empty search query. Please provide a search term.", Fore.RED)
        return default_chat_history

    print_colored(f"\n🔍 Searching for: {search_query}", Fore.BLUE)

    try:
        results = await AsyncDDGS(proxy=None).atext(search_query, max_results=100)
        search_name = search_query[:10].strip()  # Truncate to first 10 characters
        stored_searches[search_name] = results
        print_colored(f"✅ Search results for '{search_name}' stored in memory.", Fore.GREEN)

        # Add search results to chat history
        search_content = f"Search results for '{search_query}':\n"
        for idx, result in enumerate(results[:8], 1):  # Limit to first 5 results for brevity
            search_content += f"{idx}. {result['title']}: {result['body'][:100]}...\n"
        default_chat_history.append({"role": "user", "content": search_content})

    except Exception as e:
        print_colored(f"❌ Error performing search: {e}", Fore.RED)

    return default_chat_history

async def handle_clear_command():
    """Clear added files and searches from memory."""
    global added_files, stored_searches
    cleared_something = False

    if added_files:
        added_files.clear()
        cleared_something = True
        print_colored("✅ Cleared memory of added files.", Fore.GREEN)

    if stored_searches:
        stored_searches.clear()
        cleared_something = True
        print_colored("✅ Cleared stored searches.", Fore.GREEN)

    if not cleared_something:
        print_colored("ℹ️ No files or searches in memory to clear.", Fore.YELLOW)

async def handle_reset_command(system_prompt, editor_prompt):
    """Reset all chat history and memory."""
    global added_files, stored_searches
    added_files.clear()
    stored_searches.clear()

    # Re-initialize:
    default_chat_history = [{"role": "system", "content": system_prompt}]
    editor_chat_history = [{"role": "system", "content": editor_prompt}]

    print_colored(
        "✅ All chat history, memory of added files, and stored searches have been reset.",
        Fore.GREEN,
    )

    return default_chat_history, editor_chat_history

def toggle_diff():
    """Toggle diff display on/off."""
    global is_diff_on
    is_diff_on = not is_diff_on
    status = "on" if is_diff_on else "off"
    print_colored(
        f"Diff is now {status} 🚀" if is_diff_on else f"Diff is now {status} 🚫",
        Fore.YELLOW,
    )

def handle_history_command(chat_history):
    """Display chat history."""
    print_colored("\n📜 Chat History:", Fore.BLUE)
    for idx, message in enumerate(chat_history[1:], 1):  # Skip system message
        role = message['role'].capitalize()
        content = message['content'][:100] + "..." if len(message['content']) > 100 else message['content']
        print_colored(f"{idx}. {role}: {content}", Fore.CYAN)

async def handle_save_command(chat_history):
    """Save chat history to a file."""
    session = PromptSession()
    filename = await session.prompt_async(HTML(f"<ansired>Enter filename to save chat history:</ansired> "))
    try:
        with open(filename, 'w') as f:
            json.dump(chat_history, f)
        print_colored(f"✅ Chat history saved to {filename}", Fore.GREEN)
    except IOError as e:
        print_colored(f"❌ Error saving chat history: {e}", Fore.RED)

async def handle_load_command():
    """Load chat history from a file."""
    session = PromptSession()
    filename = await session.prompt_async(HTML(f"<ansired>Enter filename to load chat history:</ansired> "))
    try:
        with open(filename, 'r') as f:
            loaded_history = json.load(f)
        print_colored(f"✅ Chat history loaded from {filename}", Fore.GREEN)
        return loaded_history
    except IOError as e:
        print_colored(f"❌ Error loading chat history: {e}", Fore.RED)
        return None

async def handle_undo_command(filepath):
    """Undo the last edit for a specific file."""
    if not filepath:
        print_colored("❌ No filepath provided for undo operation.", Fore.RED)
        return
    if filepath in undo_history:
        content = undo_history[filepath]
        if write_file_content(filepath, content):
            print_colored(f"✅ Undid last edit for {filepath}", Fore.GREEN)
            del undo_history[filepath]  # Remove the used undo history
        else:
            print_colored(f"❌ Failed to undo edit for {filepath}", Fore.RED)
    else:
        print_colored(f"❌ No undo history for {filepath}", Fore.RED)

def show_current_model(model_name):
    """Display the current model name."""
    print_colored(f"Current model: {model_name}", Fore.CYAN)

async def change_model(current_model):
    """Change the current AI model."""
    session = PromptSession()
    new_model = await session.prompt_async(HTML(f"<ansired>Enter the new model name: </ansired> "))
    print_colored(f"Model changed from {current_model} to: {new_model}", Fore.GREEN)
    return new_model

async def show_file_content(filepath):
    """Display the content of a file."""
    content = read_file_content(filepath)
    if content.startswith("❌"):
        print_colored(content, Fore.RED)
    else:
        print_colored(f"Content of {filepath}:", Fore.CYAN)
        print(content)

def print_files_and_searches_in_memory():
    """Print the files and searches currently in memory."""
    if added_files:
        file_list = ', '.join(added_files)
        print_colored(
            f"📂 Files currently in memory: {file_list}", Fore.CYAN, Style.BRIGHT
        )
    if stored_searches:
        search_list = ', '.join(stored_searches.keys())
        print_colored(
            f"🔍 Searches currently in memory: {search_list}", Fore.CYAN, Style.BRIGHT
        )

async def handle_ls_command(directory='.'):
    """List files and directories in the specified path."""
    try:
        # Check if the path exists
        if not os.path.exists(directory):
            print_colored(f"❌ Directory not found: {directory}", Fore.RED)
            return

        # If it's a file, just show file info
        if os.path.isfile(directory):
            file_size = os.path.getsize(directory)
            print_colored(f"📄 {os.path.basename(directory)} - {file_size} bytes", Fore.CYAN)
            return

        # List directory contents
        items = os.listdir(directory)
        
        # Separate directories and files
        dirs = []
        files = []
        
        for item in items:
            full_path = os.path.join(directory, item)
            if os.path.isdir(full_path):
                dirs.append((item, "📁"))
            else:
                files.append((item, "📄"))
        
        # Print directories first, then files
        print_colored(f"\n📂 Directory: {os.path.abspath(directory)}", Fore.BLUE, Style.BRIGHT)
        print_colored("=" * 50, Fore.BLUE)
        
        if not dirs and not files:
            print_colored("Directory is empty", Fore.YELLOW)
            return
            
        # Print directories
        if dirs:
            print_colored("\nDirectories:", Fore.MAGENTA)
            for name, icon in dirs:
                print_colored(f"{icon} {name}/", Fore.CYAN)
                
        # Print files
        if files:
            print_colored("\nFiles:", Fore.MAGENTA)
            for name, icon in files:
                file_size = os.path.getsize(os.path.join(directory, name))
                print_colored(f"{icon} {name} - {file_size} bytes", Fore.GREEN)
    
    except PermissionError:
        print_colored(f"❌ Permission denied to access {directory}", Fore.RED)
    except Exception as e:
        print_colored(f"❌ Error listing directory: {e}", Fore.RED)


