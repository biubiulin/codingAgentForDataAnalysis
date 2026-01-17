from lib import tools_schemas, tools
from lib.coding_agent import coding_agent as _coding_agent, log
from openai import OpenAI
from lib.utils import create_sandbox
from lib.tools import execute_code
from lib.tools_schemas import execute_code_schema
from lib.logger import logger
from lib.ui import ui
import threading
from dotenv import load_dotenv, find_dotenv
import os
# Load environment variables from .env so E2B_API_KEY / OPENAI_API_KEY are available
load_dotenv(find_dotenv())
_TUZI_API_KEY = os.getenv("TUZI_API_KEY")
_TUZI_BASE_URL = os.getenv("TUZI_BASE_URL")

def coding_agent_demo_cli():
    
    client = OpenAI(api_key=_TUZI_API_KEY,
                       base_url=_TUZI_BASE_URL )
    sbx = create_sandbox()
    messages = []
    logger.info("✨: Hello there! Ask me to code something!")
    while (query := input(">:")) != "/exit":
        messages, usage = log(
            _coding_agent,
            query=query,
            messages=messages,
            client=client,
            tools_schemas=[execute_code_schema],
            system="You are senior Python software engineer",
            tools={"execute_code": execute_code},
            sbx=sbx,
        )


def coding_agent_demo_ui():
    client = OpenAI(api_key=_TUZI_API_KEY,
                       base_url=_TUZI_BASE_URL )
    sbx = create_sandbox()
    messages = []
    demo = ui(
        _coding_agent,
        messages=[],
        client=client,
        # tools_schemas=[execute_code_schema],
        tools_schemas=tools_schemas,
        system="You are senior Python software engineer",
        # tools={"execute_code": execute_code},
        tools=tools,

        sbx=sbx,
    )
    demo.launch(height=800, share=True)
if __name__ == "__main__":
    coding_agent_demo_ui()
    # coding_agent_demo_cli()

