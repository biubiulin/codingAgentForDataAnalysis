from lib.utils import create_sandbox
from dotenv import load_dotenv, find_dotenv
import os
# Load environment variables from .env so E2B_API_KEY / OPENAI_API_KEY are available
load_dotenv(find_dotenv())
_TUZI_API_KEY = os.getenv("TUZI_API_KEY")
_TUZI_BASE_URL = os.getenv("TUZI_BASE_URL")

# with open("pokemon.csv", "r", encoding="utf-8", errors="replace") as f:
#     content1 = f.read()
# sbx.files.write("data.csv", content1)



from lib.coding_agent import coding_agent, log
from lib.tools_schemas import execute_code_schema
from lib.tools import execute_code
from openai import OpenAI

# sbx = create_sandbox()
# with open("unknown.csv", "rb") as f:
#     content2 = f.read()
# client = OpenAI(api_key=_TUZI_API_KEY,
#                 base_url=_TUZI_BASE_URL)
# system = """You are a senior python programmer.
# You must run the code using the `execute_code` tool.
# The user has uploaded a data.csv.
# You help the user understanding the data
# by creating interesting plots.
# """
system = """You are a senior python programmer. 
You must run the code using the `execute_code` tool.
The user has uploaded a data.csv.
You help the user understanding the data 
by creating interesting plot  s.
"""
# tools = { "execute_code" : execute_code }
# messages = []

# query = "What is the data about?"
# query = "Can you aggregate the pokemons by type?"
# while (query := input(">:")) != "/exit":
#     messages, usage = log(coding_agent,
#         messages=messages,
#         query=query,
#         client=client,
#         system=system,
#         tools_schemas=[execute_code_schema],
#         tools=tools,
#         max_steps=10,
#         sbx=sbx,
#     )

from lib.coding_agent import coding_agent as _coding_agent, log
from lib.ui import ui

def coding_agent_demo_ui():
    client = OpenAI(api_key=_TUZI_API_KEY,
                       base_url=_TUZI_BASE_URL)
    # sbx = create_sandbox()
    sbx = create_sandbox()
    with open("unknown.csv", "rb") as f:
        content2 = f.read()
    sbx.files.write("data.csv", content2)
    messages = []
    demo = ui(
        _coding_agent,
        messages=[],
        client=client,
        tools_schemas=[execute_code_schema],
        system=system,
        tools={"execute_code": execute_code},
        sbx=sbx,
    )
    demo.launch(height=800, share=True)
if __name__ == "__main__":
    coding_agent_demo_ui()