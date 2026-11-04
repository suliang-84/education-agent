"""AI 助教：纯函数部分（内容安全、突破 / 沉默识别、策略选择与有效性、提示词、摘要触发）——不依赖数据库，可单元测试"""
import re
from datetime import datetime, timedelta

MAX_INPUT_CHARS = 500     # 学生消息上限
MAX_REPLY_CHARS = 400     # AI 回复上限
SUMMARY_EVERY = 10        # 每累积这么多条新消息，滚动生成一次摘要
SILENCE_TIMEOUT_MIN = 10  # 默认沉默超时（分钟），实际取系统配置 chat_silence_timeout_min

# ── 内容安全：简单的关键词拦截（敏感内容不进入大模型，也不入库）。这是第一道防线，后续可换成专业审核服务 ──
_BLOCKED = [
    "自杀", "怎么死", "去死", "杀人", "制造炸弹", "制作炸药", "炸弹制作", "毒品", "吸毒", "色情", "裸体", "约炮",
    "赌博", "嫖娼", "枪支购买", "买枪", "恐怖袭击",
]


def is_blocked(text: str) -> bool:
    t = re.sub(r"\s+", "", text or "").lower()
    return any(w in t for w in _BLOCKED)


# ── 理解突破：关键词初筛（再交给大模型确认）──
_AHA_PATTERNS = [
    "我明白了", "我懂了", "我想通了", "我会了", "搞懂了", "弄懂了", "原来如此", "原来是这样", "豁然开朗",
    "哦！我", "哦!我", "我知道了", "明白了", "懂了", "我悟了", "终于会了", "终于懂了",
]


def aha_prefilter(text: str) -> bool:
    t = re.sub(r"\s+", "", text or "")
    return any(p in t for p in _AHA_PATTERNS)


# ── 沉默模式 ──
_SILENCE_PATTERNS = ["我自己想", "让我自己想", "我自己来", "别提示", "不用提示", "别问我", "先别问", "我想自己", "别说了", "我自己做"]
_RESUME_PATTERNS = ["你来说", "给我提示", "帮帮我", "我需要提示", "继续引导", "我不会", "我想不出来"]


def wants_silence(text: str) -> bool:
    t = re.sub(r"\s+", "", text or "")
    return any(p in t for p in _SILENCE_PATTERNS)


def wants_resume(text: str) -> bool:
    t = re.sub(r"\s+", "", text or "")
    return any(p in t for p in _RESUME_PATTERNS)


def silence_active(mode: bool, triggered_at: datetime | None, now: datetime, timeout_min: int = SILENCE_TIMEOUT_MIN) -> bool:
    """沉默模式是否仍有效：开启后超过 timeout_min 分钟自动解除"""
    if not mode or triggered_at is None:
        return False
    return now - triggered_at < timedelta(minutes=timeout_min)


# ── 启发策略选择 ──
def effectiveness_score(positive: int, negative: int, effective: int, ineffective: int) -> float:
    """策略有效性得分 0~100：基准 50，点赞 +6、点踩 -8、触发理解突破 +10、被判无效切换 -4"""
    return float(max(0, min(100, 50 + 6 * positive - 8 * negative + 10 * effective - 4 * ineffective)))


def pick_strategy(
    strategies: list[dict],            # [{id, powers: [..], priority}]（只含启用的）
    scores: dict[str, float],          # 该学生各策略的有效性得分（没记录的按 50）
    recent: list[str],                 # 最近几条 AI 回复用的策略，最新在最后
    weak_power: str | None,            # 学生最弱的一力（策略适用该力时加分）
    progressed: bool = False,          # 最近有理解突破：视为有进展，不切换
    exclude: str | None = None,        # 强制排除的策略（重新生成时避开刚用过的）
) -> tuple[str | None, bool]:
    """返回 (策略 id, 是否发生切换)。同一策略连续用满 2 次且没有进展就切换到有效性最高的其它策略"""
    if not strategies:
        return None, False
    current = recent[-1] if recent else None
    streak = 0
    for sid in reversed(recent):
        if sid == current:
            streak += 1
        else:
            break
    if exclude is None and current and not (streak >= 2 and not progressed):
        if any(s["id"] == current for s in strategies):
            return current, False

    def score(s: dict) -> float:
        return scores.get(s["id"], 50.0) + (8.0 if weak_power and weak_power in s["powers"] else 0.0) + (10 - s["priority"]) * 0.5

    banned = {x for x in (exclude, current if (streak >= 2 and not progressed) else None) if x}
    cands = [s for s in strategies if s["id"] not in banned] or strategies
    best = max(cands, key=score)
    return best["id"], bool(current and best["id"] != current)


# ── 回复处理 ──
def trim_reply(text: str, limit: int = MAX_REPLY_CHARS) -> str:
    """超长时在句号 / 问号 / 感叹号处截断，找不到就硬截断"""
    t = (text or "").strip()
    if len(t) <= limit:
        return t
    cut = t[:limit]
    m = max(cut.rfind(c) for c in "。！？!?；\n")
    return cut[: m + 1] if m >= limit * 0.5 else cut


def finalize_reply(text: str, truncated: bool, limit: int = MAX_REPLY_CHARS) -> str:
    """回复收尾：大模型因 token 用完被截断时，退到最后一个完整句子；再按字数上限截断"""
    t = (text or "").strip()
    if truncated and t:
        m = max(t.rfind(c) for c in "。！？!?；\n")
        if m >= len(t) * 0.4:
            t = t[: m + 1]
    return trim_reply(t, limit)


# ── 图片提问 ──
_IMAGE_PATH = re.compile(r"^/uploads/assistant/[0-9a-f]{32}\.(jpg|png|webp)$")
DEFAULT_IMAGE_QUESTION = "请帮我看看这张图片里的问题，先别急着给答案，一步步引导我思考。"


def valid_image_path(path: str | None) -> bool:
    return bool(path and _IMAGE_PATH.match(path))


def sniff_image_type(raw: bytes) -> tuple[str, str] | None:
    """按文件头判断图片类型，返回 (媒体类型, 扩展名)；不是 jpg / png / webp 返回 None（不信任客户端声明的类型）"""
    if raw[:3] == b"\xff\xd8\xff":
        return "image/jpeg", "jpg"
    if raw[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png", "png"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "image/webp", "webp"
    return None


def summary_due(new_message_count: int) -> bool:
    return new_message_count >= SUMMARY_EVERY


# ── 提示词 ──
BASE_PROMPT = """你是 MESH 数理化 AI 学习伙伴，面向初高中学生，语气亲切、鼓励、口语化。
教学原则：
1. 采用启发式引导：先问学生是怎么想的，再用提问、类比、图示等方式一步步引导，不要一上来就给完整答案；学生明确说「直接告诉我答案 / 讲解一下」时，再给出清晰的讲解。
2. 每次回复不超过 400 字，只用纯文本，不要使用 Markdown 符号（不要 #、*、```、表格），需要分点时用「1.」「2.」；数学符号尽量用文字或常见符号表达（如 x²、√、≤）。
3. 不编造事实；不确定时直说，并建议和老师确认。与学习无关的闲聊可以简短回应，再自然地拉回学习。
4. 结尾可以抛出一个小问题让学生继续思考，但不要一次问多个问题。"""


def build_system_prompt(strategy: dict | None, state_text: str, insight: str, silence: bool, nickname: str | None) -> str:
    parts = [BASE_PROMPT]
    if strategy:
        parts.append(
            f"本轮使用的启发策略：【{strategy['name']}】——{strategy['description']}"
            + (f"\n示例话术：{strategy['example']}" if strategy.get("example") else "")
        )
    if silence:
        parts.append("学生说过想自己思考，现在处于「沉默模式」：只回答学生明确提出的问题，回答简短，不要主动追问、不要给额外提示。")
    if state_text:
        parts.append("【这位同学的学习情况】\n" + state_text)
    if insight:
        parts.append(
            "【老师 / 系统记录的个人特点】\n" + insight
            + "\n（用这些信息让讲解更贴合他：比如用他感兴趣的事物做类比、按他的状态调整语气。"
              "标有「【敏感】」的内容只用来调整你的语气和节奏，不要直接向学生提起，也不要复述。）"
        )
    if nickname:
        parts.append(f"学生昵称：{nickname}（偶尔称呼即可，不要每句都叫）")
    return "\n\n".join(parts)


AHA_CONFIRM_PROMPT = """你是学习分析助手。判断学生最新这句话是否表明他「真正理解了刚才讨论的内容」（理解突破），而不是敷衍的「懂了」。
只输出 JSON：{"aha": true或false, "insight": "不超过30字，概括学生领悟了什么（aha为false时留空）"}。
学生只是说「懂了」但没有体现任何思路或理由时，aha 取 false；学生用自己的话复述出关键思路，或给出正确的推理，aha 取 true。"""

ACHIEVEMENT_PROMPT = """你是 MESH 数理化 AI 学习伙伴。学生刚刚产生了理解突破：{insight}。
请写一段简短的成就感反馈（不超过 120 字，纯文本，不用 Markdown）：1）具体肯定他刚才用到的思路或动作（不要空泛夸奖）；2）可以提一句这体现了哪种能力；3）最后邀请他再来一道加深。语气真诚、有温度。"""

SUMMARY_PROMPT = """你是学习分析助手。根据「已有摘要」和「新增对话」，更新这位学生与 AI 学习伙伴的对话摘要。
要求：不超过 100 字；第三人称；概括学生最近在学习上遇到的困难、涉及的知识点、理解进展；不要出现学生原话和个人隐私；只输出摘要文本。"""
