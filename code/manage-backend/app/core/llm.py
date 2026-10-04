"""LLM 调用封装 — OpenAI-compatible 接口（当前：DeepSeek）"""
import json
import httpx

from app.core.config import get_settings


async def chat(system_prompt: str, user_content: str) -> str:
    """
    调用 LLM 返回文本内容。
    使用 OpenAI-compatible Chat Completions 接口。
    """
    settings = get_settings()
    if not settings.LLM_API_KEY:
        raise RuntimeError("LLM_API_KEY 未配置")

    payload = {
        "model": settings.LLM_MODEL,
        "max_tokens": settings.LLM_MAX_TOKENS,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{settings.LLM_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def chat_json(system_prompt: str, user_content: str) -> dict:
    """调用 LLM 并将返回内容解析为 JSON dict"""
    text = await chat(system_prompt, user_content)
    # 去除可能的 markdown 代码块包裹
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        text = text.rsplit("```", 1)[0]
    return json.loads(text.strip())
