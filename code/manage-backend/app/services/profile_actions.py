"""学生画像的「提分行动」：把画像里的各项发现，翻成管理员 / 老师能直接去做的具体建议。纯函数，不查数据库。

原则：每条建议都带数据依据；样本不够就不说；最多给 5 条，按重要程度排序。
"""
RUSH_SHARE = 40        # 错题里「秒答」占比达到这个值，才提示「答得太快」
MIN_KP_ATTEMPTS = 3    # 知识点至少做过几次才给针对性建议
MIN_BUCKET_ANSWERS = 10  # 学习时段正确率对比：每个时段至少答题数
BUCKET_GAP_PP = 15       # 最好和最差时段的正确率差距（百分点）


def kp_trend(flags: list[bool]) -> str | None:
    """知识点上正确率的走向：按时间顺序（旧 → 新）把答题分成前后两半比较；做得太少返回 None"""
    n = len(flags)
    if n < 6:
        return None
    half = n // 2
    first = sum(flags[:half]) / half
    second = sum(flags[half:]) / (n - half)
    diff = second - first
    return "up" if diff >= 0.15 else "down" if diff <= -0.15 else "flat"


def kp_advice(att: int, errors: int, blank: int, rush: int, trend: str | None) -> str | None:
    """针对一个薄弱知识点给建议：先看错因构成，再看反复练有没有进步"""
    if att < MIN_KP_ATTEMPTS or errors == 0:
        return None
    thoughtful = errors - blank - rush
    if blank / errors >= 0.5:
        return f"{round(blank / errors * 100)}% 的错题是没作答就提交，先让学生愿意动笔（比如只写第一步），再谈知识"
    if rush / errors * 100 >= RUSH_SHARE:
        return f"{round(rush / errors * 100)}% 的错题是秒答，提醒先读完题再作答，做完检查一遍"
    if thoughtful / errors >= 0.5:
        if trend in ("down", "flat"):
            return "认真做了仍然错、反复练也没有进步：不要再刷题，先安排讲解（智能解答 / AI 助教），再回来练"
        if trend == "up":
            return "认真做了仍然错，但正在进步：继续做这个知识点的训练巩固"
        return "认真做了仍然错，有真正的知识缺口：先安排讲解（智能解答 / AI 助教），再做知识点训练"
    return None


def build_actions(ctx: dict) -> list[str]:
    """ctx：mastery / diagnosis / behavior / retention / cognitive / status / wrong_pending 等画像数据；返回最多 5 条建议"""
    items: list[tuple[int, str]] = []
    blank_given = False
    d = ctx["diagnosis"]
    status = ctx["status"]

    if not ctx["cognitive"].get("has_profile"):
        items.append((1, "尚未完成五力测试，先完成测试才能生成能力画像"))

    if status == "近期懈怠":
        items.append((1, "近期训练明显减少，建议先联系学生了解情况，用较轻松的训练方式恢复节奏"))

    if d["answered"] >= 20 and (d["blank_rate"] or 0) >= 40:
        worst = max((r for r in d["blank_by_type"] if r["answered"] >= 5), key=lambda r: r["rate"] or 0, default=None)
        where = f"，其中{worst['label']}最严重（{worst['rate']}%）" if worst and (worst["rate"] or 0) >= 60 else ""
        blank_given = True
        items.append((1, f"{d['blank_rate']}% 的题没作答就提交了{where}：先解决「愿意动笔」，再谈知识；可以要求这类题至少写出第一步"))

    for k in ctx["mastery"]["weak_kps"][:3]:
        if k.get("advice") and not (blank_given and "没作答就提交" in k["advice"]):   # 总体已经提示过「不动笔」，知识点上不再重复
            items.append((2, f"「{k['name']}」（错误率 {k['error_rate']}%）：{k['advice']}"))

    rep = d["repeat"]
    if rep["questions"] >= 5 and rep["gain"] is not None and rep["gain"] <= 0:
        items.append((2, "同一道题反复做，正确率没有提高：把「再做一遍」换成「先看讲解再做」"))

    ret = ctx["retention"]
    if ret and ret["answered"] >= 5 and ret["accuracy"] is not None and ret["accuracy"] < 60:
        items.append((2, f"已攻克的错题再次遇到时只有 {ret['accuracy']}% 做对，说明没有真正掌握，建议隔几天后再复习一遍"))

    buckets = [b for b in ctx["behavior"].get("time_buckets", []) if b["count"] >= MIN_BUCKET_ANSWERS and b.get("accuracy") is not None]
    if len(buckets) >= 2:
        best = max(buckets, key=lambda b: b["accuracy"])
        worst = min(buckets, key=lambda b: b["accuracy"])
        if best["accuracy"] - worst["accuracy"] >= BUCKET_GAP_PP:
            items.append((3, f"{best['label']}做题正确率 {best['accuracy']}%，{worst['label']}只有 {worst['accuracy']}%，建议把重点训练放在{best['label']}"))

    for t in d.get("type_time", []):
        if t["right_n"] >= 5 and t["wrong_n"] >= 5 and t["avg_wrong"] is not None and t["avg_right"]:
            if t["avg_wrong"] < t["avg_right"] * 0.6:
                items.append((3, f"{t['label']}答错的比答对的快得多（{t['avg_wrong']} 秒 vs {t['avg_right']} 秒），可能没读清题就作答"))
                break

    if ctx["wrong_pending"] > 0:
        items.append((3, f"错题集还有 {ctx['wrong_pending']} 道待攻克，建议安排一次错题集训练"))

    weak = ctx["cognitive"].get("primary_weakness_label")
    if weak:
        items.append((4, f"五力里{weak}偏弱，多做考查该能力的题目"))

    items.sort(key=lambda x: x[0])
    return [t for _, t in items[:5]]
