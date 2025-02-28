#!/bin/bash

# Define the @ai function
ai() {
    # Get the AI script location - change this to the actual path
    AI_SCRIPT_PATH="$HOME/Work/ai/omni-engineer-lbl/ai_shell.py"
    
    # Activate the Python virtual environment if it exists
    if [ -f "$HOME/Work/ai/venv/bin/activate" ]; then
        source "$HOME/Work/ai/venv/bin/activate"
    fi
    
    # Run the AI script with all arguments passed to this function
    python "$AI_SCRIPT_PATH" "$@"
    
    # Deactivate virtual environment if it was activated
    if [ -n "$VIRTUAL_ENV" ]; then
        deactivate 2>/dev/null || true
    fi
}

# Create an alias @ai to point to the ai function
alias @ai='ai'

# Print a message when sourced
echo "AI assistant loaded! Use '@ai' followed by your command or question."
echo "Examples:"
echo "  @ai /add main.py"
echo "  @ai what does this test.cxx file do?"
