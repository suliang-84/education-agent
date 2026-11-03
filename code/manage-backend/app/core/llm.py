"""LLM 调用封装 — OpenAI-compatible 接口（当前：DeepSeek）"""
import asyncio
import json
import httpx

from app.core.config import get_settings


RETRY_STATUS = {429, 500, 502, 503, 504}
RETRY_DELAYS = (1.0, 2.5, 5.0)   # 第 1、2、3 次重试前等待的秒数（共最多 4 次请求）


async def _post(url: str, headers: dict, payload: dict, timeout: float = 120) -> httpx.Response:
    """向大模型服务发请求：上游繁忙（429 / 5xx）、网络抖动、超时时自动重试，其它错误（400 / 401 等）不重试直接抛出"""
    last: Exception | None = None
    for i in range(len(RETRY_DELAYS) + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code in RETRY_STATUS and i < len(RETRY_DELAYS):
                last = httpx.HTTPStatusError(f"{resp.status_code}", request=resp.request, response=resp)
            else:
                resp.raise_for_status()
                return resp
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout, httpx.RemoteProtocolError) as e:
            last = e
            if i >= len(RETRY_DELAYS):
                raise
        await asyncio.sleep(RETRY_DELAYS[i])
    raise last  # type: ignore[misc]


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

    resp = await _post(
        f"{settings.LLM_BASE_URL}/chat/completions",
        {"Authorization": f"Bearer {settings.LLM_API_KEY}", "Content-Type": "application/json"},
        payload,
    )
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


async def chat_messages(messages: list[dict], max_tokens: int | None = None, temperature: float | None = None) -> dict:
    """多轮对话：messages 为 OpenAI 格式（system / user / assistant）。
    返回 {"text": 回复文本, "usage": {"prompt_tokens", "completion_tokens", "total_tokens"}, "model": 模型名}"""
    settings = get_settings()
    if not settings.LLM_API_KEY:
        raise RuntimeError("LLM_API_KEY 未配置")

    payload: dict = {
        "model": settings.LLM_MODEL,
        "max_tokens": max_tokens or settings.LLM_MAX_TOKENS,
        "messages": messages,
    }
    if temperature is not None:
        payload["temperature"] = temperature

    resp = await _post(
        f"{settings.LLM_BASE_URL}/chat/completions",
        {"Authorization": f"Bearer {settings.LLM_API_KEY}", "Content-Type": "application/json"},
        payload,
    )
    data = resp.json()
    choice = data["choices"][0]
    msg = choice["message"]
    content = (msg.get("content") or "").strip() or (msg.get("reasoning_content") or "").strip()
    usage = data.get("usage") or {}
    return {
        "text": content,
        "truncated": choice.get("finish_reason") == "length",
        "usage": {
            "prompt_tokens": int(usage.get("prompt_tokens") or 0),
            "completion_tokens": int(usage.get("completion_tokens") or 0),
            "total_tokens": int(usage.get("total_tokens") or 0),
        },
        "model": settings.LLM_MODEL,
    }


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
