from app.services.wrong_book import build_tree, next_status


def test_wrong_always_pending():
    for cur in (None, "unreview", "aha_achieved"):
        for dim in ("KNOWLEDGE_POINT", "ERROR_QUESTIONS", "RANDOM"):
            assert next_status(cur, False, dim) == "unreview"


def test_correct_in_error_training_masters_pending():
    assert next_status("unreview", True, "ERROR_QUESTIONS") == "aha_achieved"
    assert next_status("reviewing", True, "ERROR_QUESTIONS") == "aha_achieved"


def test_correct_elsewhere_no_change():
    assert next_status("unreview", True, "KNOWLEDGE_POINT") is None
    assert next_status("unreview", True, "RANDOM") is None
    assert next_status(None, True, "ERROR_QUESTIONS") is None
    assert next_status("aha_achieved", True, "ERROR_QUESTIONS") is None


def test_tree_counts_dedup():
    chapters = [(1, "A"), (2, "B")]
    kps = [(10, "a1", 1), (11, "a2", 1), (20, "b1", 2)]
    qs = [(100, [10, 11]), (101, [10]), (102, [20]), (103, [999]), (104, [])]
    t = build_tree(chapters, kps, qs)
    assert t["count"] == 3                       # 103 不在本学期知识点里，104 无知识点
    a, b = t["chapters"]
    assert a["count"] == 2                       # 100 跨两个知识点只算一次
    assert [p["count"] for p in a["points"]] == [2, 1]
    assert b["count"] == 1 and b["points"][0]["count"] == 1


def test_tree_empty():
    t = build_tree([(1, "A")], [(10, "a", 1)], [])
    assert t["count"] == 0 and t["chapters"][0]["points"][0]["count"] == 0
