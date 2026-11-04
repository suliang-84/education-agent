from app.services.assistant.insights import accept_update, clean_paragraph


def test_clean_plain():
    assert clean_paragraph("  喜欢足球，常用球场做类比。 ") == "喜欢足球，常用球场做类比。"


def test_clean_strips_fence_label_quotes():
    assert clean_paragraph("```\n个人洞察：喜欢足球。\n```") == "喜欢足球。"
    assert clean_paragraph("“喜欢足球。”") == "喜欢足球。"


def test_clean_truncates_at_sentence():
    t = "这是一句话。" * 100
    out = clean_paragraph(t, 400)
    assert len(out) <= 400 and out.endswith("。")


def test_accept_rules():
    assert accept_update(None, "喜欢足球，爱用球场类比。")
    assert accept_update("喜欢足球。", "喜欢足球，最近考试压力大。")
    assert not accept_update("喜欢足球。", "喜欢足球。")                 # 没变化
    assert not accept_update("喜欢足球。", "")                          # 空
    assert not accept_update("喜欢足球" * 20, "足球")                   # 已有较长内容被缩得很短：疑似丢信息
    assert not accept_update("", "联系电话13800138000")                 # 含号码
