from datetime import datetime, timedelta, timezone

import pytest

from app.core.exceptions import AppException
from app.services import profile_config as pc
from app.services.profile_warning_service import evaluate


def confs(**over):
    c = {r["code"]: pc.merge_rule_conf(r["code"], None) for r in pc.RULES}
    for code, patch in over.items():
        c[code] = pc.merge_rule_conf(code, patch)
    return c


def base(**kw):
    m = {"is_minor": True, "idle_days": 0, "has_answers": True, "recent_n": 0, "recent_acc": None, "prev_n": 0, "prev_acc": None,
         "kp_flags": {}, "wrong_counts": [], "issued_14": 0, "answered_14": 0, "night_ratio": None, "fast_n": 0, "fast_wrong_ratio": None,
         "profile_at": datetime.now(timezone.utc), "emotion_history": []}
    m.update(kw)
    return m


def codes(hits):
    return {h["rule_code"]: h["level"] for h in hits}


def test_no_train_tiers():
    assert codes(evaluate(base(idle_days=2), confs())) == {}
    assert codes(evaluate(base(idle_days=3), confs()))["NO_TRAIN"] == "notice"
    assert codes(evaluate(base(idle_days=8), confs()))["NO_TRAIN"] == "attention"
    assert codes(evaluate(base(idle_days=20), confs()))["NO_TRAIN"] == "critical"


def test_disabled_rule_not_triggered():
    assert "NO_TRAIN" not in codes(evaluate(base(idle_days=20), confs(NO_TRAIN={"enabled": False})))


def test_acc_drop_needs_samples():
    m = base(recent_n=5, recent_acc=30.0, prev_n=20, prev_acc=80.0)
    assert "ACC_DROP" not in codes(evaluate(m, confs()))
    m = base(recent_n=12, recent_acc=30.0, prev_n=20, prev_acc=80.0)
    assert codes(evaluate(m, confs()))["ACC_DROP"] == "attention"


def test_kp_streak_uses_latest_answers():
    # flags 按时间从新到旧：最近 3 次都错才触发
    assert "KP_STREAK_WRONG" in codes(evaluate(base(kp_flags={1: {"name": "A", "flags": [False, False, False, True]}}), confs()))
    assert "KP_STREAK_WRONG" not in codes(evaluate(base(kp_flags={1: {"name": "A", "flags": [False, True, False, False]}}), confs()))


def test_late_night_only_for_minor():
    m = base(recent_n=20, night_ratio=50.0)
    assert "LATE_NIGHT" in codes(evaluate(m, confs()))
    assert "LATE_NIGHT" not in codes(evaluate({**m, "is_minor": False}, confs()))


def test_test_missing_and_stale():
    assert "TEST_MISSING" in codes(evaluate(base(profile_at=None), confs()))
    old = datetime.now(timezone.utc) - timedelta(days=120)
    assert "PROFILE_STALE" in codes(evaluate(base(profile_at=old), confs()))


def emo(*levels):
    now = datetime.now(timezone.utc)
    return [{"at": now, "level": lv, "reason": "测试依据"} for lv in levels]


def test_chat_negative_uses_llm_judgement():
    # 没有判断记录不触发
    assert "CHAT_NEGATIVE" not in codes(evaluate(base(), confs()))
    # 默认：明显低落且连续 1 次
    assert codes(evaluate(base(emotion_history=emo("normal", "significant")), confs()))["CHAT_NEGATIVE"] == "critical"
    assert "CHAT_NEGATIVE" not in codes(evaluate(base(emotion_history=emo("significant", "mild")), confs()))
    assert "CHAT_NEGATIVE" not in codes(evaluate(base(emotion_history=emo("normal")), confs()))


def test_chat_negative_consecutive_and_urgent():
    c = confs(CHAT_NEGATIVE={"params": {"min_level": "mild", "consecutive": 2}})
    assert "CHAT_NEGATIVE" not in codes(evaluate(base(emotion_history=emo("normal", "mild")), c))
    assert "CHAT_NEGATIVE" in codes(evaluate(base(emotion_history=emo("mild", "significant")), c))
    # 判为需要重点关注时不看连续次数
    c2 = confs(CHAT_NEGATIVE={"params": {"min_level": "significant", "consecutive": 3}})
    assert "CHAT_NEGATIVE" in codes(evaluate(base(emotion_history=emo("urgent")), c2))


def test_config_defaults_and_merge():
    c = pc.merge_rule_conf("NO_TRAIN", {"params": {"notice_days": 5}, "level": "critical"})
    assert c["params"]["notice_days"] == 5 and c["params"]["attention_days"] == 7
    assert c["level"] == "notice"   # 分档规则不能单独改级别


@pytest.mark.asyncio
async def test_save_rules_validation():
    class Db:   # 校验失败发生在写库之前，不会碰到数据库
        pass
    with pytest.raises(AppException):
        await pc.save_rules(Db(), {"rules": {"NO_TRAIN": {"params": {"notice_days": 9, "attention_days": 7, "critical_days": 14}}}}, 1)
    with pytest.raises(AppException):
        await pc.save_rules(Db(), {"rules": {"ACC_DROP": {"params": {"drop_pp": 0}}}}, 1)
    with pytest.raises(AppException):
        await pc.save_rules(Db(), {"rules": {"NOPE": {}}}, 1)
    with pytest.raises(AppException):
        await pc.save_weights(Db(), {"frequency": 50, "streak": 20, "complete": 25, "careful": 15}, 1)


def test_emotion_parse():
    from app.services.assistant import emotion
    assert emotion.parse('{"level": "significant", "reason": "反复表达压抑"}') == {"level": "significant", "reason": "反复表达压抑"}
    assert emotion.parse('```json\n{"level":"NORMAL","reason":"x"}\n```')["level"] == "normal"
    assert emotion.parse('{"level": "bad"}') is None
    assert emotion.parse("没有 JSON") is None
    assert len(emotion.parse('{"level":"mild","reason":"' + "长" * 200 + '"}')["reason"]) == emotion.MAX_REASON


@pytest.mark.asyncio
async def test_save_rules_select_validation():
    class Db:
        pass
    with pytest.raises(AppException):
        await pc.save_rules(Db(), {"rules": {"CHAT_NEGATIVE": {"params": {"min_level": "bogus", "consecutive": 1}}}}, 1)


def test_engagement_careful_needs_samples():
    from app.services.profile_service import _summary
    beh = {"_sessions": [], "last_active_date": None, "sessions_range": 12, "streak_days": 7, "complete_rate": 100.0,
           "fast_wrong_ratio": 40.0, "fast_wrong_samples": 5}
    mastery = {"weak_kps": [], "wrong_pending": 0}
    weeks = [{"weeks_ago": w, "answered": 0, "accuracy": None} for w in (3, 2, 1, 0)]
    # 前三项满分、样本不够：认真作答不计入，折算后仍是 100，而不是被拉低
    r = _summary({}, {"has_profile": True}, mastery, beh, {}, weeks, 50)
    assert r["engagement_parts"]["careful"] is None and r["engagement_score"] == 100
    # 样本够且「快而错」≥ 40%：这一项为 0；错题复盘没有样本不计入，整体 = 前三项权重 ÷ 前四项权重（默认 35+15+20 ÷ 85）
    r = _summary({}, {"has_profile": True}, mastery, {**beh, "fast_wrong_samples": 30}, {}, weeks, 50)
    assert r["engagement_parts"]["careful"] == 0 and r["engagement_parts"]["review"] is None and r["engagement_score"] == 82


def _engagement(mastery, sessions=(), weights=None):
    from datetime import datetime, timezone
    from app.services.profile_service import _summary
    beh = {"_sessions": list(sessions), "last_active_date": None, "sessions_range": 12, "streak_days": 7, "complete_rate": 100.0,
           "fast_wrong_ratio": 0.0, "fast_wrong_samples": 30}
    weeks = [{"weeks_ago": w, "answered": 0, "accuracy": None} for w in (3, 2, 1, 0)]
    r = _summary({}, {"has_profile": True}, {"weak_kps": [], **mastery}, beh, {}, weeks, 50, weights)
    return r["engagement_parts"], r["engagement_score"]


def test_engagement_review_part():
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    rev = lambda: {"started_at": now, "training_dimension": "ERROR_QUESTIONS", "session_status": "completed", "total_questions": 5}
    # 错题不足 3 道：不计入
    p, score = _engagement({"wrong_pending": 1, "wrong_mastered": 1, "wrong_mastered_rate": 50.0})
    assert p["review"] is None and score == 100
    # 攻克率 50%、近 30 天错题集训练 2 次（满分 4 次）：0.6×0.5 + 0.4×0.5 = 0.5
    p, score = _engagement({"wrong_pending": 5, "wrong_mastered": 5, "wrong_mastered_rate": 50.0}, [rev(), rev()])
    assert p["review"] == 50 and p["review_sessions"] == 2 and score == 92   # 前四项满分 85 + 15×0.5
    # 错题堆着不处理：攻克率 0、没做过错题集训练 → 0 分，整体被拉低
    p, score = _engagement({"wrong_pending": 10, "wrong_mastered": 0, "wrong_mastered_rate": 0.0})
    assert p["review"] == 0 and score == 85
    # 权重为 0（旧配置兼容）：这一项不影响总分
    p, score = _engagement({"wrong_pending": 10, "wrong_mastered": 0, "wrong_mastered_rate": 0.0},
                           weights={"frequency": 40, "streak": 20, "complete": 25, "careful": 15, "review": 0})
    assert score == 100


# ── 提分行动 ──────────────────────────────────────────────────

def test_kp_trend():
    from app.services.profile_actions import kp_trend
    assert kp_trend([True, False]) is None                              # 做得太少不判断
    assert kp_trend([False, False, False, True, True, True]) == "up"
    assert kp_trend([True, True, True, False, False, False]) == "down"
    assert kp_trend([True, False, True, True, False, True]) == "flat"


def test_kp_advice_by_cause():
    from app.services.profile_actions import kp_advice
    assert kp_advice(2, 2, 2, 0, None) is None                          # 样本不够
    assert "动笔" in kp_advice(6, 6, 5, 1, "flat")                      # 空答为主
    assert "秒答" in kp_advice(6, 5, 1, 3, "flat")                      # 秒答为主
    assert "不要再刷题" in kp_advice(8, 6, 0, 1, "flat")                # 认真做仍错且没进步：换讲解
    assert "正在进步" in kp_advice(8, 6, 0, 1, "up")


def _ctx(**kw):
    d = {"answered": 50, "blank_rate": 10, "blank_by_type": [], "repeat": {"questions": 0, "gain": None}, "type_time": [], "retention": None}
    ctx = {"diagnosis": d, "mastery": {"weak_kps": [], "wrong_pending": 0}, "behavior": {"time_buckets": []}, "retention": None,
           "status": "状态平稳", "wrong_pending": 0, "cognitive": {"has_profile": True}}
    ctx.update(kw)
    return ctx


def test_actions_blank_not_repeated_per_kp():
    from app.services.profile_actions import build_actions
    kp = {"name": "角的分类", "error_rate": 80, "advice": "80% 的错题是没作答就提交，先让学生愿意动笔"}
    ctx = _ctx(diagnosis={**_ctx()["diagnosis"], "blank_rate": 60, "blank_by_type": [{"label": "填空题", "answered": 10, "rate": 100}]},
               mastery={"weak_kps": [kp], "wrong_pending": 0})
    acts = build_actions(ctx)
    assert sum("没作答就提交" in a for a in acts) == 1                   # 总体提示过，知识点上不再重复


def test_actions_best_time_bucket_and_cap():
    from app.services.profile_actions import build_actions
    b = [{"label": "上午", "count": 20, "accuracy": 70.0}, {"label": "深夜", "count": 20, "accuracy": 30.0}]
    acts = build_actions(_ctx(behavior={"time_buckets": b}))
    assert any("上午" in a and "深夜" in a for a in acts)
    many = _ctx(status="近期懈怠", wrong_pending=3, mastery={"weak_kps": [{"name": f"k{i}", "error_rate": 90, "advice": "先讲解"} for i in range(3)], "wrong_pending": 3},
                diagnosis={**_ctx()["diagnosis"], "repeat": {"questions": 6, "gain": -3}})
    assert len(build_actions(many)) <= 5


def test_find_prerequisites():
    from app.services.profile_actions import find_prerequisites

    def kp(i, order, err, att=6, ch=1):
        return {"id": i, "name": f"k{i}", "chapter_id": ch, "order": (0, 0, order), "attempts": att, "error_rate": err}

    roots = find_prerequisites([kp(1, 1, 80), kp(2, 2, 90), kp(3, 3, 70), kp(4, 4, 20), kp(5, 1, 90, ch=2)])
    assert roots[2]["id"] == 1 and roots[3]["id"] == 1          # 单元内最靠前的薄弱知识点是根源
    assert 1 not in roots                                       # 最靠前的那个自己没有前置
    assert 4 not in roots                                       # 不薄弱的不处理
    assert 5 not in roots                                       # 别的单元不算
    assert find_prerequisites([kp(1, 1, 80, att=2), kp(2, 2, 90)]) == {}   # 前置样本不够不下结论


def test_actions_include_new_insights():
    from app.services.profile_actions import build_actions
    ctx = _ctx(insights={
        "fatigue": {"verdict": "每次训练后半段正确率明显下降"},
        "explanation": {"verdict": "看过智能解答后再做正确率提高了"},
        "misconceptions": [{"text": "某题总选同一个错误答案"}],
        "bias": {"text": "单选题 80% 都选 A"},
    }, mastery={"weak_kps": [{"name": "B", "error_rate": 80, "advice": None, "root_kp": {"name": "A"}}], "wrong_pending": 0})
    acts = build_actions(ctx)
    assert len(acts) <= 5
    joined = "".join(acts)
    assert "先补「A」再练「B」" in joined and "后半段" in joined and "同一个错误答案" in joined


def test_status_detail_drivers():
    from app.services.profile_service import _status_detail
    mastery = {"weak_kps": [{"name": "一元二次方程", "error_rate": 70, "attempts": 10, "trend": "down"}], "strong_kps": [],
               "wrong_pending": 12, "stubborn_questions": 0}
    diag = {"wrong": 20, "causes": [{"key": "blank", "label": "没作答就提交", "ratio": 60}, {"key": "thoughtful", "label": "认真做了仍然错", "ratio": 40}]}
    r = _status_detail("近期懈怠", {"streak_days": 0}, mastery, {}, diag, {}, {"n": 40, "acc": 50.0, "n_prev": 40, "acc_prev": 70.0}, 9, 1, 5, 6)
    assert [m["key"] for m in r["metrics"]] == ["sessions", "accuracy", "answered"]
    assert [(m.get("delta"), m.get("unit")) for m in r["metrics"]] == [(-4, "次"), (-20.0, "%"), (0, "题")]
    assert r["metrics"][1]["hint"] == "较前 30 天-20.0pp"
    assert len(r["drivers"]) <= 4 and all(d["tone"] == "warn" for d in r["drivers"])
    assert "9 天没有训练" in r["drivers"][0]["text"]
    # 样本不足时不做对比、不下错因结论
    r = _status_detail("状态平稳", {"streak_days": 0}, {}, {}, {"wrong": 3, "causes": []}, {}, {"n": 5, "acc": 80, "n_prev": 2, "acc_prev": 10}, 0, 0, 0, None)
    assert r["metrics"][1]["hint"] is None and r["drivers"] == []


def _range_summary(recent, answered=20, days=7, **beh_over):
    from app.services.profile_service import Range
    from app.services.profile_service import _summary
    beh = {"_sessions": [], "last_active_date": None, "sessions_range": 3, "streak_days": 7, "complete_rate": 100.0,
           "fast_wrong_ratio": 0.0, "fast_wrong_samples": 30, "active_days": 4, **beh_over}
    weeks = [{"weeks_ago": d, "label": str(d), "answered": 0, "accuracy": None} for d in range(6, -1, -1)]
    return _summary({}, {"has_profile": True}, {"weak_kps": [], "wrong_pending": 0}, beh, {}, weeks, answered, None, None, None, recent, Range.last(days))


def test_range_week_status_and_engagement():
    # 近一周：和前一周比较正确率；训练频次 3 次即满分
    r = _range_summary({"n": 20, "acc": 80.0, "n_prev": 20, "acc_prev": 60.0})
    assert r["status"] == "稳步提升" and "提高 20.0 个百分点" in r["status_reason"]
    assert r["trend"]["unit"] == "day" and r["trend"]["delta"] == 20.0 and r["engagement_parts"]["frequency"] == 100
    assert r["status_detail"]["metrics"][0]["label"] == "训练次数" and r["status_detail"]["metrics"][2]["label"] == "答题数"
    r = _range_summary({"n": 20, "acc": 57.0, "n_prev": 20, "acc_prev": 60.0})
    assert r["status"] == "状态平稳"
    r = _range_summary({"n": 20, "acc": 40.0, "n_prev": 20, "acc_prev": 60.0})
    assert r["status"] == "遇到瓶颈"
    # 前一周答题太少：不对比
    r = _range_summary({"n": 20, "acc": 80.0, "n_prev": 3, "acc_prev": 10.0})
    assert r["status"] == "状态平稳" and r["trend"]["delta"] is None
    # 近一周答题不足 8 道：不下结论；近一个月的门槛仍是 20 道
    assert _range_summary({"n": 7, "acc": 80.0}, answered=7)["status"] == "数据不足"
    assert _range_summary({"n": 12}, answered=12, days=30)["status"] == "数据不足"


def test_range_build_and_thresholds():
    from datetime import timedelta
    import pytest
    from app.core.exceptions import AppException
    from app.services.profile_service import Range, today_bj
    r = Range.build(None, None)                      # 默认近 7 天，到昨天为止（不含今天）
    assert r.days == 7 and r.end == today_bj() - timedelta(days=1) and r.is_recent and r.label == "近 7 天" and r.daily
    assert (r.freq_full, r.review_full, r.min_answered, r.points) == (3, 1, 8, 7)
    r = Range.last(30)
    assert (r.freq_full, r.review_full, r.min_answered, r.points, r.cmp_len, r.daily) == (12, 4, 20, 5, 15, False)
    # 过去的范围：按所选范围统计，起止都含当天（北京时间 0 点到次日 0 点）
    past = Range.build(str(today_bj() - timedelta(days=20)), str(today_bj() - timedelta(days=11)))
    assert past.days == 10 and not past.is_recent and past.label == "所选 10 天" and past.until - past.since == timedelta(days=10)
    for bad in [("x", None), (None, str(today_bj() + timedelta(days=1))), (str(today_bj()), str(today_bj() - timedelta(days=1))),
                (str(today_bj() - timedelta(days=91)), None)]:
        with pytest.raises(AppException):
            Range.build(*bad)
    assert Range.build(str(today_bj() - timedelta(days=90)), None).days == 90


def test_cognitive_insights():
    from datetime import datetime, timezone
    from app.services.profile_service import Range, _cognitive_insights
    rng = Range.last(7)
    cog = {"final": {"INSIGHT": 72, "CONSTRUCT": 59, "DEDUCE": 68, "ADAPT": 63, "MIGRATE": 53},
           "previous_test": {"tested_at": datetime(2026, 10, 1, tzinfo=timezone.utc), "final": {"INSIGHT": 70, "CONSTRUCT": 59, "DEDUCE": 68, "ADAPT": 55, "MIGRATE": 53}}}
    st = {  # n, c, blank, sec, n0, c0
        "INSIGHT": {"n": 20, "c": 17, "blank": 0, "sec": 20, "n0": 10, "c0": 5},      # 85%，比前一段 +35，高于测试 72 → 实战更强
        "CONSTRUCT": {"n": 20, "c": 7, "blank": 10, "sec": 40, "n0": 10, "c0": 5},     # 35%，低于测试 59 达 24，50% 空答
        "DEDUCE": {"n": 20, "c": 12, "blank": 1, "sec": 30, "n0": 8, "c0": 6},
        "ADAPT": {"n": 4, "c": 3, "blank": 0, "sec": 30, "n0": 0, "c0": 0},           # 做得太少
        "MIGRATE": {"n": 2, "c": 1, "blank": 0, "sec": 30, "n0": 0, "c0": 0},         # 最弱却几乎没练：占比 2/66≈3%
    }
    r = _cognitive_insights(cog, st, rng)
    by = {x["key"]: x for x in r["powers"]}
    assert by["INSIGHT"]["status"] == "above" and by["INSIGHT"]["delta"] == 35.0
    assert by["CONSTRUCT"]["status"] == "below" and by["CONSTRUCT"]["gap"] == -24.0 and by["CONSTRUCT"]["blank_rate"] == 50.0
    assert by["ADAPT"]["status"] == "few" and by["ADAPT"]["gap"] is None and by["ADAPT"]["test_change"] == 8
    texts = [h["text"] for h in r["highlights"]]
    assert any("迁移力" in t and "只占" in t for t in texts)                 # 最弱却没练
    assert any("建构力" in t and "低 24.0 个百分点" in t and "50.0% 的题没作答" in t for t in texts)
    assert any("洞察力" in t and "比前 7 天提高 35.0" in t for t in texts) and any("较上次测试" in t and "调适力 +8" in t for t in texts)
    assert [h["tone"] for h in r["highlights"]] == sorted([h["tone"] for h in r["highlights"]], key=lambda t: t != "warn")   # 需要关注的在前
    assert r["balance"]["level"] == "略有偏科" and r["balance"]["weakest"] == "MIGRATE"
    # 样本很少时不下结论
    r = _cognitive_insights(cog, {"INSIGHT": {"n": 3, "c": 3}}, rng)
    assert r["highlights"] == [] or all("只占" not in h["text"] for h in r["highlights"])


def test_kpi_cards():
    from datetime import datetime, timedelta
    from app.services.profile_service import _kpi_cards, Range
    rng = Range.last(7)
    inside, before = rng.since + timedelta(hours=3), rng.prev_since + timedelta(hours=3)
    beh = {"_sessions": [{"started_at": inside}, {"started_at": inside}, {"started_at": before}]}
    k = {"ad1": 5, "ad0": 3, "t1": 3600, "t0": 1800, "ai1": 6, "ai0": 2}
    recent = {"n": 20, "acc": 80.0, "n_prev": 10, "acc_prev": 70.0}
    cards = _kpi_cards(k, beh, recent, rng)
    assert [c["key"] for c in cards] == ["study_time", "sessions", "answered", "accuracy", "ai_asks"]
    c = {x["key"]: x for x in cards}
    assert c["study_time"]["value"] == "1 小时" and c["study_time"]["delta"] == 30      # 与学习时长标签页的 fmtMin 同写法（整数不带 .0）
    assert c["sessions"]["value"] == "2 次" and c["sessions"]["delta"] == 1
    assert c["answered"]["value"] == "20 题" and c["answered"]["delta"] == 10
    assert c["accuracy"]["value"] == "80.0%" and c["accuracy"]["delta"] == 10.0 and c["ai_asks"]["delta"] == 4
    # 前一周期答题太少：正确率不做对比；本期没答题：显示 —
    c2 = {x["key"]: x for x in _kpi_cards(k, beh, {"n": 0, "acc": None, "n_prev": 2, "acc_prev": 10}, rng)}
    assert c2["accuracy"]["value"] == "—" and c2["accuracy"]["delta"] is None and c2["study_time"]["value"] == "—"


def test_kpi_bucket_of_matches_sql_rule():
    from datetime import timedelta
    from app.services.profile_service import Range
    r = Range.last(7)
    assert r.bucket_of(r.since + timedelta(hours=1)) == 6 and r.bucket_of(r.until - timedelta(hours=1)) == 0
    w = Range.last(30)       # 30 天按周分 5 格：开始日起每 7 天一格，0 = 最后一格
    assert w.points == 5 and w.bucket_of(w.since + timedelta(hours=1)) == 4 and w.bucket_of(w.until - timedelta(hours=1)) == 0


def test_study_time_build():
    from datetime import timedelta
    from app.services.profile_service import _study_time_build, Range
    rng = Range.last(7)
    subs = {1: ("MATH", "数学"), 2: ("PHYSICS", "物理"), 3: ("CHEMISTRY", "化学")}
    d = lambda i: rng.end - timedelta(days=i)
    rows = [{"d": d(0), "sid": 1, "t": 1200, "n": 6, "c": 5}, {"d": d(1), "sid": 1, "t": 300, "n": 5, "c": 2},
            {"d": d(2), "sid": 2, "t": 240, "n": 4, "c": 2}, {"d": d(3), "sid": 1, "t": 360, "n": 5, "c": 2}, {"d": d(5), "sid": 1, "t": 600, "n": 6, "c": 5}]
    r = _study_time_build(rows, subs, rng, 2700, 1200, 480, [{"h": 9, "t": 600}, {"h": 20, "t": 1800}, {"h": 23, "t": 300}])
    assert [(b["key"], b["minutes"]) for b in r["time_buckets"]] == [("morning", 10.0), ("afternoon", 0.0), ("evening", 30.0), ("night", 5.0)]
    assert r["has_data"] and len(r["series"]) == 7 and r["series"][-1]["minutes"]["MATH"] == 20.0 and r["series"][-1]["total"] == 20.0
    assert [x["code"] for x in r["subjects"]][:3] == ["MATH", "PHYSICS", "CHEMISTRY"] and r["subjects"][2]["minutes"] == 0
    assert r["stats"]["total_minutes"] == 45.0 and r["stats"]["delta_pct"] == 125 and r["stats"]["active_days"] == 5
    assert r["stats"]["best_day"]["minutes"] == 20.0 and r["stats"]["avg_per_session"] == 8.0
    # 单日最长的上一周期对比：没传（前一段没学习）为 None，传了按分钟给
    assert r["stats"]["prev_best_minutes"] is None
    assert _study_time_build(rows, subs, rng, 2700, 1200, 480, None, None, 0, 750)["stats"]["prev_best_minutes"] == 12.5
    texts = " ".join(h["text"] for h in r["highlights"])
    assert "化学完全没有学习" in texts and "增加 125%" in texts
    # 学得久的日子（20、10 分钟）正确率高、学得短的日子低
    assert "正相关" in texts
    # 时间太少：不下结论
    assert _study_time_build(rows[:1] and [{"d": d(0), "sid": 1, "t": 60, "n": 1, "c": 1}], subs, rng, 60, 0, None)["has_data"] is False


def test_study_time_types_and_tips():
    from datetime import timedelta
    from app.services.profile_service import _study_time_build, Range
    rng = Range.last(7)
    subs = {1: ("MATH", "数学"), 2: ("PHYSICS", "物理"), 3: ("CHEMISTRY", "化学")}
    d = lambda i: rng.end - timedelta(days=i)
    rows = [{"d": d(0), "sid": 1, "t": 1500, "n": 6, "c": 5}, {"d": d(1), "sid": 1, "t": 300, "n": 5, "c": 2}, {"d": d(2), "sid": 1, "t": 240, "n": 4, "c": 2}]
    types = [{"dim": "UNIT", "t": 1500, "n": 1}, {"dim": "KNOWLEDGE_POINT", "t": 540, "n": 5}]
    r = _study_time_build(rows, subs, rng, 2040, 1200, 120, [{"h": 23, "t": 2040}], types, 8)
    assert [(x["key"], x["share"]) for x in r["types"]] == [("KNOWLEDGE_POINT", 26.5), ("UNIT", 73.5)]     # 顺序按小程序练习方式
    tips = " ".join(r["tips"])
    assert "平均只有 2.0 分钟" in tips and "深夜" in tips and "物理、化学" in tips and len(r["tips"]) <= 5
    # 有积压错题、错题集几乎没练：提醒（用一份别的问题都没有的数据，避免被 5 条上限挤掉）
    rows2 = [{"d": d(i), "sid": 1 + i % 3, "t": 900, "n": 4, "c": 3} for i in range(7)]
    r2 = _study_time_build(rows2, subs, rng, 6300, 6000, 900, [{"h": 19, "t": 6300}], [{"dim": "KNOWLEDGE_POINT", "t": 6300, "n": 7}], 8)
    assert any("错题集只占学习时间的 0%" in t for t in r2["tips"]) and any("练习方式比较单一" in t for t in r2["tips"])
    # 一切正常时给一条肯定的话
    ok = _study_time_build([{"d": d(i), "sid": 1 + i % 3, "t": 900, "n": 4, "c": 3} for i in range(7)], subs, rng, 6300, 6000, 900, [{"h": 19, "t": 6300}],
                           [{"dim": "KNOWLEDGE_POINT", "t": 3000, "n": 3}, {"dim": "ERROR_QUESTIONS", "t": 3300, "n": 3}], 0)
    assert ok["tips"] == ["学习时间的节奏和分配都比较健康，继续保持"]


def test_fmt_minutes_matches_study_tab():
    """顶部「学习时长」卡和学习时长标签页的总时长，同一个数必须显示成一样（前端 fmtMin：< 60 分钟保留 1 位小数，否则换成小时保留 1 位）"""
    from app.services.profile_service import _fmt_minutes
    assert _fmt_minutes(5220) == "1.5 小时"          # 87 分钟：先取整再换算会得到 1.4
    assert _fmt_minutes(3570) == "59.5 分钟"         # 59.5 分钟：先取整会变成 1.0 小时
    assert _fmt_minutes(2712) == "45.2 分钟" and _fmt_minutes(2700) == "45 分钟"
    assert _fmt_minutes(7200) == "2 小时" and _fmt_minutes(5334) == "1.5 小时" and _fmt_minutes(0) == "0 分钟"


def test_study_time_weekday_weekend_avg_divides_by_days_in_range():
    """工作日 / 周末日均 = 总时长 ÷ 所选范围内这类日子的天数（没学习的天也算），不是 ÷ 有学习的天数"""
    from datetime import date
    from app.services.profile_service import _study_time_build, Range
    subs = {1: ("MATH", "数学")}
    rng = Range(date(2026, 11, 9), date(2026, 11, 15))          # 周一到周日：5 个工作日 + 2 个周末日
    rows = [{"d": date(2026, 11, 9), "sid": 1, "t": 600, "n": 4, "c": 3},      # 周一 10 分钟
            {"d": date(2026, 11, 11), "sid": 1, "t": 1200, "n": 6, "c": 5},    # 周三 20 分钟
            {"d": date(2026, 11, 14), "sid": 1, "t": 3600, "n": 8, "c": 6}]    # 周六 60 分钟
    st = _study_time_build(rows, subs, rng, 5400, 0, 600)["stats"]
    assert st["weekday_avg"] == 6.0          # (10 + 20) ÷ 5，而不是 ÷ 2 = 15
    assert st["weekend_avg"] == 30.0         # 60 ÷ 2，周日没学习也算一天，而不是 ÷ 1 = 60
    # 范围里没有周末：周末日均为 None；没有工作日：工作日日均为 None
    assert _study_time_build(rows[:2], subs, Range(date(2026, 11, 9), date(2026, 11, 11)), 1800, 0, 600)["stats"]["weekend_avg"] is None
    only_we = [{"d": date(2026, 11, 14), "sid": 1, "t": 3600, "n": 8, "c": 6}]
    st2 = _study_time_build(only_we, subs, Range(date(2026, 11, 14), date(2026, 11, 15)), 3600, 0, 600)["stats"]
    assert st2["weekday_avg"] is None and st2["weekend_avg"] == 30.0
    # 工作日全勤、周末没学：周末日均是 0（不是「没数据」）
    st3 = _study_time_build(rows[:2], subs, rng, 1800, 0, 600)["stats"]
    assert st3["weekend_avg"] == 0.0 and st3["weekday_avg"] == 6.0


def test_study_time_kp_top5_per_subject():
    """知识点学习时长 Top5：按学科分组、按用时从多到少；用时 0 的不上榜；每科最多 5 个"""
    from datetime import date
    from app.services.profile_service import _study_time_build, Range
    subs = {1: ("MATH", "数学"), 2: ("PHYSICS", "物理")}
    rng = Range(date(2026, 11, 9), date(2026, 11, 15))
    rows = [{"d": date(2026, 11, 9), "sid": 1, "t": 6000, "n": 10, "c": 8}]
    kp = [{"sid": 1, "kid": i, "name": f"数学知识点{i}", "t": 600 * i, "n": i} for i in range(1, 8)]      # 7 个，用时 10~70 分钟
    kp += [{"sid": 1, "kid": 99, "name": "没记录用时", "t": 0, "n": 3}, {"sid": 2, "kid": 50, "name": "牛顿第二定律", "t": 900, "n": 4}]
    top = _study_time_build(rows, subs, rng, 6000, 0, 600, None, None, 0, None, kp)["kp_top"]
    assert [x["name"] for x in top["MATH"]] == ["数学知识点7", "数学知识点6", "数学知识点5", "数学知识点4", "数学知识点3"]
    assert top["MATH"][0]["minutes"] == 70.0 and top["MATH"][0]["answered"] == 7
    assert [x["name"] for x in top["PHYSICS"]] == ["牛顿第二定律"] and top["PHYSICS"][0]["minutes"] == 15.0
    assert "CHEMISTRY" not in top
    assert _study_time_build(rows, subs, rng, 6000, 0, 600)["kp_top"] == {}


def _sess_rows():
    """固定的一周（2026-11-09 周一 ~ 11-15 周日）+ 前一周，每条：开始时间、状态、练习方式、下发题数、实际作答题数"""
    from datetime import datetime
    from app.services.profile_service import BJ
    subj = {(11, 9): 1, (11, 11): 2, (11, 14): 3}                      # 11/9 数学、11/11 物理、11/14 化学，其余（前一周）数学
    mk = lambda m, d, h, st, dim, tot, ans: {"started_at": datetime(2026, m, d, h, 0, tzinfo=BJ), "session_status": st, "training_dimension": dim,
                                             "total_questions": tot, "answered": ans, "correct": ans // 2, "subject_id": subj.get((m, d), 1)}
    cur = [mk(11, 9, 10, "completed", "KNOWLEDGE_POINT", 5, 5), mk(11, 9, 11, "abandoned", "KNOWLEDGE_POINT", 5, 2),
           mk(11, 11, 20, "abandoned", "ERROR_QUESTIONS", 5, 0), mk(11, 14, 23, "completed", "RANDOM", 5, 5), mk(11, 14, 9, "abandoned", "RANDOM", 5, 0)]
    prv = [mk(11, 3, 10, "completed", "KNOWLEDGE_POINT", 5, 5), mk(11, 3, 15, "completed", "KNOWLEDGE_POINT", 5, 4)]
    return cur + prv


def test_sessions_build_stats():
    from datetime import date
    from app.services.profile_service import _sessions_build, Range
    rng = Range(date(2026, 11, 9), date(2026, 11, 15))
    r = _sessions_build(_sess_rows(), rng)
    st = r["stats"]
    assert r["has_data"] and st["total"] == 5 and st["prev_total"] == 2 and st["active_days"] == 3 and st["done"] == 2
    assert st["avg_per_day"] == 0.7 and st["prev_avg_per_day"] == 0.3                        # 5 ÷ 7、2 ÷ 7（没训练的天也算）
    assert st["best_day"] == {"date": "2026-11-14", "count": 2} and st["prev_best_count"] == 2     # 11/9 和 11/14 都是 2 次，取最近的
    assert st["completion"] == 48.0 and st["prev_completion"] == 90.0                        # 作答 12 ÷ 下发 25；前一周 9 ÷ 10
    assert st["avg_answered"] == 4.0 and st["prev_avg_answered"] == 4.5                      # 只算作答了的训练：(5+2+5)÷3
    assert st["weekday_avg"] == 0.6 and st["weekend_avg"] == 1.0                             # 工作日 3 ÷ 5，周末 2 ÷ 2
    assert st["max_gap_days"] == 2 and st["completeness"] == {"full": 2, "partial": 1, "none": 2}
    # 趋势：按天、从旧到新、完成 / 未完成
    assert [x["label"] for x in r["series"]] == ["11/9", "11/10", "11/11", "11/12", "11/13", "11/14", "11/15"]
    assert {k: r["series"][0][k] for k in ("label", "done", "undone", "total")} == {"label": "11/9", "done": 1, "undone": 1, "total": 2}
    assert r["series"][5]["total"] == 2 and r["series"][6]["total"] == 0
    # 练习方式：顺序同小程序，带占比和做完的比例
    assert [(x["key"], x["count"], x["share"], x["done_rate"]) for x in r["types"]] == [
        ("KNOWLEDGE_POINT", 2, 40.0, 50.0), ("ERROR_QUESTIONS", 1, 20.0, 0.0), ("RANDOM", 2, 40.0, 50.0)]
    assert "weekdays" not in r


def test_sessions_build_tips_and_edges():
    from datetime import date
    from app.services.profile_service import _sessions_build, Range
    rng = Range(date(2026, 11, 9), date(2026, 11, 15))
    tips = " ".join(_sessions_build(_sess_rows(), rng, wrong_pending=8)["tips"])
    assert "2 次训练一题都没答" in tips and "只有 3 天在训练" in tips and "深夜" in tips
    assert "还有 8 道错题" not in tips                                  # 错题集占 20%，不算练得少
    # 没练过错题集、还有积压错题：提醒
    no_err = [x for x in _sess_rows() if x["training_dimension"] != "ERROR_QUESTIONS"]
    assert any("还有 8 道错题" in t and "错题集训练只占 0%（0 次）" in t for t in _sessions_build(no_err, rng, 8)["tips"])
    assert len(_sessions_build(_sess_rows(), rng, 8)["tips"]) <= 5
    # 本期没有训练：没数据
    assert _sessions_build([x for x in _sess_rows() if x["started_at"].day < 8], rng)["has_data"] is False
    # 前一段没有训练：对比值为 None（页面不显示涨跌），其余照常
    only_cur = [x for x in _sess_rows() if x["started_at"].day >= 9]
    st = _sessions_build(only_cur, rng)["stats"]
    assert st["prev_total"] == 0 and st["prev_avg_per_day"] is None and st["prev_best_count"] is None and st["prev_completion"] is None
    # 一周只有周一训练：周末日均 0（不是没数据）；训练天数太少会提醒
    mon = [x for x in _sess_rows() if x["started_at"].day == 9]
    r = _sessions_build(mon, rng)
    assert r["stats"]["weekend_avg"] == 0.0 and r["stats"]["weekday_avg"] == 0.4 and any("周末没有训练记录" in t for t in r["tips"])


def test_sessions_build_by_subject():
    """训练次数趋势按学科拆分：每个点各学科的训练次数、各学科总次数和占比"""
    from datetime import date
    from app.services.profile_service import _sessions_build, Range
    subs = {1: ("MATH", "数学"), 2: ("PHYSICS", "物理"), 3: ("CHEMISTRY", "化学")}
    rng = Range(date(2026, 11, 9), date(2026, 11, 15))
    r = _sessions_build(_sess_rows(), rng, 0, subs)
    assert [(x["code"], x["name"], x["count"], x["share"]) for x in r["subjects"]] == [("MATH", "数学", 2, 40.0), ("PHYSICS", "物理", 1, 20.0), ("CHEMISTRY", "化学", 2, 40.0)]
    assert r["series"][0]["by_subject"] == {"MATH": 2, "PHYSICS": 0, "CHEMISTRY": 0}        # 11/9
    assert r["series"][2]["by_subject"] == {"MATH": 0, "PHYSICS": 1, "CHEMISTRY": 0}        # 11/11
    assert r["series"][5]["by_subject"] == {"MATH": 0, "PHYSICS": 0, "CHEMISTRY": 2}        # 11/14
    assert all(sum(x["by_subject"].values()) == x["total"] for x in r["series"])               # 每个点各学科相加 = 合计
    # 没传学科表 / 学科对不上：归到「其他」，不丢
    r2 = _sessions_build(_sess_rows(), rng)
    assert r2["subjects"][-1]["code"] == "OTHER" and r2["subjects"][-1]["count"] == 5 and r2["subjects"][0]["count"] == 0
    # 有学科 id 但为 None（没法判断）：同样归「其他」
    rows = _sess_rows()
    for x in rows:
        x["subject_id"] = None
    assert _sessions_build(rows, rng, 0, subs)["subjects"][-1] == {"code": "OTHER", "name": "其他", "count": 5, "share": 100.0}


def test_sessions_build_kp_top5():
    """知识点训练次数 Top5：按学科分组、按训练次数从多到少（并列看做完的多少）；每科最多 5 个"""
    from datetime import date
    from app.services.profile_service import _sessions_build, Range
    subs = {1: ("MATH", "数学"), 2: ("PHYSICS", "物理")}
    rng = Range(date(2026, 11, 9), date(2026, 11, 15))
    kp = [{"sid": 1, "kid": i, "name": f"数学知识点{i}", "n": i, "done": i // 2} for i in range(1, 8)]        # 7 个知识点，训练 1~7 次
    kp += [{"sid": 1, "kid": 20, "name": "并列但做完更多", "n": 3, "done": 3}, {"sid": 1, "kid": 21, "name": "没训练", "n": 0, "done": 0},
           {"sid": 2, "kid": 50, "name": "牛顿第二定律", "n": 4, "done": 1}]
    top = _sessions_build(_sess_rows(), rng, 0, subs, kp)["kp_top"]
    assert [x["name"] for x in top["MATH"]] == ["数学知识点7", "数学知识点6", "数学知识点5", "数学知识点4", "并列但做完更多"]      # 训练 3 次的有两个，做完多的在前
    assert top["MATH"][0] == {"id": 7, "name": "数学知识点7", "count": 7, "done": 3}
    assert [x["name"] for x in top["PHYSICS"]] == ["牛顿第二定律"] and "CHEMISTRY" not in top
    assert _sessions_build(_sess_rows(), rng, 0, subs)["kp_top"] == {}


def test_study_time_types_by_subject():
    """类型时长分布按学科区分：types 是所有学科合起来的，types_by_subject 是每个学科自己的分布（占比按本学科总时长算）"""
    from datetime import date
    from app.services.profile_service import _study_time_build, Range
    subs = {1: ("MATH", "数学"), 2: ("PHYSICS", "物理")}
    rng = Range(date(2026, 11, 9), date(2026, 11, 15))
    rows = [{"d": date(2026, 11, 9), "sid": 1, "t": 3600, "n": 10, "c": 8}, {"d": date(2026, 11, 10), "sid": 2, "t": 1200, "n": 6, "c": 3}]
    types = [{"sid": 1, "dim": "KNOWLEDGE_POINT", "t": 2700, "n": 3}, {"sid": 1, "dim": "RANDOM", "t": 900, "n": 2},
             {"sid": 2, "dim": "KNOWLEDGE_POINT", "t": 600, "n": 1}, {"sid": 2, "dim": "UNIT", "t": 600, "n": 1}]
    r = _study_time_build(rows, subs, rng, 4800, 0, 600, None, types)
    # 合起来：知识点 3300 秒 / 总 4800 秒 = 68.8%，随机 18.8%，按单元 12.5%
    assert [(x["key"], x["minutes"], x["sessions"], x["share"]) for x in r["types"]] == [("KNOWLEDGE_POINT", 55.0, 4, 68.8), ("UNIT", 10.0, 1, 12.5), ("RANDOM", 15.0, 2, 18.8)]
    by = r["types_by_subject"]
    assert [(x["key"], x["share"]) for x in by["MATH"]] == [("KNOWLEDGE_POINT", 75.0), ("RANDOM", 25.0)]       # 数学：2700 / 3600、900 / 3600
    assert [(x["key"], x["share"], x["minutes"]) for x in by["PHYSICS"]] == [("KNOWLEDGE_POINT", 50.0, 10.0), ("UNIT", 50.0, 10.0)]
    assert "CHEMISTRY" not in by
    # 老格式（没有学科）：合起来的照常，按学科的全归「其他」
    r2 = _study_time_build(rows, subs, rng, 4800, 0, 600, None, [{"dim": "UNIT", "t": 600, "n": 1}])
    assert r2["types"][0]["key"] == "UNIT" and list(r2["types_by_subject"]) == ["OTHER"]


def test_sessions_build_types_by_subject():
    """练习方式次数分布按学科区分：types 是所有学科合起来的，types_by_subject 是每个学科自己的（占比按本学科的训练数算）"""
    from datetime import date
    from app.services.profile_service import _sessions_build, Range
    subs = {1: ("MATH", "数学"), 2: ("PHYSICS", "物理"), 3: ("CHEMISTRY", "化学")}
    rng = Range(date(2026, 11, 9), date(2026, 11, 15))
    r = _sessions_build(_sess_rows(), rng, 0, subs)
    # 本期 5 次：11/9 数学×2（知识点，完成 + 放弃）、11/11 物理×1（错题集，放弃）、11/14 化学×2（随机，完成 + 放弃）
    assert [(x["key"], x["count"], x["share"]) for x in r["types"]] == [("KNOWLEDGE_POINT", 2, 40.0), ("ERROR_QUESTIONS", 1, 20.0), ("RANDOM", 2, 40.0)]
    by = r["types_by_subject"]
    assert [(x["key"], x["count"], x["share"], x["done_rate"]) for x in by["MATH"]] == [("KNOWLEDGE_POINT", 2, 100.0, 50.0)]
    assert [(x["key"], x["count"], x["share"], x["done_rate"]) for x in by["PHYSICS"]] == [("ERROR_QUESTIONS", 1, 100.0, 0.0)]
    assert [(x["key"], x["count"], x["share"], x["done_rate"]) for x in by["CHEMISTRY"]] == [("RANDOM", 2, 100.0, 50.0)]
    # 各学科的次数相加 = 合计
    assert sum(x["count"] for v in by.values() for x in v) == sum(x["count"] for x in r["types"]) == 5
    assert set(by) == {"MATH", "PHYSICS", "CHEMISTRY"}              # 没有训练的学科不出现


def _ans_data():
    subs = {1: ("MATH", "数学"), 2: ("PHYSICS", "物理"), 3: ("CHEMISTRY", "化学")}
    cube = [{"sid": 1, "qt": "SINGLE_CHOICE", "df": "basic", "n": 20, "c": 15}, {"sid": 1, "qt": "FILL_BLANK", "df": "basic", "n": 30, "c": 10},
            {"sid": 1, "qt": "MULTIPLE_CHOICE", "df": "advanced", "n": 5, "c": 1},
            {"sid": 2, "qt": "SINGLE_CHOICE", "df": "basic", "n": 10, "c": 9}, {"sid": 2, "qt": "TRUE_FALSE", "df": "basic", "n": 5, "c": 5}]
    wrong = [{"sid": 1, "k": "unreview", "n": 6}, {"sid": 1, "k": "aha_achieved", "n": 4}, {"sid": 2, "k": "unreview", "n": 1}]
    kp = [{"sid": 1, "kid": 1, "name": "角的分类", "n": 25, "c": 10}, {"sid": 1, "kid": 2, "name": "余角与补角", "n": 20, "c": 8}, {"sid": 2, "kid": 50, "name": "牛顿第二定律", "n": 8, "c": 7}]
    return subs, cube, wrong, [{"sid": 1, "n": 2}], [{"sid": 1, "n": 3}, {"sid": 2, "n": 1}], kp


def test_answers_build_stats_and_distributions():
    from app.services.profile_service import _answers_build
    subs, cube, wrong, stub, fav, kp = _ans_data()
    r = _answers_build(cube, subs, 100, wrong, stub, fav, kp)
    st = r["stats"]
    assert r["has_data"] and st["total"] == 70 and st["correct"] == 40 and st["accuracy"] == 57.1 and st["prev_total"] == 100
    # 错题 / 顽固错题 / 收藏：总数，以及每个学科的数量
    assert (st["wrong_pending"], st["wrong_mastered"], st["mastered_rate"], st["stubborn"], st["favorites"]) == (7, 4, 36.4, 2, 4)
    assert st["breakdown"]["MATH"] == {"pending": 6, "mastered": 4, "stubborn": 2, "favorites": 3} and st["breakdown"]["PHYSICS"]["pending"] == 1
    # 科目答题数：数学 55、物理 15、化学 0；占比和正确率按各自算
    assert [(x["code"], x["count"], x["share"], x["accuracy"]) for x in r["subjects"]] == [("MATH", 55, 78.6, 47.3), ("PHYSICS", 15, 21.4, 93.3), ("CHEMISTRY", 0, 0.0, None)]
    # 题型：固定输出 5 种（没做过的是 0），占比按这个学科自己的答题数
    math_t = r["types_by_subject"]["MATH"]
    assert [x["key"] for x in math_t] == ["SINGLE_CHOICE", "MULTIPLE_CHOICE", "TRUE_FALSE", "FILL_BLANK", "APPLICATION"]
    assert [(x["count"], x["accuracy"]) for x in math_t] == [(20, 75.0), (5, 20.0), (0, None), (30, 33.3), (0, None)] and math_t[3]["share"] == 54.5
    assert set(r["types_by_subject"]) == {"MATH", "PHYSICS"}                                   # 没答题的学科不出现
    # 难度：基础 / 进阶 / 挑战固定 3 档
    assert [(x["key"], x["count"]) for x in r["difficulty_by_subject"]["MATH"]] == [("basic", 50), ("advanced", 5), ("challenge", 0)]
    assert [(x["key"], x["count"]) for x in r["difficulty_by_subject"]["PHYSICS"]] == [("basic", 15), ("advanced", 0), ("challenge", 0)]
    # 知识点 Top5：按答题数从多到少，带正确率
    assert [(x["name"], x["count"], x["accuracy"]) for x in r["kp_top"]["MATH"]] == [("角的分类", 25, 40.0), ("余角与补角", 20, 40.0)]
    assert [x["name"] for x in r["kp_top"]["PHYSICS"]] == ["牛顿第二定律"] and "CHEMISTRY" not in r["kp_top"]


def test_answers_build_tips():
    from app.services.profile_service import _answers_build
    subs, cube, wrong, stub, fav, kp = _ans_data()
    tips = _answers_build(cube, subs, 100, wrong, stub, fav, kp)["tips"]
    assert len(tips) <= 5
    assert "还有 7 道错题没攻克（已攻克 4 道，攻克率 36.4%）" in tips[0] and "2 道顽固错题" in tips[1]
    assert all(len(t) <= 48 for t in tips)                              # 页面上一条尽量一行放下（5 条要放进 210px 的卡片）
    assert "数学占 78.6%（55 题）" in tips[2] and "物理 15 题、化学 0 题" in tips[2]
    assert "「数学」正确率 47.3%，比「物理」（93.3%）低 46 个百分点" in tips[3] and "「填空题」正确率仅 33.3%" in tips[4]
    # 没有错题 / 顽固 / 收藏，只有基础题：基础题占比、答题量下降、知识点集中的提醒
    only = [{"sid": 1, "qt": "SINGLE_CHOICE", "df": "basic", "n": 40, "c": 36}]
    t2 = " ".join(_answers_build(only, subs, 100, [], [], [], [{"sid": 1, "kid": 1, "name": "角的分类", "n": 30, "c": 27}])["tips"])
    assert "100% 是基础题，进阶以上仅 0 题" in t2 and "「角的分类」答了 30 题（占 75%）" in t2 and "答题量比前一段（100 题）减少了 60%" in t2
    # 错题全部攻克 / 什么问题都没有：给肯定
    assert "错题已全部攻克（共 3 道）" in _answers_build(only, subs, 0, [{"sid": 1, "k": "aha_achieved", "n": 3}], [], [], [])["tips"][0]
    small = [{"sid": 1, "qt": "SINGLE_CHOICE", "df": "advanced", "n": 10, "c": 9}]                  # 样本小，哪条规则都不触发
    assert _answers_build(small, subs, 0, [], [], [], [])["tips"] == ["答题的覆盖和质量都比较均衡，继续保持"]


def test_answers_build_no_answers_keeps_state_stats():
    """所选范围内没有答题：图表没数据，但错题 / 顽固 / 收藏是当前状态，照样给"""
    from app.services.profile_service import _answers_build
    subs, _, wrong, stub, fav, _ = _ans_data()
    r = _answers_build([], subs, 0, wrong, stub, fav, [])
    assert r["has_data"] is False and r["stats"]["total"] == 0 and r["stats"]["accuracy"] is None
    assert r["stats"]["wrong_pending"] == 7 and r["stats"]["stubborn"] == 2 and r["stats"]["favorites"] == 4
    assert r["types_by_subject"] == {} and r["kp_top"] == {} and [x["count"] for x in r["subjects"]] == [0, 0, 0]


def _acc_data():
    subs = {1: ("MATH", "数学"), 2: ("PHYSICS", "物理"), 3: ("CHEMISTRY", "化学")}
    cube = [{"sid": 1, "qt": "SINGLE_CHOICE", "df": "basic", "n": 20, "c": 15}, {"sid": 1, "qt": "FILL_BLANK", "df": "basic", "n": 30, "c": 10},
            {"sid": 1, "qt": "MULTIPLE_CHOICE", "df": "advanced", "n": 5, "c": 1},
            {"sid": 2, "qt": "SINGLE_CHOICE", "df": "basic", "n": 10, "c": 9}, {"sid": 2, "qt": "TRUE_FALSE", "df": "basic", "n": 5, "c": 5}]
    kp = [{"sid": 1, "kid": 1, "name": "角的分类", "n": 25, "c": 10, "b": 3, "r": 2}, {"sid": 1, "kid": 2, "name": "余角与补角", "n": 20, "c": 18, "b": 0, "r": 0},
          {"sid": 1, "kid": 3, "name": "只做了一次", "n": 1, "c": 0, "b": 0, "r": 0}, {"sid": 2, "kid": 50, "name": "牛顿第二定律", "n": 8, "c": 7, "b": 0, "r": 0}]
    return subs, cube, {"n": 100, "c": 70}, {"wrong": 30, "blank": 8, "rush": 6}, kp, {"practiced": 2, "total": 20, "rate": 10.0}


def test_accuracy_build_stats():
    from app.services.profile_service import _accuracy_build
    subs, cube, prev, causes, kp, sem = _acc_data()
    r = _accuracy_build(cube, subs, prev, causes, kp, sem)
    st = r["stats"]
    assert r["has_data"] and (st["total"], st["correct"], st["wrong"], st["accuracy"], st["prev_accuracy"]) == (70, 40, 30, 57.1, 70.0)
    assert st["prev_correct"] == 70 and _accuracy_build(cube, subs, {"n": 5, "c": 3}, causes, kp, sem)["stats"]["prev_correct"] is None     # 前一段不足 10 题：不做对比
    assert st["causes"] == {"wrong": 30, "blank": 8, "rush": 6, "thoughtful": 16}                      # 认真做仍错 = 30 − 8 − 6
    assert st["semester"] == sem and (st["weak_kps"], st["strong_kps"]) == (1, 2)                      # 只做了 1 次的知识点不算
    assert [(x["code"], x["count"], x["accuracy"]) for x in r["subjects"]] == [("MATH", 55, 47.3), ("PHYSICS", 15, 93.3), ("CHEMISTRY", 0, None)]
    # 题型 / 难度：固定档位，按学科
    assert [(x["key"], x["count"], x["accuracy"]) for x in r["types_by_subject"]["MATH"]][:4] == [("SINGLE_CHOICE", 20, 75.0), ("MULTIPLE_CHOICE", 5, 20.0), ("TRUE_FALSE", 0, None), ("FILL_BLANK", 30, 33.3)]
    assert [(x["key"], x["count"], x["accuracy"]) for x in r["difficulty_by_subject"]["MATH"]] == [("basic", 50, 50.0), ("advanced", 5, 20.0), ("challenge", 0, None)]
    # 薄弱 / 强项知识点：按学科，带错因
    w = r["weak_by_subject"]["MATH"]
    assert [x["name"] for x in w] == ["角的分类"] and (w[0]["error_rate"], w[0]["wrong"], w[0]["blank"], w[0]["rush"], w[0]["thoughtful"]) == (60.0, 15, 3, 2, 10)
    assert [x["name"] for x in r["strong_by_subject"]["MATH"]] == ["余角与补角"] and r["strong_by_subject"]["MATH"][0]["accuracy"] == 90.0
    assert r["weak_by_subject"]["PHYSICS"] == [] and [x["name"] for x in r["strong_by_subject"]["PHYSICS"]] == ["牛顿第二定律"]


def test_accuracy_build_tips():
    from app.services.profile_service import _accuracy_build
    subs, cube, prev, causes, kp, sem = _acc_data()
    tips = _accuracy_build(cube, subs, prev, causes, kp, sem)["tips"]
    assert len(tips) <= 5 and all(len(t) <= 48 for t in tips)
    assert "整体正确率 57.1%，比前一段下降了 12.9 个百分点" in tips[0] and "8 道错题是没作答（占错题 27%）" in tips[1]
    assert "1 个知识点错误率超过 40%，最薄弱是「角的分类」（60%）" in tips[2] and "「数学」正确率 47.3%，比「物理」（93.3%）低 46 个百分点" in tips[3]
    assert "「填空题」正确率仅 33.3%" in tips[4]
    # 没有前一段、秒答多、基础题没做稳、学期只练了很少
    only = [{"sid": 1, "qt": "SINGLE_CHOICE", "df": "basic", "n": 40, "c": 20}]
    t2 = " ".join(_accuracy_build(only, subs, None, {"wrong": 20, "blank": 0, "rush": 12}, [], sem)["tips"])
    assert "整体正确率 50%（共 40 题）" in t2 and "12 道错题是 3 秒内秒答（占 60%）" in t2 and "基础题正确率只有 50%" in t2 and "只练过 2/20 个知识点" in t2
    # 错题多半是认真做了仍错：说明没吃透
    assert "90% 的错题是认真做了仍错" in " ".join(_accuracy_build(only, subs, None, {"wrong": 20, "blank": 1, "rush": 1}, [], None)["tips"])
    # 前一段差不多：不说涨跌；强项会被提到
    t3 = " ".join(_accuracy_build(cube, subs, {"n": 100, "c": 57}, {"wrong": 0, "blank": 0, "rush": 0}, kp[1:2], None)["tips"])
    assert "和前一段差不多" in t3 and "强项是「余角与补角」（正确率 90%）" in t3
    # 没答题：没数据，给一条默认的
    e = _accuracy_build([], subs, None, {"wrong": 0, "blank": 0, "rush": 0}, [], None)
    assert e["has_data"] is False and e["stats"]["accuracy"] is None and e["tips"] == ["正确率整体稳定，继续保持"]


def test_accuracy_build_trend():
    """正确率趋势：按天从旧到新，每个点整体 + 各学科的正确率；样本太少（按天 < 2 题）的点不给正确率"""
    from datetime import date
    from app.services.profile_service import _accuracy_build, Range
    subs, cube, prev, causes, kp, sem = _acc_data()
    rng = Range(date(2026, 11, 9), date(2026, 11, 15))
    # w：0 = 最近一天（11/15）、6 = 最早一天（11/9）
    rows = [{"w": 6, "sid": 1, "n": 10, "c": 5}, {"w": 6, "sid": 2, "n": 4, "c": 4},          # 11/9：数学 5/10，物理 4/4 → 整体 9/14
            {"w": 4, "sid": 1, "n": 1, "c": 1},                                                # 11/11：只答了 1 题
            {"w": 0, "sid": 1, "n": 6, "c": 3}, {"w": 0, "sid": 3, "n": 2, "c": 1}]            # 11/15：数学 3/6，化学 1/2 → 整体 4/8
    t = _accuracy_build(cube, subs, prev, causes, kp, sem, rows, rng)["trend"]
    assert t["unit"] == "day" and [x["label"] for x in t["series"]] == ["11/9", "11/10", "11/11", "11/12", "11/13", "11/14", "11/15"]
    s0, s2, s6 = t["series"][0], t["series"][2], t["series"][6]
    assert (s0["count"], s0["accuracy"]) == (14, 64.3) and s0["by_subject"]["MATH"] == {"count": 10, "accuracy": 50.0} and s0["by_subject"]["PHYSICS"]["accuracy"] == 100.0
    assert s0["by_subject"]["CHEMISTRY"] == {"count": 0, "accuracy": None}                                   # 这天没做化学
    assert (s2["count"], s2["accuracy"], s2["by_subject"]["MATH"]["accuracy"]) == (1, None, None)            # 只有 1 题：不给正确率
    assert (s6["accuracy"], s6["by_subject"]["CHEMISTRY"]) == (50.0, {"count": 2, "accuracy": 50.0})
    assert t["series"][1]["accuracy"] is None and t["series"][1]["count"] == 0                               # 没答题的天
    # 不传 rng：没有趋势（兼容老调用）
    assert _accuracy_build(cube, subs, prev, causes, kp, sem)["trend"] is None


def test_accuracy_build_weak_kp_meta():
    """薄弱知识点带上「走向」和「可能的前置」（来自按全部历史算的知识点统计）；没有就是 None"""
    from app.services.profile_service import _accuracy_build
    subs, cube, prev, causes, kp, sem = _acc_data()
    meta = {1: {"trend": "down", "root_kp": {"id": 9, "name": "线段的比较与运算"}}}
    w = _accuracy_build(cube, subs, prev, causes, kp, sem, None, None, meta)["weak_by_subject"]["MATH"][0]
    assert w["name"] == "角的分类" and w["trend"] == "down" and w["root_kp"] == {"id": 9, "name": "线段的比较与运算"}
    w0 = _accuracy_build(cube, subs, prev, causes, kp, sem)["weak_by_subject"]["MATH"][0]
    assert w0["trend"] is None and w0["root_kp"] is None


def _ai_rows(rng):
    from datetime import timedelta
    base = rng.since + timedelta(hours=20)          # 区间第一天 20:00（晚上）
    def m(sid, role, at, **kw):
        d = {"sid": sid, "role": role, "at": at, "aha": False, "rating": None, "strat": None, "strat_name": None, "ask_ans": False, "mood": False, "summary": None, "started": at}
        d.update(kw)
        return d
    return [
        m("a", "student", base, ask_ans=True), m("a", "assistant", base + timedelta(minutes=1), strat="S1", strat_name="苏格拉底", rating="like", aha=True, summary="学生搞懂了余角"),
        m("a", "student", base + timedelta(minutes=2)),
        m("b", "student", base + timedelta(days=1, hours=-14), mood=True),
        m("old", "student", rng.since - timedelta(days=1)),
    ]


def test_ai_build_counts_and_tips():
    from app.services import profile_service as ps
    rng = ps.Range.last(7)
    r = ps._ai_build(_ai_rows(rng), rng)
    st = r["stats"]
    assert (st["total"], st["sessions"], st["aha"], st["prev_total"]) == (3, 2, 1, 1)
    assert st["avg_ask"] == 1.5 and st["like_rate"] == 100.0 and st["ask_answer"] == 1 and st["mood"] == 1
    assert sum(x["count"] for x in r["periods"]) == 3 and sum(x["count"] for x in r["series"]) == 3
    assert r["strategies"][0]["name"] == "苏格拉底" and r["strategies"][0]["likes"] == 1
    assert any("顿悟" in t for t in r["tips"]) and len(r["tips"]) <= 5


def test_ai_build_empty():
    from app.services import profile_service as ps
    r = ps._ai_build([], ps.Range.last(7))
    assert r["has_data"] is False and r["tips"] == [] and r["stats"]["avg_ask"] is None
