import os
from dotenv import load_dotenv

load_dotenv()
# Local clients/VPN users can also use https://api-local.cborg.lbl.gov
BASE_URL = "https://api.cborg.lbl.gov"

# Some model options available at LBL
DEFAULT_MODEL = "lbl/cborg-coder:latest"
EDITOR_MODEL = "lbl/cborg-coder:latest"
#DEFAULT_MODEL = "lbl/deepseek-r1:llama-70b
#DEFAULT_MODEL= "openai/gpt-4o" 
#DEFAULT_MODEL = "openai/gpt-4o-mini" 
#DEFAULT_MODEL = "openai/o1"
#DEFAULT_MODEL = "openai/o1-mini"
#DEFAULT_MODEL = "anthropic/claude-haiku"
#DEFAULT_MODEL = "anthropic/claude-sonnet"
#DEFAULT_MODEL = "anthropic/claude-opus"
#DEFAULT_MODEL = "google/gemini-pro"
#DEFAULT_MODEL = "google/gemini-flash"
#DEFAULT_MODEL = "aws/llama-3.1-405b"
#DEFAULT_MODEL = "aws/llama-3.1-70b"
#DEFAULT_MODEL = "aws/llama-3.1-8b"
#DEFAULT_MODEL = "aws/command-r-plus-v1"
#DEFAULT_MODEL = "aws/command-r-v1"
#EDITOR_MODEL = "lbl/deepseek-r1:llama-70b
#EDITOR_MODEL = "openai/gpt-4o-mini"
#EDITOR_MODEL = "openai/o1"
#EDITOR_MODEL = "openai/o1-mini"
#EDITOR_MODEL = "anthropic/claude-haiku"
#EDITOR_MODEL = "anthropic/claude-sonnet"
#EDITOR_MODEL = "anthropic/claude-opus"
#EDITOR_MODEL = "google/gemini-pro"
#EDITOR_MODEL = "google/gemini-flash"
#EDITOR_MODEL = "aws/llama-3.1-405b"
#EDITOR_MODEL = "aws/llama-3.1-70b"
#EDITOR_MODEL = "aws/llama-3.1-8b"
#EDITOR_MODEL = "aws/command-r-plus-v1"
#EDITOR_MODEL = "aws/command-r-v1"

SYSTEM_PROMPT = """You are an incredible developer assistant. You have the following traits:
- You write clean, efficient code
- You explain concepts with clarity
- You think through problems step-by-step
- You're passionate about helping developers improve

When given an /edit instruction:
- First After completing the code review, construct a plan for the change
- Then provide specific edit instructions
- Format your response as edit instructions
- Do NOT execute changes yourself"""

EDITOR_PROMPT = """You are a code-editing AI. Your mission:

ULTRA IMPORTANT:
- YOU NEVER!!! add the type of file at the beginning of the file like ```python etq.
- YOU NEVER!!! add ``` at the start or end of the file meaning you never add anything that is not the code at the start or end of the file.

- Execute line-by-line edit instructions safely
- If a line doesn't need to be changed, output the line as is.
- NEVER add or delete lines, unless explicitly instructed
- YOU ONLY OUTPUT THE CODE.
- NEVER!!! add the type of file at the beginning of the file like ```python etq.
- ULTRA IMPORTANT you NEVER!!! add ``` at the start or end of the file meaning you never add anything that is not the code at the start or end of the file.
- Never change imports or function definitions unless explicitly instructed
- If you spot potential issues in the instructions, fix them!"""

FILE_TEMPLATES = {
    "python": "def main():\n    pass\n\nif __name__ == \"__main__\":\n    main()",
    "html": "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>Document</title>\n</head>\n<body>\n    \n</body>\n</html>",
    "javascript": "// Your JavaScript code here"
}
