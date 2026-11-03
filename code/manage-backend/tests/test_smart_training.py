import random
from collections import Counter
from datetime import datetime, timedelta, timezone

from app.services.smart_training.core import (
    QInfo, Signals, allocate_slots, compose, decay, merge_params, power_gaps, smoothed_error,
)

NOW = datetime(2026, 11, 3, tzinfo=timezone.utc)
T = ["SINGLE_CHOICE", "MULTIPLE_CHOICE", "TRUE_FALSE", "FILL_BLANK", "APPLICATION"]


def pool(kps=(1, 2, 3, 4), per=6):
    out, i = [], 0
    for k in kps:
        for j in range(per):
            i += 1
            out.append(QInfo(i, T[j % 5], "basic" if j % 2 == 0 else "advanced", [k],
                             primary_power="INSIGHT", power_weights={"INSIGHT": 4, "CONSTRUCT": 2, "DEDUCE": 2, "ADAPT": 1, "MIGRATE": 1}))
    return out


def sig(**kw):
    return Signals(now=NOW, **kw)


def test_smoothing_and_decay():
    assert smoothed_error(0, 0, [1, 2]) == 1 / 3
    assert smoothed_error(1, 1, [1, 2]) < 0.6            # 做 1 错 1 不会被判成 100% 错
    assert decay(14, 14) == 0.5 and decay(0, 14) == 1


def test_power_gaps_sign():
    g = power_gaps({"INSIGHT": 80, "CONSTRUCT": 40, "DEDUCE": 60, "ADAPT": 60, "MIGRATE": 60})
    assert g["INSIGHT"] < 0 < g["CONSTRUCT"]


def test_allocate_slots():
    assert allocate_slots(5, {"weak": 0.6, "strong": 0.2, "review": 0.2}) == {"weak": 3, "strong": 1, "review": 1}
    assert sum(allocate_slots(7, {"weak": 0.6, "strong": 0.2, "review": 0.2}).values()) == 7


def test_empty_signals_still_works():
    """没有任何历史（新用户、聊天为空）也能正常出题"""
    qs = pool()
    ids = [p.question_id for p in compose(qs, sig(), 5, rng=random.Random(1))]
    assert len(ids) == 5 and len(set(ids)) == 5


def test_weak_kp_preferred():
    qs = pool()
    s = sig(kp_stats={1: (10, 9), 2: (10, 1), 3: (10, 1), 4: (10, 1)})
    cnt = Counter()
    for seed in range(200):
        for p in compose(qs, s, 5, rng=random.Random(seed)):
            cnt[next(q for q in qs if q.id == p.question_id).kp_ids[0]] += 1
    assert cnt[1] > cnt[2] and cnt[1] > cnt[3] and cnt[1] > cnt[4]


def test_intent_guaranteed():
    qs = pool()
    s = sig(intents={3: 0.9}, kp_stats={1: (10, 9)})
    for seed in range(50):
        picks = compose(qs, s, 5, rng=random.Random(seed))
        kp3 = [p for p in picks if next(q for q in qs if q.id == p.question_id).kp_ids[0] == 3]
        assert kp3 and any(p.tag == "intent" for p in picks)


def test_recent_avoided_when_enough():
    qs = pool()
    recent = {q.id for q in qs[:12]}
    for seed in range(30):
        ids = {p.question_id for p in compose(qs, sig(recent_ids=recent), 5, rng=random.Random(seed))}
        assert not ids & recent


def test_due_review_selected():
    qs = pool(per=3)
    due_q = qs[0]
    s = sig(mastered={due_q.id: NOW - timedelta(days=10)}, answered={due_q.id: (NOW - timedelta(days=10), True)})
    hits = sum(due_q.id in {p.question_id for p in compose(qs, s, 5, rng=random.Random(i))} for i in range(100))
    assert hits > 55


def test_type_diversity():
    qs = pool()
    for seed in range(30):
        types = {next(q for q in qs if q.id == p.question_id).question_type for p in compose(qs, sig(), 5, rng=random.Random(seed))}
        assert len(types) >= 3


def test_small_pool():
    qs = pool(kps=(1,), per=2)
    assert len(compose(qs, sig(), 5)) == 2
    assert compose([], sig(), 5) == []


def test_params_override():
    p = merge_params({"weights": {"intent": 9}, "slots": {"weak": 1}})
    assert p["weights"]["intent"] == 9 and p["weights"]["kp_weak"] == 1.0 and p["slots"]["weak"] == 1
