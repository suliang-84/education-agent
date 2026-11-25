"""学生画像的「建议」与各维度的「总结」：把画像里的关键数据交给大模型，一次调用同时生成。

  - 建议（页面底部）：结合认知能力与学习数据，挑出最有效的最多 5 条；
  - 总结（学习时长 / 训练次数 / 答题数 / 正确率 / AI 提问 五个维度卡片）：每个维度最多 5 条，只陈述事实与发现，不给建议。

原则：
  - 不按维度分类建议、不追求数量，只要「提分最有效」的几条，按重要程度排序；
  - 每条都带数据依据，能让老师 / 家长直接照着做；样本太少就少给，不凑数；
  - 不把姓名、手机号等能识别个人的信息交给大模型（只传年级和统计数据）；
  - 大模型较慢，结果按（学生、日期范围）缓存一段时间；调用失败时退回规则建议，页面不会空。
"""
import hashlib
import json
import re
import time

MAX_ITEMS = 5          # 建议、每个维度的总结，都最多这么多条
DIMS = {"study_time": "学习时长", "training": "训练次数", "answers": "答题数", "accuracy": "正确率", "ai_asks": "AI 提问"}
CACHE_TTL = 30 * 60
_CACHE: dict[tuple, tuple[float, str, list[str], dict[str, list[str]]]] = {}

SYSTEM_PROMPT = f"""你是一位资深的初高中学习规划老师，正在为一名学生的老师 / 家长分析学习情况。
我会给你这名学生的画像数据（JSON）：基本信息、五力认知能力（测试得分与近期实战正确率）、各维度学习统计（「各维度数据」）、薄弱知识点与错因、学习状态、预警、个人洞察等。
请一次输出两部分内容：

【一】summaries：学习时长（study_time）、训练次数（training）、答题数（answers）、正确率（accuracy）、AI 提问（ai_asks）五个维度各自的「总结」。
- 每个维度最多 {MAX_ITEMS} 条，挑最值得关注的发现，宁缺毋滥；该维度没有数据时给空数组。
- 只陈述事实和发现（现状、变化、特点、异常），不要给建议、不要出现「建议」「应该」「可以」之类的措辞。
- 每条一句话，不超过 40 字，带具体数字（必须来自数据，不要编造）；同一维度内不要重复。

【二】advice：给老师 / 家长的「提分建议」，综合全部信息，最多 {MAX_ITEMS} 条，只给对提分最有效的，宁缺毋滥。
- 按重要程度从高到低排序；不按维度分组，也不要写分类标签；合并同类建议。
- 每条先点明依据（具体数字或知识点名，数字必须来自数据），再给能马上照做的具体动作（做什么、做多少、什么时候做），不超过 70 字。
- 要结合五力认知特点：测试能力与实战表现的落差、最弱 / 最强的一力、偏好的学习方式，不要通用的学习鸡汤。
- 已经做得好的地方不用建议；数据太少时少给，不凑数。
- 带【敏感】标记的个人洞察只用来调整措辞的温和程度，不要直接写出其中的情绪、家庭等内容。

只输出一个 JSON 对象，不要任何解释或多余文字，格式：
{{"summaries": {{"study_time": ["…"], "training": ["…"], "answers": ["…"], "accuracy": ["…"], "ai_asks": ["…"]}}, "advice": ["…"]}}"""


def _pick(d: dict | None, *keys):
    d = d or {}
    return {k: d.get(k) for k in keys if d.get(k) is not None}


def _drop_sensitive(text: str | None) -> str:
    """去掉个人洞察里标了【敏感】的句子"""
    parts = re.split(r"(?<=[。！？\n])", text or "")
    return "".join(x for x in parts if "【敏感】" not in x).strip()


_SKIP_KEYS = {"series", "highlights", "tips", "has_data", "unit", "kp_top", "types_by_subject", "weak_by_subject", "strong_by_subject", "trend"}


def _slim(v, depth=0):
    """维度数据瘦身：去掉按天的序列等体积大的字段，列表只留前 8 项，保证传给大模型的内容精炼"""
    if isinstance(v, dict):
        return {k: _slim(x, depth + 1) for k, x in v.items() if k not in _SKIP_KEYS}
    if isinstance(v, list):
        return [_slim(x, depth + 1) for x in v[:8]]
    return v


def _dim_data(d: dict | None):
    return _slim(d) if d and d.get("has_data", True) else None


def build_context(p: dict) -> dict:
    """从画像里挑出对建议有用的数据（不含姓名、联系方式等）"""
    basic = p.get("basic") or {}
    cog = p.get("cognitive") or {}
    mastery = p.get("mastery") or {}
    diag = p.get("diagnosis") or {}
    summ = p.get("summary") or {}
    ctx: dict = {
        "年级": basic.get("grade"), "学期": basic.get("semester"),
        "统计范围": (p.get("range") or {}).get("label"),
        "近30天学习天数": basic.get("active_days_30"),
    }
    if cog.get("has_profile"):
        ins = cog.get("insights") or {}
        ctx["认知能力"] = {
            "五力测试得分": cog.get("final"), "最强": cog.get("primary_strength"), "最弱": cog.get("primary_weakness"),
            "次弱": cog.get("secondary_weakness"), "偏好": cog.get("preferred_force"), "推荐学习方式": cog.get("recommended_mode"),
            "各力实战对比": [_pick(x, "label", "test", "accuracy", "answered", "gap", "status", "delta", "avg_seconds", "blank_rate") for x in ins.get("powers") or []],
            "均衡度": ins.get("balance"), "标签": cog.get("tags"),
        }
    else:
        ctx["认知能力"] = "尚未完成五力测试"
    ctx["关键指标"] = [{"指标": k.get("label"), "值": k.get("value"), "较前一周期": k.get("delta")} for k in p.get("kpis") or []]
    ctx["学习状态"] = {"状态": summ.get("status"), "原因": summ.get("status_reason"), "投入度": summ.get("engagement_score"),
                       "要点": [d.get("text") for d in (summ.get("status_detail") or {}).get("drivers") or []][:6]}
    ctx["各维度数据"] = {label: _dim_data(p.get(k)) for k, label in DIMS.items() if _dim_data(p.get(k))}
    ctx["薄弱知识点"] = [_pick(x, "name", "error_rate", "count", "wrong", "blank", "rush", "thoughtful", "trend") | ({"可能的前置": x["root_kp"]["name"]} if x.get("root_kp") else {})
                     for x in (mastery.get("weak_kps") or [])[:6]]
    ctx["强项知识点"] = [_pick(x, "name", "accuracy", "count") for x in (mastery.get("strong_kps") or [])[:3]]
    ctx["错题与掌握"] = _pick(mastery, "wrong_pending", "wrong_mastered", "wrong_mastered_rate", "stubborn_questions", "semester_progress")
    ctx["错因诊断"] = _pick(diag, "blank_rate", "causes", "repeat", "retention")
    ctx["待处理预警"] = [{"规则": w.get("rule_name"), "说明": w.get("message")} for w in (p.get("warnings") or {}).get("open") or []][:5]
    traits = p.get("traits") or {}
    ctx["个人洞察"] = _drop_sensitive(traits.get("personal_insight"))[:400] or None
    ctx["学习信息摘要"] = (traits.get("learning_summary") or "")[:300] or None
    return {k: v for k, v in ctx.items() if v not in (None, "", [], {})}


def _clean_list(items) -> list[str]:
    out: list[str] = []
    for x in items if isinstance(items, list) else []:
        x = str(x).strip().strip("\"“”")
        if len(x) >= 6 and x not in out:
            out.append(x)
    return out[:MAX_ITEMS]


def parse_result(text: str) -> tuple[list[str], dict[str, list[str]]]:
    """解析大模型输出的 JSON 对象，返回（建议, {维度: 总结}）。解析不出来返回 ([], {})"""
    t = re.sub(r"^```[a-zA-Z]*\n?|\n?```$", "", (text or "").strip()).strip()
    m = re.search(r"\{.*\}", t, re.S)
    if not m:
        return [], {}
    try:
        data = json.loads(m.group(0))
    except ValueError:
        return [], {}
    if not isinstance(data, dict):
        return [], {}
    sums = data.get("summaries") if isinstance(data.get("summaries"), dict) else {}
    return _clean_list(data.get("advice")), {k: _clean_list(sums.get(k)) for k in DIMS if k in sums}


def fallback_items(p: dict) -> list[str]:
    """大模型不可用时的规则建议：综合建议 + 各维度拆出来的建议，去重后最多 MAX_ITEMS 条（各维度总结此时沿用规则生成的 tips）"""
    summ = p.get("summary") or {}
    out: list[str] = []
    for t in list(summ.get("tips") or []) + [a["text"] for a in summ.get("dim_advice") or []]:
        if t not in out:
            out.append(t)
    return out[:MAX_ITEMS]


async def generate(p: dict, key: tuple, refresh: bool = False) -> dict:
    ctx = build_context(p)
    payload = json.dumps(ctx, ensure_ascii=False, default=str)
    digest = hashlib.md5(payload.encode()).hexdigest()
    hit = _CACHE.get(key)
    if hit and not refresh and hit[1] == digest and time.time() - hit[0] < CACHE_TTL:
        return {"items": hit[2], "summaries": hit[3], "source": "ai", "generated_at": hit[0]}
    from app.core import llm
    advice, sums = [], {}
    try:
        advice, sums = parse_result(await llm.chat(SYSTEM_PROMPT, payload[:14000]))
    except Exception:   # 大模型未配置 / 超时 / 限流：退回规则建议
        pass
    if not advice and not any(sums.values()):
        return {"items": fallback_items(p), "summaries": {}, "source": "rule", "generated_at": time.time()}
    now = time.time()
    _CACHE[key] = (now, digest, advice, sums)
    return {"items": advice, "summaries": sums, "source": "ai", "generated_at": now}
