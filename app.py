import os
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI

from lib.utils import create_sandbox
from lib.tools import execute_code
from lib.tools_schemas import execute_code_schema
from lib.ui import ui
from lib.coding_agent_bak import coding_agent as _coding_agent

# Load env early
load_dotenv(find_dotenv())

_TUZI_API_KEY = os.getenv("TUZI_API_KEY")
_TUZI_BASE_URL = os.getenv("TUZI_BASE_URL")

# Build the Gradio demo without launching automatically
_client = OpenAI(api_key=_TUZI_API_KEY, base_url=_TUZI_BASE_URL)
_sbx = create_sandbox()

demo = ui(
    _coding_agent,
    messages=[],
    client=_client,
    tools_schemas=[execute_code_schema],
    system="You are senior Python software engineer",
    tools={"execute_code": execute_code},
    sbx=_sbx,
)

if __name__ == "__main__":
    # Allow overriding via env vars
    share = os.getenv("GRADIO_SHARE", "false").lower() == "true"
    height = int(os.getenv("GRADIO_HEIGHT", "800"))
    demo.launch(height=height, share=share)
