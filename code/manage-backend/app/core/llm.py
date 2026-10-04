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

    async with httpx.AsyncClient(timeout=120) as client:
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
        choice = data["choices"][0]
        if choice.get("finish_reason") == "length":
            raise RuntimeError("LLM 输出被截断（max_tokens 不足），请增大 LLM_MAX_TOKENS")
        msg = choice["message"]
        # DeepSeek 推理模型有时将答案放在 reasoning_content，content 为空
        content = (msg.get("content") or "").strip()
        if not content:
            content = (msg.get("reasoning_content") or "").strip()
        return content


async def chat_json(system_prompt: str, user_content: str) -> dict:
    """调用 LLM 并将返回内容解析为 JSON dict"""
    import re
    text = await chat(system_prompt, user_content)
    text = text.strip()

    # 去除 markdown 代码块包裹
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        text = text.rsplit("```", 1)[0].strip()

    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 从文本中提取第一个完整 JSON 对象（应对 reasoning_content 包含额外文字的情况）
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        return json.loads(match.group())

    raise ValueError(f"无法从 LLM 返回内容中解析 JSON，内容长度: {len(text)}")
