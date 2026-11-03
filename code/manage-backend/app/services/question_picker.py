"""训练抽题：按「题型比例 + 难度比例」从抽取池里选题，并尽量避开学生最近做过的题

纯函数，不依赖数据库，便于单元测试。调用方负责准备抽取池（已启用、未删除的题目）。

规则：
1. 题型名额：把 n 道题按 type_ratio 分到各题型（最大余数法）；没配置时五种题型平均分，
   比如 n=5 时每种题型 1 道。某题型的题不够，缺的名额按比例转给还有题的题型。
2. 题型内选题：先从「最近没做过」的题里选；不够再从做过的里补（尽量避开，但不因此少出题）。
3. 难度：每个名额按 difficulty_ratio 的权重在「还有题的难度档」里抽一档，该档没有题就自动落到别的档。
4. 最后整体打乱顺序，让题型不按固定次序出现。
"""
import random
from collections import defaultdict
from typing import Iterable

from app.services.answer_judge import APPLICATION, FILL_BLANK, MULTIPLE_CHOICE, SINGLE_CHOICE, TRUE_FALSE

QUESTION_TYPES = [SINGLE_CHOICE, MULTIPLE_CHOICE, TRUE_FALSE, FILL_BLANK, APPLICATION]


def allocate_by_type(
    n: int,
    available: dict[str, int],
    type_ratio: dict[str, float] | None = None,
) -> dict[str, int]:
    """把 n 个名额分给各题型：按比例（最大余数法），每个题型不超过自己的题量；总量不足 n 时有多少出多少"""
    types = [t for t in available if available[t] > 0]
    quota = {t: 0 for t in available}
    remaining = min(n, sum(available[t] for t in types))
    while remaining > 0 and types:
        weights = {t: float((type_ratio or {}).get(t, 1) if type_ratio else 1) for t in types}
        if sum(weights.values()) <= 0:
            weights = {t: 1.0 for t in types}
        total_w = sum(weights.values())
        raw = {t: remaining * weights[t] / total_w for t in types}
        base = {t: int(raw[t]) for t in types}
        left = remaining - sum(base.values())
        # 最大余数优先；余数相同时按题型固定顺序，保证结果可复现
        order = sorted(types, key=lambda t: (-(raw[t] - base[t]), QUESTION_TYPES.index(t) if t in QUESTION_TYPES else 99))
        for t in order[:left]:
            base[t] += 1
        # 超出自身题量的按上限截断，剩余名额下一轮在其它题型里再分
        capped = False
        for t in types:
            room = available[t] - quota[t]
            take = min(base[t], room)
            quota[t] += take
            remaining -= take
            if take < base[t]:
                capped = True
        types = [t for t in types if quota[t] < available[t]]
        if not capped:
            break
    return quota


def pick_questions(
    pool: Iterable[dict],
    n: int,
    type_ratio: dict[str, float] | None = None,
    difficulty_ratio: dict[str, float] | None = None,
    avoid_ids: Iterable[int] = (),
    rng: random.Random | None = None,
) -> list[int]:
    """从 pool（元素含 id / question_type / difficulty）里选出至多 n 道题的 id"""
    rng = rng or random.Random()
    avoid = set(avoid_ids)
    by_type: dict[str, list[dict]] = defaultdict(list)
    for q in pool:
        by_type[q.get("question_type") or "UNKNOWN"].append(q)

    quota = allocate_by_type(n, {t: len(v) for t, v in by_type.items()}, type_ratio)
    picked: list[int] = []
    for t, k in quota.items():
        picked.extend(_pick_in_type(by_type[t], k, difficulty_ratio, avoid, rng))
    rng.shuffle(picked)
    return picked


def _pick_in_type(items: list[dict], k: int, difficulty_ratio, avoid: set[int], rng: random.Random) -> list[int]:
    fresh = [q for q in items if q["id"] not in avoid]
    seen = [q for q in items if q["id"] in avoid]
    chosen: list[int] = []
    for _ in range(k):
        candidates = fresh or seen          # 优先没做过的
        buckets: dict[str, list[dict]] = defaultdict(list)
        for q in candidates:
            buckets[q.get("difficulty") or "basic"].append(q)
        levels = list(buckets)
        weights = [max(float((difficulty_ratio or {}).get(lv, 0)), 0) for lv in levels]
        if not difficulty_ratio or sum(weights) <= 0:
            weights = [1.0] * len(levels)    # 没配置比例，或配置里没有这些难度：各档等权
        level = rng.choices(levels, weights=weights)[0]
        q = rng.choice(buckets[level])
        chosen.append(q["id"])
        (fresh if q in fresh else seen).remove(q)
    return chosen
