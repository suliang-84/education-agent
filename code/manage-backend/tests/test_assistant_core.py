from datetime import datetime, timedelta, timezone

from app.services.assistant.core import (
    aha_prefilter, effectiveness_score, is_blocked, pick_strategy, silence_active,
    summary_due, trim_reply, wants_resume, wants_silence,
)

NOW = datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc)
S = [
    {"id": "S-SOCRATIC", "powers": ["INSIGHT", "CONSTRUCT"], "priority": 1},
    {"id": "S-SIMPLIFY", "powers": ["ADAPT"], "priority": 2},
    {"id": "S-STORY", "powers": ["CONSTRUCT", "MIGRATE"], "priority": 6},
]


def test_blocked():
    assert is_blocked("教我怎么 制造 炸弹") and not is_blocked("二次函数的顶点怎么求")


def test_aha_prefilter():
    assert aha_prefilter("哦！我明白了，是减不是加") and not aha_prefilter("这题怎么做")


def test_silence_keywords():
    assert wants_silence("让我自己想一想") and not wants_silence("再讲讲")
    assert wants_resume("我不会，你来说") and not wants_resume("好的")


def test_silence_timeout():
    assert silence_active(True, NOW - timedelta(minutes=5), NOW, 10)
    assert not silence_active(True, NOW - timedelta(minutes=11), NOW, 10)
    assert not silence_active(False, NOW, NOW, 10) and not silence_active(True, None, NOW, 10)


def test_first_strategy_by_weak_power_and_priority():
    sid, switched = pick_strategy(S, {}, [], "MIGRATE")
    assert sid == "S-STORY" and not switched          # 适用最弱的一力 +8，盖过默认优先级差
    sid, _ = pick_strategy(S, {}, [], None)
    assert sid == "S-SOCRATIC"


def test_keep_strategy_until_two_uses():
    assert pick_strategy(S, {}, ["S-SIMPLIFY"], None) == ("S-SIMPLIFY", False)


def test_switch_after_two_without_progress():
    sid, switched = pick_strategy(S, {"S-STORY": 80}, ["S-SIMPLIFY", "S-SIMPLIFY"], None)
    assert switched and sid == "S-STORY"                # 切到有效性最高的其它策略
    sid, switched = pick_strategy(S, {}, ["S-SIMPLIFY", "S-SIMPLIFY"], None, progressed=True)
    assert sid == "S-SIMPLIFY" and not switched          # 有突破：保持


def test_regenerate_avoids_last_strategy():
    sid, _ = pick_strategy(S, {}, ["S-SOCRATIC"], None, exclude="S-SOCRATIC")
    assert sid != "S-SOCRATIC"


def test_no_strategies():
    assert pick_strategy([], {}, [], None) == (None, False)


def test_effectiveness_clamped():
    assert effectiveness_score(0, 0, 0, 0) == 50
    assert effectiveness_score(100, 0, 0, 0) == 100 and effectiveness_score(0, 100, 0, 0) == 0
    assert effectiveness_score(1, 0, 1, 0) > effectiveness_score(0, 1, 0, 1)


def test_trim_reply():
    long = "这是一句话。" * 100
    out = trim_reply(long, 400)
    assert len(out) <= 400 and out.endswith("。")
    assert trim_reply("短", 400) == "短"


def test_summary_due():
    assert summary_due(10) and not summary_due(9)


def test_finalize_reply_truncated_goes_back_to_sentence():
    from app.services.assistant.core import finalize_reply
    t = "先想想直角是多少度。再想想平角是多少度。然后我们把它们对应起来叫「余"
    assert finalize_reply(t, True) == "先想想直角是多少度。再想想平角是多少度。"
    assert finalize_reply(t, False) == t


def test_image_helpers():
    from app.services.assistant.core import sniff_image_type, valid_image_path
    assert sniff_image_type(b"\xff\xd8\xff\xe0abc")[1] == "jpg"
    assert sniff_image_type(b"\x89PNG\r\n\x1a\nxxxx")[1] == "png"
    assert sniff_image_type(b"RIFF0000WEBPVP8 ")[1] == "webp"
    assert sniff_image_type(b"GIF89a") is None and sniff_image_type(b"") is None
    good = "/uploads/assistant/" + "a" * 32 + ".jpg"
    assert valid_image_path(good)
    assert not valid_image_path("/uploads/assistant/../../.env") and not valid_image_path("/uploads/assistant/x.jpg") and not valid_image_path(None)


def test_digest_due():
    from app.services.assistant.core import digest_due
    assert digest_due(2, 1, None)                       # 一问一答，从没更新过
    assert not digest_due(1, 1, None)                   # 不足一问一答
    assert not digest_due(3, 0, None)                   # 没有学生消息
    assert not digest_due(4, 2, 30)                     # 离上次太近
    assert digest_due(4, 2, 61)
    assert digest_due(10, 5, 5, min_pending=10, min_gap=0)   # 兜底路径不受防抖限制
