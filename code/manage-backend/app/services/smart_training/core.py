"""智能训练：打分与组卷（纯函数，不依赖数据库，可单元测试 / 离线模拟）

思路：
1. 把学生的各类数据变成「信号」（Signals）：五力得分、知识点薄弱度（带时间衰减的平滑错误率）、题型薄弱度、
   待攻克 / 已攻克的题、收藏、近期困惑（来自 AI 助手聊天）、做题历史。
2. 给范围内每道题按三种用途分别打分：弱项强化 / 强项拓展 / 复习与探索。
3. 按槽位配比（默认 弱项 60% / 强项 20% / 复习探索 20%）在各槽位里做加权随机抽取（不取最高分，保证每次不一样）；
   近期困惑的知识点至少占一个槽位；已选题型 / 知识点越多，同类再被选的概率越低（保证多样性）。
4. 每道题带一个「推荐理由」标签。

所有权重、配比都可以通过维度配置的 smart_params 覆盖，没有配置时用 DEFAULT_PARAMS。
"""
import math
import random
from dataclasses import dataclass, field
from datetime import datetime

POWERS = ["INSIGHT", "CONSTRUCT", "DEDUCE", "ADAPT", "MIGRATE"]

DEFAULT_PARAMS: dict = {
    # 槽位配比：弱项强化 / 强项拓展 / 复习与探索
    "slots": {"weak": 0.6, "strong": 0.2, "review": 0.2},
    # 近期困惑（AI 助手聊天）的知识点至少占几道题
    "intent_min_slots": 1,
    # 弱项槽位的打分权重
    "weights": {
        "kp_weak": 1.0,      # 知识点薄弱度
        "pending": 0.8,      # 在待攻克里
        "type_weak": 0.4,    # 题型薄弱度
        "power_fit": 0.5,    # 与薄弱的五力匹配
        "intent": 1.2,       # 近期困惑
        "fav": 0.3,          # 收藏
        "novelty": 0.15,     # 没做过
    },
    "half_life_days": 14,           # 做题历史的时间衰减半衰期
    "intent_half_life_days": 7,     # 聊天困惑的衰减半衰期
    "prior": [1.0, 2.0],            # 平滑错误率的先验 (错, 对)：没有数据时错误率 = 1/3
    "recent_penalty": 0.8,          # 最近做过的题扣分
    "temperature": 0.35,            # 抽取的随机程度：越小越偏向高分，越大越随机
    "diversity_type": 0.5,          # 同题型再被选的权重倍数
    "diversity_kp": 0.7,            # 同知识点再被选的权重倍数
    "review_intervals_days": [1, 3, 7, 14],   # 已攻克题的复习间隔
}

REASON_LABELS = {
    "intent": "你提到的困惑",
    "weak_kp": "薄弱知识点",
    "pending": "待攻克巩固",
    "type_weak": "题型强化",
    "power": "弱项五力",
    "strength": "强项拓展",
    "due": "到期复习",
    "fav": "收藏回顾",
    "new": "新知识点探索",
    "general": "综合推荐",
}


@dataclass
class QInfo:
    id: int
    question_type: str | None
    difficulty: str | None
    kp_ids: list[int]
    primary_power: str | None = None
    power_weights: dict[str, float] = field(default_factory=dict)


@dataclass
class Signals:
    now: datetime
    powers: dict[str, float] = field(default_factory=dict)             # 五力最终得分（没有画像为空）
    kp_stats: dict[int, tuple[float, float]] = field(default_factory=dict)    # kp_id → (加权作答数, 加权错误数)
    type_stats: dict[str, tuple[float, float]] = field(default_factory=dict)  # 题型 → (加权作答数, 加权错误数)
    answered: dict[int, tuple[datetime, bool]] = field(default_factory=dict)  # 题目 → (最近一次作答时间, 是否答对)
    pending: set[int] = field(default_factory=set)                     # 待攻克的题
    mastered: dict[int, datetime] = field(default_factory=dict)        # 已攻克的题 → 攻克时间
    favorites: set[int] = field(default_factory=set)
    intents: dict[int, float] = field(default_factory=dict)            # 知识点 → 近期困惑强度（已衰减，0~1）
    recent_ids: set[int] = field(default_factory=set)                  # 最近做过的题（避重复）


@dataclass
class Pick:
    question_id: int
    tag: str
    label: str
    slot: str
    score: float


def merge_params(override: dict | None) -> dict:
    p = {k: (dict(v) if isinstance(v, dict) else v) for k, v in DEFAULT_PARAMS.items()}
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(p.get(k), dict):
            p[k].update(v)
        else:
            p[k] = v
    return p


def smoothed_error(att: float, err: float, prior: list[float]) -> float:
    """平滑错误率：做得少时靠近先验，避免「做 1 题错 1 题 = 100% 错」"""
    return (err + prior[0]) / (att + prior[0] + prior[1])


def decay(age_days: float, half_life_days: float) -> float:
    return 0.5 ** (max(age_days, 0.0) / max(half_life_days, 0.1))


def power_gaps(powers: dict[str, float]) -> dict[str, float]:
    """五力缺口：得分低于平均为正（弱项），高于平均为负（强项），范围约 -1 ~ 1"""
    if not powers:
        return {}
    mean = sum(powers.values()) / len(powers)
    return {p: max(-1.0, min(1.0, (mean - s) / 40.0)) for p, s in powers.items()}


def _kp_weak(q: QInfo, sig: Signals, params: dict) -> float:
    if not q.kp_ids:
        return smoothed_error(0, 0, params["prior"])
    return max(smoothed_error(*sig.kp_stats.get(k, (0.0, 0.0)), params["prior"]) for k in q.kp_ids)


def _kp_attempts(q: QInfo, sig: Signals) -> float:
    return max((sig.kp_stats.get(k, (0.0, 0.0))[0] for k in q.kp_ids), default=0.0)


def _type_weak(q: QInfo, sig: Signals, params: dict) -> float:
    if not sig.type_stats or not q.question_type:
        return 0.0
    tot_att = sum(a for a, _ in sig.type_stats.values())
    tot_err = sum(e for _, e in sig.type_stats.values())
    base = smoothed_error(tot_att, tot_err, params["prior"])
    mine = smoothed_error(*sig.type_stats.get(q.question_type, (0.0, 0.0)), params["prior"])
    return max(0.0, min(1.0, (mine - base) * 2.0))


def _power_fit(q: QInfo, gaps: dict[str, float], positive: bool) -> float:
    """题目考查的五力与学生弱项（positive=True）/ 强项（False）的匹配度，0~1"""
    if not gaps:
        return 0.0
    w = dict(q.power_weights) if q.power_weights else ({q.primary_power: 1.0} if q.primary_power else {})
    total = sum(w.values())
    if total <= 0:
        return 0.0
    fit = 0.0
    for p, v in w.items():
        g = gaps.get(p, 0.0)
        fit += (max(g, 0.0) if positive else max(-g, 0.0)) * (v / total)
    return min(1.0, fit * 2.0)


def _intent(q: QInfo, sig: Signals) -> float:
    return max((sig.intents.get(k, 0.0) for k in q.kp_ids), default=0.0)


def _due(q: QInfo, sig: Signals, params: dict) -> float:
    """已攻克的题按间隔复习：距攻克（或上次作答）超过间隔才算到期，越久越急"""
    t = sig.mastered.get(q.id)
    if t is None:
        return 0.0
    last = sig.answered.get(q.id, (t, True))[0]
    days = (sig.now - max(t, last)).total_seconds() / 86400
    intervals = params["review_intervals_days"]
    if days < intervals[0]:
        return 0.0
    return min(1.0, days / max(intervals[-1], 1))


def _difficulty_fit(q: QInfo, mastery: float, slot: str) -> float:
    """难度匹配：弱项里掌握很差的先做基础题；强项往上拔一档。不匹配只打折，不排除"""
    d = q.difficulty or "basic"
    if slot == "weak":
        want = {"basic"} if mastery < 0.5 else {"basic", "advanced"}
    elif slot == "strong":
        want = {"advanced", "challenge"}
    else:
        return 1.0
    return 1.0 if d in want else 0.6


def score_question(q: QInfo, slot: str, sig: Signals, params: dict, gaps: dict[str, float]) -> tuple[float, str]:
    """返回 (分数, 主要原因标签)"""
    w = params["weights"]
    kp_weak = _kp_weak(q, sig, params)
    mastery = 1.0 - kp_weak
    never = q.id not in sig.answered
    parts: dict[str, float]
    if slot == "weak":
        parts = {
            "weak_kp": w["kp_weak"] * kp_weak,
            "pending": w["pending"] * (1.0 if q.id in sig.pending else 0.0),
            "type_weak": w["type_weak"] * _type_weak(q, sig, params),
            "power": w["power_fit"] * _power_fit(q, gaps, True),
            "intent": w["intent"] * _intent(q, sig),
            "fav": w["fav"] * (1.0 if q.id in sig.favorites else 0.0),
            "new": w["novelty"] * (1.0 if never else 0.0),
        }
    elif slot == "strong":
        attempts = _kp_attempts(q, sig)
        parts = {
            # 强项：知识点掌握得好（做过几次且错得少）+ 考查的是强项五力
            "strength": 0.6 * _power_fit(q, gaps, False) + 0.4 * (mastery if attempts >= 2 else 0.0),
            "fav": w["fav"] * (1.0 if q.id in sig.favorites else 0.0),
            "new": w["novelty"] * (1.0 if never else 0.0),
        }
    else:  # review
        parts = {
            "due": 1.5 * _due(q, sig, params),
            "new": 0.4 * (1.0 if never else 0.0) * (1.0 if _kp_attempts(q, sig) < 1 else 0.5),
            "fav": 0.3 * (1.0 if q.id in sig.favorites else 0.0),
            "intent": 0.5 * _intent(q, sig),
        }
    base = sum(parts.values())
    base *= _difficulty_fit(q, mastery, slot)
    if q.id in sig.recent_ids:
        base -= params["recent_penalty"]
    tag = max(parts, key=lambda k: parts[k]) if any(v > 0 for v in parts.values()) else "general"
    return base, tag


def allocate_slots(n: int, ratios: dict[str, float]) -> dict[str, int]:
    """把 n 个名额按比例分到各槽位（最大余数法）"""
    keys = ["weak", "strong", "review"]
    total = sum(max(ratios.get(k, 0.0), 0.0) for k in keys) or 1.0
    raw = {k: n * max(ratios.get(k, 0.0), 0.0) / total for k in keys}
    out = {k: int(raw[k]) for k in keys}
    for k in sorted(keys, key=lambda k: -(raw[k] - out[k]))[: n - sum(out.values())]:
        out[k] += 1
    return out


def _weighted_choice(items: list[tuple[QInfo, float, str]], temperature: float, rng: random.Random):
    """按 softmax(score / T) 加权随机选一个"""
    top = max(s for _, s, _ in items)
    ws = [math.exp((s - top) / max(temperature, 1e-6)) for _, s, _ in items]
    return rng.choices(items, weights=ws)[0]


def compose(
    questions: list[QInfo],
    sig: Signals,
    n: int,
    override: dict | None = None,
    rng: random.Random | None = None,
) -> list[Pick]:
    """从 questions（抽取池）里组出至多 n 道题"""
    rng = rng or random.Random()
    params = merge_params(override)
    gaps = power_gaps(sig.powers)
    n = min(n, len(questions))
    if n <= 0:
        return []
    # 最近做过的题：没做过的题够用就完全不选它们，不够才放回来（并在打分里扣分）
    fresh = [q for q in questions if q.id not in sig.recent_ids]
    if len(fresh) >= n:
        questions = fresh

    quota = allocate_slots(n, params["slots"])
    # 近期困惑保底：从弱项槽位里划出名额（弱项没有名额就从强项 / 复习里划）
    intent_qs = [q for q in questions if _intent(q, sig) > 0.05]
    need_intent = min(params["intent_min_slots"], len(intent_qs), n)

    chosen: list[Pick] = []
    used: set[int] = set()
    type_count: dict[str, int] = {}
    kp_count: dict[int, int] = {}

    def candidates(slot: str, pool: list[QInfo]):
        out = []
        for q in pool:
            if q.id in used:
                continue
            s, tag = score_question(q, slot, sig, params, gaps)
            # 多样性：已选过的题型 / 知识点再选的概率降低
            f = params["diversity_type"] ** type_count.get(q.question_type or "", 0)
            for k in q.kp_ids[:1]:
                f *= params["diversity_kp"] ** kp_count.get(k, 0)
            out.append((q, s + math.log(max(f, 1e-6)) * params["temperature"], tag))
        return out

    def take(slot: str, pool: list[QInfo], force_tag: str | None = None):
        items = candidates(slot, pool)
        if not items:
            return False
        q, s, tag = _weighted_choice(items, params["temperature"], rng)
        tag = force_tag or tag
        chosen.append(Pick(q.id, tag, REASON_LABELS.get(tag, "综合推荐"), slot, round(s, 3)))
        used.add(q.id)
        type_count[q.question_type or ""] = type_count.get(q.question_type or "", 0) + 1
        for k in q.kp_ids[:1]:
            kp_count[k] = kp_count.get(k, 0) + 1
        return True

    for _ in range(need_intent):
        if take("weak", intent_qs, force_tag="intent"):
            for slot in ("weak", "review", "strong"):
                if quota[slot] > 0:
                    quota[slot] -= 1
                    break

    for slot in ("weak", "strong", "review"):
        for _ in range(quota[slot]):
            if not take(slot, questions):
                break

    # 某个槽位没题可选（比如没有强项数据）时，用弱项打分补齐
    while len(chosen) < n:
        if not take("weak", questions):
            break

    rng.shuffle(chosen)
    return chosen
