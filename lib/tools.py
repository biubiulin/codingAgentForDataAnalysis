import json
import time
from typing import Callable, Optional
from e2b_code_interpreter import Execution, Sandbox
from .logger import logger, log_tool_call


def execute_code(sbx: Sandbox, code: str, language: str = "python") -> Execution:
    start = time.perf_counter()
    preview = code.strip().splitlines()[:3]
    preview_text = " \\n".join(preview)
    logger.info(f"[sandbox] 🏁 run_code start: lang={language} lines={len(code.splitlines())}\n{preview_text}")
    try:
        execution = sbx.run_code(code, language)
    except Exception as e:
        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.error(f"[sandbox] ❌ run_code failed: lang={language} duration={duration_ms}ms error={e}")
        raise
    duration_ms = int((time.perf_counter() - start) * 1000)
    metadata = {}
    results = execution.results
    for result in results:
        if result.png:
            metadata["images"] = [result.png]
            result.png = None
            result.chart = None
    logger.info(
        f"[sandbox] ✅ run_code done: lang={language} results={len(results)} duration={duration_ms}ms"
    )
    return execution.to_json(), metadata


tools = {
    "execute_code": execute_code,
    "execute_bash": lambda **a: execute_code(**a, language="bash"),
    "list_directory": lambda **a: execute_code(
        a["sbx"],
        f"list_directory(secure_path({repr(a.get('path', '.'))}), {repr(a.get('ignore'))}, {a.get('offset', 0)}, {a.get('limit', 16)})",
    ),
    "read_file": lambda **a: execute_code(
        a["sbx"],
        f"read_file(secure_path({repr(a.get('file_path', ''))}), {a.get('limit')}, {a.get('offset', 0)})",
    ),
    "write_file": lambda **a: execute_code(
        a["sbx"],
        f"write_file({repr(a.get('content', ''))}, secure_path({repr(a.get('file_path', ''))}))",
    ),
    "replace_in_file": lambda **a: execute_code(
        a["sbx"],
        f"replace_in_file(secure_path({repr(a.get('file_path', ''))}), {repr(a.get('old_string', ''))}, {repr(a.get('new_string', ''))}, {a.get('expected_replacements', 1)})",
    ),
    "search_file_content": lambda **a: execute_code(
        a["sbx"],
        f"search_file_content({repr(a.get('pattern', ''))}, {repr(a.get('include'))}, secure_path({repr(a.get('path', '.'))}), {a.get('use_regex', False)}, {a.get('fuzzy_threshold')}, {a.get('offset', 0)}, {a.get('limit', 16)})",
    ),
    "glob": lambda **a: execute_code(
        a["sbx"],
        f"glob({repr(a.get('pattern', ''))}, secure_path({repr(a.get('path', '.'))}), {repr(a.get('ignore'))}, {a.get('offset', 0)}, {a.get('limit', 16)})",
    ),
}


def execute_tool(name: str, args: str, tools: dict[str, Callable], **kwargs):
    metadata = {}
    started = time.perf_counter()
    try:
        args_obj = json.loads(args)
        if name not in tools:
            result = {"error": f"Tool {name} doesn't exist."}
            logger.error(f"[tool] ❌ not found: {name}")
            return result, metadata
        logger.info(f"[tool] ▶️ executing: {name} , args_keys={list(args_obj.keys())}")
        result, metadata = tools[name](**args_obj, **kwargs)
        duration_ms = int((time.perf_counter() - started) * 1000)
        log_tool_call(name, args, result)
        logger.info(f"[tool] ✅ success: {name} duration={duration_ms}ms")
    except json.JSONDecodeError as e:
        result = {"error": f"{name} failed to parse arguments: {str(e)}"}
        logger.error(f"[tool] ❌ arg parse error in {name}: {e}")
    except KeyError as e:
        result = {"error": f"Missing key in arguments: {str(e)}"}
        logger.error(f"[tool] ❌ missing arg in {name}: {e}")
    except Exception as e:
        result = {"error": str(e)}
        logger.error(f"[tool] ❌ exception in {name}: {e}")
    return result, metadata
