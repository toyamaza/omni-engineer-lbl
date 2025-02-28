import os
import sys
import select
from openai import OpenAI
from colorama import Fore
from utils import print_colored

# Initialize OpenAI client
client = OpenAI(
    base_url=os.getenv("BASE_URL", "https://api.cborg.lbl.gov"),
    api_key=os.getenv("CBORG_API_KEY"),
)

def get_streaming_response(messages, model):
    """Get a streaming response from the AI model."""
    try:
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
        )
        full_response = ""
        for chunk in stream:
            # Check for user input without blocking
            rlist, _, _ = select.select([sys.stdin], [], [], 0)
            if rlist:
                user_input = sys.stdin.readline().strip()
                if user_input.lower() == '/stop':
                    print_colored("\n\nResponse interrupted by user.", Fore.YELLOW)
                    return None

            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                print_colored(content, end="")
                full_response += content

        return full_response.strip()
    except Exception as e:
        print_colored(f"Error in streaming response: {e}", Fore.RED)
        return None
