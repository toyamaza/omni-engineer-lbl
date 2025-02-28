import os
import sys
import select
from colorama import Fore, Style
import difflib
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import TerminalFormatter
from rich.console import Console
from rich.table import Table
from urllib.parse import urlparse

def clear_console():
    """Clear the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_colored(text, color=Fore.WHITE, style=Style.NORMAL, end='\n'):
    """Print text with specified color and style."""
    print(f"{style}{color}{text}{Style.RESET_ALL}", end=end)

def read_file_content(filepath):
    """Read content from a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return f"❌ Error: File not found: {filepath}"
    except IOError as e:
        return f"❌ Error reading {filepath}: {e}"

def write_file_content(filepath, content):
    """Write content to a file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except IOError as e:
        print_colored(f"❌ Error writing to {filepath}: {e}", Fore.RED)
        return False

def is_text_file(file_path, sample_size=8192, text_characters=set(bytes(range(32,127)) + b'\n\r\t\b')):
    """Determine whether a file is text or binary."""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(sample_size)

        if not chunk:  # Empty files are considered text
            return True

        if b'\x00' in chunk:  # Null bytes usually indicate binary
            return False

        # If >30% of chars are non-text, probably binary
        text_chars = sum(byte in text_characters for byte in chunk)
        return text_chars / len(chunk) > 0.7

    except IOError:
        return False

def is_url(string):
    """Check if a string is a valid URL."""
    try:
        result = urlparse(string)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def display_diff(original, edited):
    """Display the difference between two strings."""
    diff = difflib.unified_diff(
        original.splitlines(), edited.splitlines(), lineterm='', n=0
    )
    for line in diff:
        if line.startswith('+'):
            print_colored(line, Fore.GREEN)
        elif line.startswith('-'):
            print_colored(line, Fore.RED)
        else:
            print_colored(line, Fore.BLUE)

def syntax_highlight(code, language):
    """Highlight syntax in code."""
    lexer = get_lexer_by_name(language)
    return highlight(code, lexer, TerminalFormatter())

def print_welcome_message():
    """Print welcome message with command help."""
    print_colored(
        "🔮 Welcome to the Assistant Developer Console! 🔮", Fore.MAGENTA, Style.BRIGHT
    )

    console = Console()
    table = Table()

    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Description")

    table.add_row("/add", "Add files to AI's knowledge base")
    table.add_row("/edit", "Edit existing files")
    table.add_row("/new", "Create new files")
    table.add_row("/search", "Perform a DuckDuckGo search")
    table.add_row("/clear", "Clear added files and searches from AI's memory")
    table.add_row("/reset", "Reset entire chat and file memory")
    table.add_row("/stop", "Stop the output of the Assistant chat.") 
    table.add_row("/diff", "Toggle display of diffs")
    table.add_row("/history", "View chat history")
    table.add_row("/save", "Save chat history to a file")
    table.add_row("/load", "Load chat history from a file")
    table.add_row("/undo", "Undo last edit for a specific file")
    table.add_row("/help", "Show this help message")
    table.add_row("/model", "Show current AI model")
    table.add_row("/change_model", "Change the AI model")
    table.add_row("/show", "Show content of a file")
    table.add_row("exit", "Exit the application")

    console.print(table)

    print_colored(
        "For any other input, the AI will respond to your query or command.",
        Fore.YELLOW,
    )
    print_colored(
        "Use '<command> help' for more information on a specific command.",
        Fore.YELLOW,
    )
    
    print_colored(
        "Type '/stop' and press Enter at any time to interrupt the AI's response.",
        Fore.RED,
    )

def check_for_interrupt():
    """Check if user has entered input to interrupt."""
    rlist, _, _ = select.select([sys.stdin], [], [], 0)
    if rlist:
        user_input = sys.stdin.readline().strip()
        if user_input.lower() == '/stop':
            return True
    return False
