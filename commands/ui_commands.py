"""UI commands for the AI assistant."""

from colorama import Fore
from utils import print_colored
from . import is_diff_on

def toggle_diff():
    """Toggle diff display mode for file edits."""
    global is_diff_on
    is_diff_on = not is_diff_on
    status = "ON" if is_diff_on else "OFF"
    print_colored(f"🔄 Diff mode is now {status}", Fore.GREEN)
    return is_diff_on

def show_current_model(model_name):
    """Display the currently active AI model."""
    print_colored(f"🤖 Current model: {model_name}", Fore.CYAN)

def change_model(available_models, current_model):
    """Change the AI model being used."""
    print_colored("\n🔄 Available Models:", Fore.CYAN)
    
    for i, model in enumerate(available_models, 1):
        marker = "✓" if model == current_model else " "
        print_colored(f"  [{i}] {marker} {model}", Fore.WHITE)
    
    try:
        choice = input("\nEnter model number or name (or press Enter to cancel): ")
        
        if not choice.strip():
            print_colored("❌ Model change canceled.", Fore.YELLOW)
            return current_model
        
        # Check if input is a number
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(available_models):
                new_model = available_models[index]
            else:
                print_colored(f"❌ Invalid model number. Please enter 1-{len(available_models)}.", Fore.RED)
                return current_model
        else:
            # Input is a name
            if choice in available_models:
                new_model = choice
            else:
                print_colored(f"❌ Model '{choice}' not found in available models.", Fore.RED)
                return current_model
        
        if new_model == current_model:
            print_colored(f"ℹ️ Model {new_model} is already selected.", Fore.BLUE)
        else:
            print_colored(f"✅ Changed model to: {new_model}", Fore.GREEN)
        
        return new_model
        
    except Exception as e:
        print_colored(f"❌ Error changing model: {str(e)}", Fore.RED)
        return current_model
