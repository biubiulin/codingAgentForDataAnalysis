# Coding Agent for Data Analysis

A coding agent that chats (CLI or Gradio UI), calls a Tuzi-compatible OpenAI Responses API, and executes code securely in an e2b sandbox.

## Features

- **Agent loop with tool calls**: `lib/coding_agent.py` drives an LLM loop, calling tools via `tools_schemas` and `tools`.
- **Secure code execution**: `lib/tools.py` runs Python/Bash in an E2B `Sandbox`, returning text and images.
- **Built-in tools**:
  - `execute_code`, `execute_bash`
  - `list_directory`, `read_file`, `write_file`, `replace_in_file`, `search_file_content`, `glob`
- **Gradio UI**: `lib/ui.py` wraps the agent into an interactive interface.
- **Message compression**: Long conversations are compressed automatically.

## Contents
- **`demos.py`**: Demo functions `coding_agent_demo_cli()` and `coding_agent_demo_ui()`.
- **`main.py`**: Unified entrypoint to run CLI or UI.
- **`app.py`**: Exposes a Gradio `demo` app instance for `gradio app.py` or `python app.py`.
- **`lib/`**: Core libraries
  - `coding_agent.py`: Agent loop using OpenAI Responses API tool calls
  - `ui.py`: Gradio UI
  - `tools.py`, `tools_schemas.py`: Tools and schemas
  - `utils.py`: e2b sandbox helpers
  - `logger.py`, `prompts.py`, `sbx_tools.py`: Logging, prompts, sandbox-side utils
- **`.env.example`**: Template for required environment variables
- **`requirements.txt`**: Python dependencies

## Prerequisites
- Python 3.10–3.12
- e2b account and `E2B_API_KEY`
- Tuzi-compatible OpenAI endpoint and key: `TUZI_BASE_URL`, `TUZI_API_KEY`

## Setup (Windows PowerShell)
```powershell
# 1) Create and activate venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2) Install dependencies
pip install -r requirements.txt

# 3) Configure environment
copy .env.example .env
# Edit .env and set: E2B_API_KEY, TUZI_API_KEY, TUZI_BASE_URL
```

## Environment variables

Create a `.env` in the project root (loaded via `python-dotenv`):

- Required
  - `TUZI_API_KEY` — OpenAI-compatible API key
  - `TUZI_BASE_URL` — OpenAI-compatible base URL
- Recommended (UI/server behavior)
  - `GRADIO_SHARE` — "true" or "false" (default false)
  - `GRADIO_HEIGHT` — UI height, e.g. 800
- Sandbox
  - `E2B_API_KEY` — E2B Code Interpreter API key (if required by your setup)

## Run
- **CLI chat** (terminal):
```powershell
python main.py --mode cli
```

- **Gradio UI** (web):
```powershell
# Option A: via main.py
python main.py --mode ui

# Option B: direct app file
python app.py  # respects GRADIO_SHARE/GRADIO_HEIGHT env vars

# Option C: with gradio CLI (optional)
python -m gradio app.py
```
Application uses keys from `.env` loaded in `demos.py`/`app.py`.


## Notes
- The agent streams via OpenAI Responses API and may call tools like `execute_code` to run code inside an e2b sandbox (`lib/tools.py`).
- `sbx.cache` stores a sandbox name for reconnects; delete it to force a fresh sandbox.
- Security: do NOT commit your real `.env`. Rotate any leaked keys immediately.

## Troubleshooting
- If Gradio UI doesn't open, check console for errors and ensure `TUZI_*` and `E2B_API_KEY` are set.
- If e2b install fails inside sandbox, verify network access and your e2b plan limits.
- Windows PowerShell execution policy can block venv activation; you can run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.
