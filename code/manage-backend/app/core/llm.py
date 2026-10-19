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


async def chat_vision(image_base64: str, image_media_type: str = "image/jpeg") -> str:
    """
    调用支持视觉的 LLM，识别图片中的文字内容并返回题干文本。
    image_base64: base64 编码的图片数据（不含 data:xxx;base64, 前缀）
    """
    settings = get_settings()
    if not settings.LLM_API_KEY:
        raise RuntimeError("LLM_API_KEY 未配置")

    system_prompt = (
        "你是一个专业的题目识别助手。请仔细识别图片中的所有文字内容，"
        "包括题干、数学公式、图表说明等，原样输出为纯文本，不要添加任何解释或额外内容。"
        "如果图片中包含数学公式，请用标准文本形式表达。"
    )

    payload = {
        "model": settings.LLM_MODEL,
        "max_tokens": settings.LLM_MAX_TOKENS,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{image_media_type};base64,{image_base64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": "请识别并输出图片中的全部文字内容。"
                    }
                ]
            }
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
        msg = choice["message"]
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
