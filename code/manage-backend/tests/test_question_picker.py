import random

from app.services.question_picker import allocate_by_type, pick_questions

T = ["SINGLE_CHOICE", "MULTIPLE_CHOICE", "TRUE_FALSE", "FILL_BLANK", "APPLICATION"]


def mk(start, qtype, n, diff="basic"):
    return [{"id": start + i, "question_type": qtype, "difficulty": diff} for i in range(n)]


def full_pool(per=10):
    pool = []
    for i, t in enumerate(T):
        pool += mk(i * 100, t, per)
    return pool


def types_of(ids, pool):
    m = {q["id"]: q["question_type"] for q in pool}
    return [m[i] for i in ids]


def test_default_equal_split_five():
    pool = full_pool()
    ids = pick_questions(pool, 5, rng=random.Random(1))
    assert sorted(types_of(ids, pool)) == sorted(T)


def test_ratio_split():
    q = allocate_by_type(10, {t: 20 for t in T}, {"SINGLE_CHOICE": 4, "MULTIPLE_CHOICE": 2, "TRUE_FALSE": 2, "FILL_BLANK": 1, "APPLICATION": 1})
    assert q == {"SINGLE_CHOICE": 4, "MULTIPLE_CHOICE": 2, "TRUE_FALSE": 2, "FILL_BLANK": 1, "APPLICATION": 1}


def test_shortage_shifts_to_other_types():
    pool = mk(0, "SINGLE_CHOICE", 1) + mk(100, "FILL_BLANK", 10) + mk(200, "TRUE_FALSE", 10)
    ids = pick_questions(pool, 5, rng=random.Random(2))
    assert len(ids) == 5 and len(set(ids)) == 5
    assert types_of(ids, pool).count("SINGLE_CHOICE") == 1


def test_pool_smaller_than_n():
    pool = full_pool(1)[:3]
    assert len(pick_questions(pool, 5)) == 3


def test_empty_pool():
    assert pick_questions([], 5) == []


def test_avoid_seen_when_enough():
    pool = full_pool(4)
    seen = {q["id"] for q in pool if q["id"] % 100 < 2}   # 每个题型 2 道做过
    for s in range(20):
        ids = pick_questions(pool, 5, avoid_ids=seen, rng=random.Random(s))
        assert not set(ids) & seen


def test_seen_used_when_not_enough():
    pool = mk(0, "SINGLE_CHOICE", 3)
    ids = pick_questions(pool, 3, avoid_ids={0, 1}, rng=random.Random(3))
    assert sorted(ids) == [0, 1, 2]


def test_difficulty_ratio_respected():
    pool = mk(0, "SINGLE_CHOICE", 50, "basic") + mk(100, "SINGLE_CHOICE", 50, "advanced")
    ids = pick_questions(pool, 20, difficulty_ratio={"basic": 100, "advanced": 0}, rng=random.Random(4))
    assert all(i < 100 for i in ids)


def test_difficulty_falls_back_when_level_missing():
    pool = mk(0, "SINGLE_CHOICE", 6, "basic")
    ids = pick_questions(pool, 5, difficulty_ratio={"basic": 50, "advanced": 35, "challenge": 15}, rng=random.Random(5))
    assert len(ids) == 5


def test_no_duplicates():
    pool = full_pool(3)
    for s in range(30):
        ids = pick_questions(pool, 12, rng=random.Random(s))
        assert len(ids) == len(set(ids)) == 12
