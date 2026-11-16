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
    assert [m["key"] for m in r["metrics"]] == ["idle", "sessions", "accuracy", "answered"]
    assert r["metrics"][0]["value"] == "9 天" and r["metrics"][2]["hint"] == "较前 30 天-20.0pp"
    assert len(r["drivers"]) <= 4 and all(d["tone"] == "warn" for d in r["drivers"])
    assert "9 天没有训练" in r["drivers"][0]["text"]
    # 样本不足时不做对比、不下错因结论
    r = _status_detail("状态平稳", {"streak_days": 0}, {}, {}, {"wrong": 3, "causes": []}, {}, {"n": 5, "acc": 80, "n_prev": 2, "acc_prev": 10}, 0, 0, 0, None)
    assert r["metrics"][2]["hint"] is None and r["drivers"] == []


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
    assert r["status_detail"]["metrics"][1]["label"] == "近 7 天训练" and r["status_detail"]["metrics"][3]["label"] == "近 7 天答题"
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
    r = Range.build(None, None)                      # 默认近 7 天，含今天
    assert r.days == 7 and r.end == today_bj() and r.is_recent and r.label == "近 7 天" and r.daily
    assert (r.freq_full, r.review_full, r.min_answered, r.points) == (3, 1, 8, 7)
    r = Range.last(30)
    assert (r.freq_full, r.review_full, r.min_answered, r.points, r.cmp_len, r.daily) == (12, 4, 20, 5, 15, False)
    # 过去的范围：按所选范围统计，起止都含当天（北京时间 0 点到次日 0 点）
    past = Range.build(str(today_bj() - timedelta(days=20)), str(today_bj() - timedelta(days=11)))
    assert past.days == 10 and not past.is_recent and past.label == "所选 10 天" and past.until - past.since == timedelta(days=10)
    for bad in [("x", None), (None, str(today_bj() + timedelta(days=1))), (str(today_bj()), str(today_bj() - timedelta(days=1))),
                (str(today_bj() - timedelta(days=90)), None)]:
        with pytest.raises(AppException):
            Range.build(*bad)
    assert Range.build(str(today_bj() - timedelta(days=89)), None).days == 90
