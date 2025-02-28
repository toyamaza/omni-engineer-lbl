"""Search operations for the AI assistant."""

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from colorama import Fore

from duckduckgo_search import AsyncDDGS
from utils import print_colored
from . import stored_searches

async def handle_search_command(default_chat_history):
    """Perform a search and add results to chat history."""
    session = PromptSession()
    search_query = await session.prompt_async(HTML(f"<ansired>What would you like to search?</ansired> "))
    if not search_query.strip():
        print_colored("❌ Empty search query. Please provide a search term.", Fore.RED)
        return default_chat_history

    print_colored(f"\n🔍 Searching for: {search_query}", Fore.CYAN)
    
    try:
        async with AsyncDDGS() as ddgs:
            results = await ddgs.text(search_query, max_results=5)
        
        if not results:
            print_colored("❌ No results found.", Fore.RED)
            return default_chat_history
        
        print_colored("\n📊 Search Results:", Fore.GREEN)
        formatted_results = []
        
        for i, result in enumerate(results, 1):
            title = result.get('title', 'No title')
            body = result.get('body', 'No content')
            url = result.get('href', 'No URL')
            
            print_colored(f"\n{i}. {title}", Fore.YELLOW)
            print_colored(f"   {body}", Fore.WHITE)
            print_colored(f"   URL: {url}", Fore.BLUE)
            
            formatted_results.append(f"{i}. {title}\n{body}\n{url}\n")
        
        # Store the search results
        stored_searches[search_query] = formatted_results
        
        # Add search results to chat history
        search_content = f"Search query: {search_query}\n\n" + "\n".join(formatted_results)
        updated_history = default_chat_history + [{"role": "system", "content": f"Web search results:\n{search_content}"}]
        
        return updated_history
        
    except Exception as e:
        print_colored(f"❌ Error during search: {str(e)}", Fore.RED)
        return default_chat_history