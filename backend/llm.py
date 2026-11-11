"""呼叫 AI 模型。任何 OpenAI 相容的 API（OpenAI、LiteLLM、Ollama、vLLM…）都可以用。"""
from openai import OpenAI

from .config import env, load_config


def model_name() -> str:
    return env("LLM_MODEL", "gpt-4o-mini")


def is_configured() -> bool:
    return bool(env("LLM_API_KEY"))


def chat(messages: list[dict]) -> str:
    client = OpenAI(
        base_url=env("LLM_BASE_URL") or None,  # 留空 = OpenAI 官方
        api_key=env("LLM_API_KEY"),
        timeout=50,  # 要比 vercel.json 的 maxDuration 短
    )
    kwargs = {"model": model_name(), "messages": messages}
    temperature = load_config().get("temperature")
    if temperature is not None:  # 有些推理模型不接受 temperature，所以預設不送
        kwargs["temperature"] = temperature
    resp = client.chat.completions.create(**kwargs)
    return (resp.choices[0].message.content or "").strip()
