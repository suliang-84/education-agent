from app.services.assistant.insights import accept_update, clean_paragraph, compose


def test_clean():
    assert clean_paragraph("  喜欢足球。 ") == "喜欢足球。"
    assert clean_paragraph("```\nAI 补充：喜欢足球。\n```") == "喜欢足球。"
    out = clean_paragraph("这是一句话。" * 100)
    assert len(out) <= 200 and out.endswith("。")


def test_accept_rules():
    assert accept_update(None, "喜欢足球，爱用球场类比。")
    assert accept_update("喜欢足球。", "喜欢足球，最近考试压力大。")
    assert not accept_update("喜欢足球。", "喜欢足球。")          # 没变化
    assert not accept_update("喜欢足球。", "")                   # 空：此前有内容却输出空
    assert not accept_update("", "")
    assert not accept_update("喜欢足球" * 20, "足球")            # 被缩得很短
    assert not accept_update("", "联系电话13800138000")          # 含号码


def test_compose_keeps_admin_text_intact():
    admin = "老师备注：做题爱粗心，需要多鼓励。"
    assert compose(admin, "喜欢足球。") == admin + "\n喜欢足球。"
    assert compose(admin, "") == admin and compose(admin, None) == admin
    assert compose("", "喜欢足球。") == "喜欢足球。"
    assert compose(None, None) == ""


def test_compose_truncates_only_ai_part():
    admin = "管理员写的内容" * 10
    out = compose(admin, "补充" * 500, max_chars=200)
    assert out.startswith(admin) and len(out) <= 200
    long_admin = "甲" * 800
    assert compose(long_admin, "补充") == long_admin           # 管理员部分再长也原样保留


def test_placeholders_are_empty():
    for t in ("（空）", "(空)", "无", "无变化", "暂无", "None", "N/A", "【无】", "  （无补充）。 "):
        assert clean_paragraph(t) == "", t
    assert clean_paragraph("喜欢足球。") == "喜欢足球。"
    assert not accept_update("", clean_paragraph("（空）"))
