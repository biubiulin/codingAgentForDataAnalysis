import json
from openai import OpenAI
from typing import Generator, Literal, Optional, Callable
from e2b_code_interpreter import Sandbox
import re
from .logger import logger, log_tool_call
from .prompts import *
from IPython.display import Image, display
import base64
from .tools import execute_tool
import os

TOKEN_LIMIT = 60_000
COMPRESS_THRESHOLD = 0.7
STATE_SNAPSHOT_PATTERN = re.compile(
    r"<state_snapshot>(.*?)</state_snapshot>", re.DOTALL
)


def clean_messages_for_llm(messages: list[dict]) -> list[dict]:
    return [{k: v for k, v in msg.items() if not k.startswith("_")} for msg in messages]


def compress_messages(client: OpenAI, messages: list[dict]) -> list[dict]:
    logger.info(f"[agent] 📦 starting compression for {len(messages)} messages...")
    response = client.responses.create(
        model="gpt-5-nano",

      input=[
            {"role": "developer", "content": SYSTEM_PROMPT_COMPRESS_MESSAGES},
            *messages,
            {
                "role": "user",
                "content": "First, reason in your scratchpad. Then, generate the <state_snapshot>.",
            },
        ],
    )

    text = response.output_text
    # we extract the <state_snapshot>
    context = "\n".join(STATE_SNAPSHOT_PATTERN.findall(text))
    new_messages = [
        {
            "role": "user",
            "content": f"This is snapshot of the conversation so far:\n{context}",
        },
        {
            "role": "assistant",
            "content": "Got it. Thanks for the additional context!",
        },
    ]
    logger.info(
        f"[agent] 📦 compression complete: snapshot_chars={len(context)}, replaced={len(messages)} -> {len(new_messages)} messages"
    )

    return new_messages


def format_messages(messages: list[dict]) -> str:
    content = ""
    for message in messages:
        if "role" in message:
            if message["role"] == "user":
                content += f"[user]: {message['content']}\n"
            elif message["role"] == "assistant":
                content += f"[assistant]: {message['content']}\n"
        elif "type" in message:
            if message["type"] == "function_call":
                content += f"[assistant] Calls {message['name']}\n"
            elif message["type"] == "function_call_output":
                content += f"[function_result]: {message['output']}\n"
    return content


def get_compress_message_index(messages: list[dict]) -> int:
    # couting the number of chars
    chars = [len(json.dumps(message)) for message in messages]
    total_chars = sum(chars)
    # we keep a portion of them
    target_chars = total_chars * COMPRESS_THRESHOLD
    curr_chars = 0
    for index, char in enumerate(chars):
        curr_chars += char
        if (curr_chars) >= target_chars:
            return index
    return len(messages)


def get_first_user_message_index(messages: list[dict]) -> int:
    first_user_message_index = 0
    for index, message in enumerate(messages):
        if "role" in message:
            if message["role"] == "user":
                first_user_message_index = index
                break
    return first_user_message_index


def maybe_compress_messages(
    client: OpenAI, messages: list[dict], usage: int
) -> list[dict]:
    if usage <= TOKEN_LIMIT * COMPRESS_THRESHOLD:
        logger.debug(
            f"[agent] 🧮 no compression needed: usage={usage} threshold={int(TOKEN_LIMIT * COMPRESS_THRESHOLD)}"
        )
        return messages
    compress_index = get_compress_message_index(messages)
    if compress_index >= len(messages):
        return messages
    compress_index += get_first_user_message_index(messages[compress_index:])
    if compress_index <= 0:
        return messages
    # edge case, if we cut and the last message is `function_call`
    # we need to add the output as well
    last_message = messages[compress_index - 1]
    if "type" in last_message:
        if last_message["type"] == "function_call":
            # add its output as well
            compress_index += 1

    to_compress_messages = messages[:compress_index]
    to_keep_messages = messages[compress_index:]

    if len(to_compress_messages) > 0:
        logger.info(
            f"[agent] 📦 compressing messages range=[0...{compress_index}] keep={len(to_keep_messages)}"
        )
        compressed = compress_messages(client, to_compress_messages)
        logger.info(
            f"[agent] 📦 compression applied: before={len(messages)} after={len(compressed) + len(to_keep_messages)}"
        )
        return [*compressed, *to_keep_messages]

    return messages


def coding_agent(
    client: OpenAI,
    sbx: Sandbox,
    query: str,
    tools: dict[str, Callable],
    tools_schemas: list[dict],
    max_steps: int = 5,
    system: Optional[str] = "You are a senior python programmer",
    messages: Optional[list[dict]] = None,
    usage: Optional[int] = 0,
    model: Literal["gpt-4o-mini, gpt-5-mini"] = "gpt-4o-mini",
    **model_kwargs,
# Generator[YieldType, SendType, ReturnType]表示生成器的三部分类型：
# YieldType：每次 yield 的值的类型。你的代码里多次执行 yield part_dict, messages, usage（还有第一次 yield user_message, messages, usage），所以实际应该是 tuple[dict, list[dict], int]（第一项是单个消息 dict，第二项是消息列表 messages，第三项是整数 usage）。
# SendType：通过 generator.send(value) 发送进来的值类型。代码没有使用 .send()，所以是 None。
# ReturnType：生成器结束时 return 返回值的类型。except StopIteration as e: messages, final_usage = e.value 显示返回的是 tuple[list[dict], int]，也就是消息列表和最终 token 用量。
) -> Generator[tuple[dict, list[dict], int], None, tuple[list[dict], int]]:
    if messages is None:
        messages = []
    # up to here
    start_index = len(messages)
    user_message = {"role": "user", "content": query}
    messages.append(user_message)
    yield user_message, messages, usage

    steps = 0
    # continue till max_steps
    while steps < max_steps:
        messages = maybe_compress_messages(
            client, clean_messages_for_llm(messages), usage
        )
        response = client.responses.create(
            model=model,
            input=[
                {"role": "developer", "content": system},
                *clean_messages_for_llm(messages),
            ],
            tools=tools_schemas,
            **model_kwargs,
        )
        usage = response.usage.total_tokens
        try:
            parts_count = len(response.output)
        except Exception:
            parts_count = 0
        logger.info(
            f"[agent] 🤖 LLM responded: model={model} tokens_total={usage} parts={parts_count} step={steps}"
        )

        has_function_call = False
        for part in response.output:
            messages.append(part.to_dict())
            yield part.to_dict(), messages, usage
            if part.type == "function_call":
                has_function_call = True
                name = part.name
                logger.info(
                    f"[agent] 🧰 tool call: {name} args_len={len(part.arguments) if hasattr(part, 'arguments') and part.arguments else 0}"
                )
                result, metadata = execute_tool(name, part.arguments, tools, sbx=sbx)
                result_msg = {
                    "type": "function_call_output",
                    "call_id": part.call_id,
                    "output": json.dumps(result),
                    "_metadata": metadata,
                }
                messages.append(result_msg)
                yield result_msg, messages, usage

        steps += 1
        if not has_function_call:
            logger.info("[agent] ✅ no further tool calls; final assistant message produced")
            break

    return messages, usage


def log(generator_func, *args, **kwargs):
    """Wraps the coding_agent and handles logging like the original"""
    gen = generator_func(*args, **kwargs)
    step = 0
    pending_tool_calls = {}  # call_id -> (name, arguments)

    try:
        while True:
            part_dict, messages, usage = next(gen)
            part_type = part_dict.get("type")

            if part_type == "reasoning":
                if step == 0:
                    logger.info(f"✨: [agent-#{step}] Thinking...")
                    step += 1
                logger.info(" ...")
            elif part_type == "message":
                content = part_dict.get("content")
                if content and content[0].get("text"):
                    logger.info(f"✨: {content[0]['text']}")
            elif part_type == "function_call":
                call_id = part_dict.get("call_id")
                name = part_dict.get("name")
                arguments = part_dict.get("arguments")
                pending_tool_calls[call_id] = (name, arguments)
            elif part_type == "function_call_output":
                call_id = part_dict.get("call_id")
                if call_id in pending_tool_calls:
                    name, arguments = pending_tool_calls.pop(call_id)
                    result = json.loads(part_dict.get("output", "{}"))
                    log_tool_call(name, arguments, result)
                metadata = part_dict.get("_metadata")
                if metadata:
                    images = metadata.get("images")
                    if images:
                        for image in images:
                            display(Image(data=base64.b64decode(image)))

    except StopIteration as e:
        messages, final_usage = e.value
        logger.info(f"[agent] 🔢 tokens: {final_usage} total")
        return messages, final_usage





