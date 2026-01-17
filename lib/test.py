import os
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI

# Load env early
load_dotenv(find_dotenv())

_TUZI_API_KEY = os.getenv("TUZI_API_KEY")
# _TUZI_BASE_URL = os.getenv("TUZI_BASE_URL")
def clean_messages_for_llm(messages: list[dict]) -> list[dict]:
    return [{k: v for k, v in msg.items() if not k.startswith("_")} for msg in messages]

client = OpenAI(api_key=_TUZI_API_KEY, base_url="https://api.tu-zi.com/v1")

messages = [{'role': 'user', 'content': 'hihi,1+1=?'}]

response = client.responses.create(
    # model="gpt-4.1-mini", # not work
    # model="gpt-4o",
    model="gpt-4o-mini",

    # instructions="You are a coding assistant that talks like a pirate.",
    # instructions="You are a senior python programmer",
    # input="How do I check if a Python object is an instance of a class?",
    # input="hihi,1+1=?",
    input=[
        {"role": "developer", "content": "You are a senior python programmer"},
        *clean_messages_for_llm(messages),
    ],
)

print(response.output_text)
