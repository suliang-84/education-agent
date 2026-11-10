"""学生画像（管理员视图）：把训练、五力、错题、AI 互动等已有数据汇总成一份画像。

一期只用现有表，不依赖日汇总表：直接按单个学生查询。设计见 docs/4.架构设计/09_学生画像设计方案.md。
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.services.smart_training.core import DEFAULT_PARAMS, smoothed_error

TZ = "Asia/Shanghai"
POWERS = ["INSIGHT", "CONSTRUCT", "DEDUCE", "ADAPT", "MIGRATE"]
POWER_LABELS = {"INSIGHT": "洞察力", "CONSTRUCT": "建构力", "DEDUCE": "推演力", "ADAPT": "调适力", "MIGRATE": "迁移力"}
TYPE_LABELS = {"SINGLE_CHOICE": "单选题", "MULTIPLE_CHOICE": "多选题", "TRUE_FALSE": "判断题",
               "FILL_BLANK": "填空题", "APPLICATION": "应用题"}
DIFF_LABELS = {"basic": "基础", "advanced": "进阶", "challenge": "挑战"}
DIM_LABELS = {"KNOWLEDGE_POINT": "按知识点", "UNIT": "按单元", "RANDOM": "随机", "ERROR_QUESTIONS": "错题集",
              "FAVORITES": "收藏夹", "SMART": "智能训练", "SEMESTER": "按学期"}
TIME_BUCKETS = [("morning", "上午", 6, 12), ("afternoon", "下午", 12, 18), ("evening", "晚上", 18, 22), ("night", "深夜", 22, 30)]

# 学习投入度权重（训练频次 / 连续天数 / 答题完成度 / 认真作答）
# 「认真作答」至少要有这么多道带用时的答题才有意义，不够时这一项不计入，其余三项按比例折算
MIN_CAREFUL_SAMPLES = 20
RUSH_SECONDS = 3   # 非空作答、用时不超过这个秒数的错题，视为「秒答」（可能没读题或乱选）

# 学习投入度权重默认值见 profile_config.DEFAULT_WEIGHTS（可在配置管理里修改）

_BASE = """
FROM training_answer_records a
JOIN training_sessions s ON s.id = a.session_id
JOIN questions q ON q.id = a.question_id
WHERE s.student_id = :sid AND COALESCE(a.is_seed_data, false) = false
"""


def _r(v, n=1):
    return None if v is None else round(float(v), n)


def _pct(num, den):
    return None if not den else round(num / den * 100, 1)


async def _rows(db: AsyncSession, sql: str, **p):
    return (await db.execute(text(sql), p)).mappings().all()


async def _one(db: AsyncSession, sql: str, **p):
    return (await db.execute(text(sql), p)).mappings().first()


# ── 各维度 ────────────────────────────────────────────────────

async def _basic(db, sid):
    s = await _one(db, "SELECT id, nickname, avatar_url, grade, semester, is_minor, created_at, last_login_at FROM students WHERE id=:sid AND deleted_at IS NULL", sid=sid)
    if not s:
        raise AppException("学生不存在", 404)
    parents = await _rows(db, """
        SELECT p.id, p.nickname, b.confirmed_at FROM parent_student_bindings b
        JOIN students p ON p.id = b.parent_id
        WHERE b.student_id=:sid AND b.bind_status='active' AND b.deleted_at IS NULL ORDER BY b.created_at""", sid=sid)
    active = await _one(db, f"""
        SELECT count(DISTINCT (a.answered_at AT TIME ZONE '{TZ}')::date) d {_BASE}
        AND a.answered_at >= now() - interval '30 days'""", sid=sid)
    return {
        "id": s["id"], "nickname": s["nickname"], "avatar_url": s["avatar_url"], "grade": s["grade"],
        "semester": s["semester"], "is_minor": s["is_minor"], "created_at": s["created_at"],
        "last_login_at": s["last_login_at"], "active_days_30": active["d"] if active else 0,
        "parents": [dict(p) for p in parents],
    }


async def _cognitive(db, sid):
    rows = await _rows(db, "SELECT * FROM five_power_profiles WHERE student_id=:sid ORDER BY created_at", sid=sid)
    if not rows:
        return {"has_profile": False}
    latest = next((r for r in reversed(rows) if r["is_latest"]), rows[-1])

    def trio(key):
        return {p: latest[f"{p.lower()}_{key}"] for p in POWERS}

    final = trio("final")
    ability, pref = trio("ability"), trio("preference")
    tags = []
    tp = await _one(db, "SELECT * FROM five_power_training_profiles WHERE student_id=:sid", sid=sid)
    training = None
    if tp:
        training = {p: tp[f"{p.lower()}_ability"] for p in POWERS}
        for p in POWERS:
            t, f = training.get(p), final.get(p)
            if t is not None and f is not None and f - t >= 15:
                tags.append(f"{POWER_LABELS[p]}：训练表现低于测试（发挥不稳定）")
    return {
        "has_profile": True,
        "tested_at": latest["created_at"],
        "final": final, "ability": ability, "preference": pref, "training": training,
        "training_info": {"total_training_count": tp["total_training_count"], "total_question_count": tp["total_question_count"],
                          "last_trained_at": tp["last_trained_at"]} if tp else None,
        "primary_strength": latest["primary_strength"], "primary_weakness": latest["primary_weakness"],
        "secondary_weakness": latest["secondary_weakness"], "preferred_force": latest["preferred_force"],
        "recommended_mode": latest["recommended_mode"],
        "confidence": _r(latest["profile_confidence"], 2),
        "tags": tags,
    }


async def _kp_stats(db, sid):
    """知识点掌握：按答题记录现算（student_kp_stats 表目前没有被维护）。
    每个知识点同时统计错因构成（没作答 / 秒答 / 认真做了仍错）和前后半段的走向，用来给针对性建议。"""
    from app.services import profile_actions as pa

    rows = await _rows(db, f"""
        SELECT kp.id, kp.name, kp.chapter_id, kp.sort_order AS kso, ch.sort_order AS cso, ch.name AS chapter, a.is_correct, a.answered_at, a.time_spent_sec t,
               (coalesce(btrim(a.student_answer), '') = '') AS blank
        FROM training_answer_records a
        JOIN training_sessions s ON s.id = a.session_id
        JOIN questions q ON q.id = a.question_id
        CROSS JOIN LATERAL jsonb_array_elements_text(q.knowledge_point_ids) AS t(kid)
        JOIN knowledge_points kp ON kp.id = (CASE WHEN t.kid ~ '^[0-9]+$' THEN t.kid::bigint END)
        LEFT JOIN chapters ch ON ch.id = kp.chapter_id
        WHERE s.student_id=:sid AND COALESCE(a.is_seed_data,false)=false
        ORDER BY kp.id, a.answered_at""", sid=sid)
    by: dict[int, dict] = {}
    for r in rows:
        e = by.setdefault(r["id"], {"id": r["id"], "name": r["name"], "chapter": r["chapter"], "chapter_id": r["chapter_id"], "order": (r["cso"] or 0, r["kso"] or 0, r["id"]),   # 排序字段目前大多是 0，用 id（录入顺序≈教材顺序）兜底
                                    "flags": [], "blank": 0, "rush": 0, "last_at": None})
        e["flags"].append(bool(r["is_correct"]))
        if not r["is_correct"]:
            if r["blank"]:
                e["blank"] += 1
            elif r["t"] is not None and r["t"] <= RUSH_SECONDS:
                e["rush"] += 1
        e["last_at"] = r["answered_at"]
    prior = DEFAULT_PARAMS["prior"]
    out = []
    for e in by.values():
        att = len(e["flags"])
        err = att - sum(e["flags"])
        trend = pa.kp_trend(e["flags"])
        out.append({"id": e["id"], "name": e["name"], "chapter": e["chapter"], "chapter_id": e["chapter_id"], "order": e["order"], "attempts": att, "errors": err,
                    "error_rate": _pct(err, att), "weak_score": round(smoothed_error(att, err, prior), 3), "last_at": e["last_at"],
                    "blank_errors": e["blank"], "rush_errors": e["rush"], "thoughtful_errors": err - e["blank"] - e["rush"],
                    "trend": trend, "advice": pa.kp_advice(att, err, e["blank"], e["rush"], trend)})
    return out


from app.services.profile_actions import find_prerequisites as pa_find_prerequisites  # noqa: E402


async def _mastery(db, sid, grade, semester):
    tot = await _one(db, f"SELECT count(*) n, count(*) FILTER (WHERE a.is_correct) c {_BASE}", sid=sid)
    by_type = await _rows(db, f"SELECT q.question_type k, count(*) n, count(*) FILTER (WHERE a.is_correct) c {_BASE} GROUP BY 1", sid=sid)
    by_diff = await _rows(db, f"SELECT q.difficulty k, count(*) n, count(*) FILTER (WHERE a.is_correct) c {_BASE} GROUP BY 1", sid=sid)
    subj = await _rows(db, f"""
        SELECT sb.name k, count(*) n, count(*) FILTER (WHERE a.is_correct) c
        FROM training_answer_records a JOIN training_sessions s ON s.id=a.session_id
        JOIN questions q ON q.id=a.question_id JOIN subjects sb ON sb.id=q.subject_id
        WHERE s.student_id=:sid AND COALESCE(a.is_seed_data,false)=false GROUP BY 1""", sid=sid)
    wrong = await _rows(db, "SELECT review_status k, count(*) n FROM wrong_answer_records WHERE student_id=:sid GROUP BY 1", sid=sid)
    w = {r["k"]: r["n"] for r in wrong}
    stubborn = await _one(db, f"""
        SELECT count(*) n FROM (SELECT a.question_id {_BASE} AND NOT a.is_correct GROUP BY 1 HAVING count(*) >= 3) t""", sid=sid)
    fav = await _one(db, "SELECT count(*) n FROM question_favorites WHERE student_id=:sid", sid=sid)

    kps = await _kp_stats(db, sid)
    valid = [k for k in kps if k["attempts"] >= 2]
    # 薄弱：错误率 ≥ 40% 里最差的；强项：错误率 ≤ 40% 里最好的。整体都做得不好时，强项为空，而不是把「相对没那么差」的当强项
    roots = pa_find_prerequisites(kps)
    for k in kps:
        k["root_kp"] = roots.get(k["id"])
    weak = sorted([k for k in valid if (k["error_rate"] or 0) >= 40], key=lambda k: -k["weak_score"])[:5]
    strong = sorted([k for k in valid if (k["error_rate"] or 0) <= 40], key=lambda k: k["weak_score"])[:5]

    # 当前学期进度：练过的知识点 / 当前学期知识点总数
    prog = await _one(db, """
        SELECT count(DISTINCT kp.id) total FROM knowledge_points kp
        JOIN chapters ch ON ch.id = kp.chapter_id JOIN semesters se ON se.id = ch.semester_id
        JOIN grades g ON g.id = se.grade_id
        WHERE g.code=:g AND se.code=:s""", g=grade, s=semester) if grade and semester else None
    sem_total = prog["total"] if prog else 0
    practiced = 0
    if sem_total:
        r = await _one(db, f"""
            SELECT count(DISTINCT t.kid) n FROM training_answer_records a
            JOIN training_sessions s ON s.id=a.session_id JOIN questions q ON q.id=a.question_id
            CROSS JOIN LATERAL jsonb_array_elements_text(q.knowledge_point_ids) AS t(kid)
            JOIN knowledge_points kp ON kp.id = (CASE WHEN t.kid ~ '^[0-9]+$' THEN t.kid::bigint END) JOIN chapters ch ON ch.id=kp.chapter_id
            JOIN semesters se ON se.id=ch.semester_id JOIN grades g ON g.id=se.grade_id
            WHERE s.student_id=:sid AND g.code=:g AND se.code=:sm""", sid=sid, g=grade, sm=semester)
        practiced = r["n"] if r else 0

    def rate(rows, labels):
        return [{"key": r["k"], "label": labels.get(r["k"], r["k"]), "answered": r["n"], "accuracy": _pct(r["c"], r["n"])}
                for r in rows if r["k"]]
    return {
        "answered": tot["n"], "correct": tot["c"], "accuracy": _pct(tot["c"], tot["n"]),
        "by_subject": rate(subj, {}),
        "by_type": sorted(rate(by_type, TYPE_LABELS), key=lambda x: list(TYPE_LABELS).index(x["key"]) if x["key"] in TYPE_LABELS else 9),
        "by_difficulty": sorted(rate(by_diff, DIFF_LABELS), key=lambda x: list(DIFF_LABELS).index(x["key"]) if x["key"] in DIFF_LABELS else 9),
        "weak_kps": [{k: v for k, v in x.items() if k != "order"} for x in weak],
        "strong_kps": [{k: v for k, v in x.items() if k != "order"} for x in strong], "kp_total_practiced": len(kps),
        "wrong_pending": w.get("unreview", 0), "wrong_mastered": w.get("aha_achieved", 0),
        "wrong_mastered_rate": _pct(w.get("aha_achieved", 0), sum(w.values())),
        "stubborn_questions": stubborn["n"], "favorites": fav["n"],
        "semester_progress": {"practiced": practiced, "total": sem_total, "rate": _pct(practiced, sem_total)},
    }


async def _behavior(db, sid):
    now = datetime.now(timezone.utc)
    sess = await _rows(db, "SELECT started_at, session_status, is_early_end, training_dimension, total_questions FROM training_sessions WHERE student_id=:sid", sid=sid)
    s7 = sum(1 for s in sess if s["started_at"] >= now - timedelta(days=7))
    s30 = sum(1 for s in sess if s["started_at"] >= now - timedelta(days=30))
    finished = [s for s in sess if s["session_status"] in ("completed", "abandoned")]
    completed = sum(1 for s in finished if s["session_status"] == "completed")
    issued = sum(int(s["total_questions"] or 0) for s in sess)
    ans_cnt = await _one(db, f"SELECT count(*) n {_BASE}", sid=sid)
    dims: dict[str, int] = {}
    for s in sess:
        dims[s["training_dimension"]] = dims.get(s["training_dimension"], 0) + 1

    days = await _rows(db, f"SELECT DISTINCT (a.answered_at AT TIME ZONE '{TZ}')::date d {_BASE} ORDER BY 1 DESC", sid=sid)
    dayset = [r["d"] for r in days]
    streak = 0
    if dayset:
        today = datetime.now(timezone(timedelta(hours=8))).date()
        cur = dayset[0] if (today - dayset[0]).days <= 1 else None
        while cur and cur in dayset:
            streak += 1
            cur -= timedelta(days=1)
    last_day = dayset[0] if dayset else None

    hours = await _rows(db, f"SELECT extract(hour FROM a.answered_at AT TIME ZONE '{TZ}')::int h, count(*) n, count(*) FILTER (WHERE a.is_correct) c {_BASE} GROUP BY 1", sid=sid)
    total_h = sum(r["n"] for r in hours) or 0
    buckets = []
    for key, label, lo, hi in TIME_BUCKETS:
        rs = [r for r in hours if lo <= (r["h"] if r["h"] >= 6 else r["h"] + 24) < hi]
        n, c = sum(r["n"] for r in rs), sum(r["c"] for r in rs)
        buckets.append({"key": key, "label": label, "count": n, "ratio": _pct(n, total_h), "accuracy": _pct(c, n)})

    t = await _one(db, f"""
        SELECT avg(a.time_spent_sec) avg_t, percentile_cont(0.33) WITHIN GROUP (ORDER BY a.time_spent_sec) p33,
               count(*) n {_BASE} AND a.time_spent_sec IS NOT NULL""", sid=sid)
    fw = None
    if t and t["n"] and t["p33"] is not None:
        r = await _one(db, f"""
            SELECT count(*) FILTER (WHERE a.time_spent_sec <= :p AND NOT a.is_correct) fw, count(*) n {_BASE}
            AND a.time_spent_sec IS NOT NULL""", sid=sid, p=t["p33"])
        fw = _pct(r["fw"], r["n"])
    per_sess = await _one(db, f"""
        SELECT avg(x.tot) v FROM (SELECT sum(a.time_spent_sec) tot {_BASE} GROUP BY a.session_id) x""", sid=sid)
    return {
        "sessions_7d": s7, "sessions_30d": s30, "sessions_total": len(sess), "streak_days": streak,
        "last_active_date": str(last_day) if last_day else None,
        "time_buckets": buckets,
        "avg_seconds_per_question": _r(t["avg_t"]) if t else None,
        "avg_seconds_per_session": _r(per_sess["v"]) if per_sess else None,
        "fast_wrong_ratio": fw, "fast_wrong_samples": t["n"] if t else 0,
        # 退出训练不保存（视为放弃）是正常流程，所以不用「完成的训练 / 全部训练」；用「作答题数 / 发放题数」衡量答题完成度
        "completed_sessions": completed, "finished_sessions": len(finished),
        "issued_questions": issued, "answered_questions": ans_cnt["n"],
        "complete_rate": min(100.0, _pct(ans_cnt["n"], issued)) if issued else None,
        "dimensions": sorted([{"key": k, "label": DIM_LABELS.get(k, k), "count": v} for k, v in dims.items()], key=lambda x: -x["count"]),
        "_sessions": sess,
    }


async def _power_trend(db, sid):
    """五力训练趋势：最近 8 周每周各力的做题正确率（该周该力答题少于 3 道的点不画）"""
    rows = await _rows(db, f"""
        SELECT floor(extract(epoch FROM (now() - a.answered_at)) / 604800)::int w, a.power_type p,
               count(*) n, count(*) FILTER (WHERE a.is_correct) c
        {_BASE} AND a.answered_at >= now() - interval '56 days' AND a.power_type IS NOT NULL GROUP BY 1, 2""", sid=sid)
    by = {(r["w"], r["p"]): r for r in rows}
    weeks = []
    for w in range(7, -1, -1):
        item = {"weeks_ago": w, "label": "本周" if w == 0 else f"{w}周前", "powers": {}}
        for p in POWERS:
            r = by.get((w, p))
            item["powers"][p] = {"answered": r["n"] if r else 0, "accuracy": _pct(r["c"], r["n"]) if r and r["n"] >= 3 else None}
        weeks.append(item)
    total = sum(r["n"] for r in rows)
    return {"weeks": weeks, "answered": total, "has_data": any(v["accuracy"] is not None for w in weeks for v in w["powers"].values())}


async def _diagnosis(db, sid):
    """答题诊断：跳题（未作答就提交）、错因构成、同一道题反复做是否有进步"""
    blank_sql = "coalesce(btrim(a.student_answer), '') = ''"
    tot = await _one(db, f"SELECT count(*) n, count(*) FILTER (WHERE {blank_sql}) blank {_BASE}", sid=sid)
    by_type = await _rows(db, f"SELECT q.question_type k, count(*) n, count(*) FILTER (WHERE {blank_sql}) blank {_BASE} GROUP BY 1", sid=sid)
    wrong = await _one(db, f"""
        SELECT count(*) n, count(*) FILTER (WHERE {blank_sql}) blank,
               count(*) FILTER (WHERE NOT ({blank_sql}) AND a.time_spent_sec <= :rush) rush {_BASE} AND NOT a.is_correct""", sid=sid, rush=RUSH_SECONDS)
    att = await _rows(db, f"""
        SELECT least(x.att, 3) k, count(*) n, count(*) FILTER (WHERE x.is_correct) c FROM (
            SELECT a.is_correct, row_number() OVER (PARTITION BY a.question_id ORDER BY a.answered_at) att,
                   count(*) OVER (PARTITION BY a.question_id) tot {_BASE}) x
        WHERE x.tot >= 2 GROUP BY 1 ORDER BY 1""", sid=sid)
    rep = await _one(db, f"""SELECT count(*) q FROM (SELECT a.question_id {_BASE} GROUP BY 1 HAVING count(*) >= 2) t""", sid=sid)
    tt = await _rows(db, f"""
        SELECT q.question_type k, count(*) FILTER (WHERE a.is_correct) rn, count(*) FILTER (WHERE NOT a.is_correct AND NOT ({blank_sql})) wn,
               avg(a.time_spent_sec) FILTER (WHERE a.is_correct) ar, avg(a.time_spent_sec) FILTER (WHERE NOT a.is_correct AND NOT ({blank_sql})) aw
        {_BASE} GROUP BY 1""", sid=sid)
    ret = await _one(db, """
        SELECT count(*) n, count(*) FILTER (WHERE a.is_correct) c FROM training_answer_records a
        JOIN training_sessions s ON s.id = a.session_id
        JOIN wrong_answer_records w ON w.student_id = s.student_id AND w.question_id = a.question_id AND w.aha_at IS NOT NULL AND a.answered_at > w.aha_at
        WHERE s.student_id = :sid AND COALESCE(a.is_seed_data, false) = false""", sid=sid)
    w = wrong["n"] or 0
    causes = []
    if w:
        thoughtful = w - wrong["blank"] - wrong["rush"]
        causes = [
            {"key": "blank", "label": "没作答就提交", "count": wrong["blank"], "ratio": _pct(wrong["blank"], w)},
            {"key": "rush", "label": f"{RUSH_SECONDS} 秒内答完就错", "count": wrong["rush"], "ratio": _pct(wrong["rush"], w)},
            {"key": "thoughtful", "label": "认真做了仍然错", "count": thoughtful, "ratio": _pct(thoughtful, w)},
        ]
    attempts = [{"attempt": r["k"], "label": "第 1 次" if r["k"] == 1 else "第 2 次" if r["k"] == 2 else "第 3 次及以后",
                 "answered": r["n"], "accuracy": _pct(r["c"], r["n"])} for r in att]
    gain = None
    if len(attempts) >= 2 and attempts[0]["accuracy"] is not None:
        later_n = sum(a["answered"] for a in attempts[1:])
        later_c = sum(round((a["accuracy"] or 0) * a["answered"] / 100) for a in attempts[1:])
        gain = round(_pct(later_c, later_n) - attempts[0]["accuracy"], 1) if later_n else None
    return {
        "answered": tot["n"], "blank": tot["blank"], "blank_rate": _pct(tot["blank"], tot["n"]),
        "blank_by_type": sorted([{"key": r["k"], "label": TYPE_LABELS.get(r["k"], r["k"]), "answered": r["n"], "blank": r["blank"],
                                  "rate": _pct(r["blank"], r["n"])} for r in by_type if r["k"]],
                                key=lambda x: list(TYPE_LABELS).index(x["key"]) if x["key"] in TYPE_LABELS else 9),
        "wrong": w, "causes": causes,
        "repeat": {"questions": rep["q"], "attempts": attempts, "gain": gain},
        # 已攻克的错题之后再遇到时做对的比例：衡量是不是真的掌握了
        "retention": {"answered": ret["n"], "accuracy": _pct(ret["c"], ret["n"])},
        # 各题型答对 / 答错（非空答）的平均用时：答错明显比答对快，多半是没读清题
        "type_time": [{"key": r["k"], "label": TYPE_LABELS.get(r["k"], r["k"]), "right_n": r["rn"], "wrong_n": r["wn"],
                       "avg_right": _r(r["ar"]), "avg_wrong": _r(r["aw"])} for r in tt if r["k"]],
    }


MIN_HALF_ANSWERS = 10     # 疲劳对比：前后半段各至少答题数
FATIGUE_DROP_PP = 10      # 后半段比前半段正确率低这么多，算明显下滑
BLANK_RISE_PP = 15        # 后半段空答率比前半段高这么多，算更容易跳题
MIN_AFTER_EXPLAIN = 5     # 看过讲解后再做的题至少这么多道才评价讲解效果
MISCONCEPTION_MIN = 3     # 同一道题至少答错几次才看是不是总选同一个错误答案
MISCONCEPTION_SHARE = 0.7  # 其中同一个错误答案的占比
BIAS_MIN_ANSWERS = 10     # 选项倾向：至少答了几道才判断
BIAS_SHARE = 0.6          # 单选 / 判断题里同一个答案占比达到这个值，算有倾向


async def _insights(db, sid):
    """更深入的挖掘：题序疲劳、看过智能解答后的效果、反复选同一个错误答案（概念性误解）、选项倾向"""
    blank_sql = "coalesce(btrim(a.student_answer), '') = ''"
    out: dict = {}

    # ① 题序疲劳：同一次训练里，前半段 vs 后半段
    r = await _rows(db, f"""
        SELECT (a.question_index * 2 >= s.total_questions) AS late, count(*) n, count(*) FILTER (WHERE a.is_correct) c,
               count(*) FILTER (WHERE {blank_sql}) b {_BASE} AND s.total_questions >= 4 GROUP BY 1""", sid=sid)
    half = {bool(x["late"]): x for x in r}
    fat: dict = {"early": None, "late": None, "verdict": None}
    for key, flag in (("early", False), ("late", True)):
        x = half.get(flag)
        if x:
            fat[key] = {"answered": x["n"], "accuracy": _pct(x["c"], x["n"]), "blank_rate": _pct(x["b"], x["n"])}
    e, l = fat["early"], fat["late"]
    if e and l and e["answered"] >= MIN_HALF_ANSWERS and l["answered"] >= MIN_HALF_ANSWERS:
        if e["accuracy"] - l["accuracy"] >= FATIGUE_DROP_PP:
            fat["verdict"] = f"每次训练后半段正确率（{l['accuracy']}%）比前半段（{e['accuracy']}%）低，容易疲劳或失去耐心，建议每次少抽几道题，或中途休息"
        elif l["blank_rate"] - e["blank_rate"] >= BLANK_RISE_PP:
            fat["verdict"] = f"每次训练后半段更容易没作答就提交（{l['blank_rate']}%，前半段 {e['blank_rate']}%），建议每次少抽几道题"
    out["fatigue"] = fat

    # ② 看过智能解答之后再做同一道题：正确率有没有提高
    r = await _one(db, f"""
        WITH t AS (
            SELECT a.question_id, min(a.answered_at) FILTER (WHERE coalesce(a.rag_content, '') <> '') AS seen_at {_BASE} GROUP BY a.question_id)
        SELECT count(*) FILTER (WHERE a.answered_at <= t.seen_at) bn, count(*) FILTER (WHERE a.answered_at <= t.seen_at AND a.is_correct) bc,
               count(*) FILTER (WHERE a.answered_at > t.seen_at) an, count(*) FILTER (WHERE a.answered_at > t.seen_at AND a.is_correct) ac,
               count(DISTINCT t.question_id) qs
        FROM training_answer_records a JOIN training_sessions s ON s.id = a.session_id JOIN t ON t.question_id = a.question_id
        WHERE s.student_id = :sid AND COALESCE(a.is_seed_data, false) = false AND t.seen_at IS NOT NULL""", sid=sid)
    ex = {"questions": r["qs"], "before": {"answered": r["bn"], "accuracy": _pct(r["bc"], r["bn"])},
          "after": {"answered": r["an"], "accuracy": _pct(r["ac"], r["an"])}, "verdict": None}
    if r["an"] >= MIN_AFTER_EXPLAIN and ex["before"]["accuracy"] is not None:
        gain = round(ex["after"]["accuracy"] - ex["before"]["accuracy"], 1)
        ex["verdict"] = (f"看过智能解答后再做同一道题，正确率从 {ex['before']['accuracy']}% 提高到 {ex['after']['accuracy']}%，讲解对这个学生有帮助，遇到不会的题建议先看解答"
                         if gain >= 10 else
                         f"看过智能解答后再做同一道题，正确率没有明显提高（{ex['before']['accuracy']}% → {ex['after']['accuracy']}%），建议配合 AI 助教一步步引导，而不只是看解答")
    out["explanation"] = ex

    # ③ 同一道选择 / 判断题总选同一个错误答案 → 概念性误解
    rows = await _rows(db, f"""
        SELECT a.question_id, kp.name AS kp, a.student_answer ans, count(*) n
        FROM training_answer_records a JOIN training_sessions s ON s.id = a.session_id JOIN questions q ON q.id = a.question_id
        LEFT JOIN LATERAL (SELECT k.name FROM knowledge_points k WHERE k.id = (CASE WHEN q.knowledge_point_ids->>0 ~ '^[0-9]+$' THEN (q.knowledge_point_ids->>0)::bigint END)) kp ON true
        WHERE s.student_id = :sid AND COALESCE(a.is_seed_data, false) = false AND NOT a.is_correct AND NOT ({blank_sql})
          AND q.question_type IN ('SINGLE_CHOICE', 'MULTIPLE_CHOICE', 'TRUE_FALSE')
        GROUP BY a.question_id, kp.name, a.student_answer""", sid=sid)
    per_q: dict[int, list] = {}
    for x in rows:
        per_q.setdefault(x["question_id"], []).append(x)
    mis = []
    for qid, xs in per_q.items():
        total = sum(x["n"] for x in xs)
        top = max(xs, key=lambda x: x["n"])
        if total >= MISCONCEPTION_MIN and top["n"] / total >= MISCONCEPTION_SHARE:
            mis.append({"question_id": qid, "kp": top["kp"], "answer": top["ans"], "wrong_times": total, "same_times": top["n"]})
    mis.sort(key=lambda m: -m["same_times"])
    for m in mis:
        where = f"「{m['kp']}」里的一道题" if m["kp"] else f"题目 #{m['question_id']}"
        m["text"] = f"{where}答错了 {m['wrong_times']} 次，其中 {m['same_times']} 次都选「{m['answer']}」，很可能存在固定的错误理解，建议讲清楚这个错误答案错在哪里"
    out["misconceptions"] = mis[:5]

    # ④ 选项倾向：单选总选同一个字母 / 判断总答同一边，多半在猜
    r = await _rows(db, f"""
        SELECT q.question_type k, a.student_answer ans, count(*) n {_BASE} AND NOT ({blank_sql})
          AND q.question_type IN ('SINGLE_CHOICE', 'TRUE_FALSE') GROUP BY 1, 2""", sid=sid)
    bias = {"text": None, "items": []}
    for qt, label in (("SINGLE_CHOICE", "单选题"), ("TRUE_FALSE", "判断题")):
        xs = [x for x in r if x["k"] == qt]
        tot = sum(x["n"] for x in xs)
        if tot >= BIAS_MIN_ANSWERS:
            top = max(xs, key=lambda x: x["n"])
            share = round(top["n"] / tot * 100, 1)
            bias["items"].append({"type": qt, "label": label, "answer": top["ans"], "share": share, "answered": tot})
            if share >= BIAS_SHARE * 100 and not bias["text"]:
                bias["text"] = f"{label}有 {share}% 都选「{top['ans']}」（共 {tot} 道），像是在猜答案，建议让学生每题写出选择理由"
    out["bias"] = bias
    return out


async def _ai(db, sid):
    msgs = await _one(db, """
        SELECT count(*) FILTER (WHERE m.role='student') stu, count(*) FILTER (WHERE m.role='assistant') ast,
               count(*) FILTER (WHERE m.is_aha_trigger) aha, max(m.created_at) last_at, count(DISTINCT m.session_id) sess
        FROM ai_chat_messages m JOIN ai_chat_sessions cs ON cs.id = m.session_id WHERE cs.student_id=:sid""", sid=sid)
    strat = await _rows(db, """
        SELECT p.strategy_id, st.strategy_name, p.total_uses, p.positive_ratings, p.negative_ratings, p.effectiveness_score
        FROM ai_student_strategy_profiles p JOIN ai_heuristic_strategies st ON st.strategy_id = p.strategy_id
        WHERE p.student_id=:sid AND p.total_uses > 0 ORDER BY p.effectiveness_score DESC""", sid=sid)
    sig = await _one(db, "SELECT intents, chat_summary, refreshed_at FROM student_learning_signals WHERE student_id=:sid", sid=sid)
    items = [{"strategy_id": r["strategy_id"], "name": r["strategy_name"], "uses": r["total_uses"], "likes": r["positive_ratings"],
              "dislikes": r["negative_ratings"], "score": _r(r["effectiveness_score"])} for r in strat]
    intents = []
    if sig and sig["intents"]:
        raw = sig["intents"]
        raw = raw if isinstance(raw, list) else raw.get("items", []) if isinstance(raw, dict) else []
        raw = raw[:10]
        ids = [int(x["kp_id"]) for x in raw if isinstance(x, dict) and str(x.get("kp_id", "")).isdigit()]
        names = {}
        if ids:
            names = {r["id"]: r["name"] for r in await _rows(db, "SELECT id, name FROM knowledge_points WHERE id = ANY(:ids)", ids=ids)}
        intents = [{"kp_id": x.get("kp_id"), "name": names.get(int(x["kp_id"])) if str(x.get("kp_id", "")).isdigit() else None,
                    "confidence": x.get("confidence"), "mentioned_at": x.get("mentioned_at")} for x in raw if isinstance(x, dict)]
    return {
        "student_messages": msgs["stu"], "assistant_messages": msgs["ast"], "sessions": msgs["sess"],
        "last_chat_at": msgs["last_at"], "aha_count": msgs["aha"],
        "top_strategies": items[:3], "bottom_strategies": [i for i in reversed(items) if i["score"] is not None][:1] if len(items) > 3 else [],
        "strategies": items,
        "intents": intents, "chat_summary": sig["chat_summary"] if sig else None, "intents_refreshed_at": sig["refreshed_at"] if sig else None,
    }


async def _traits(db, sid):
    r = await _one(db, """
        SELECT personal_insight, insight_admin_text, insight_ai_text, personal_insight_updated_at, learning_summary, learning_summary_updated_at
        FROM student_ai_prompt_summaries WHERE student_id=:sid""", sid=sid)
    return dict(r) if r else {"personal_insight": None, "insight_admin_text": None, "insight_ai_text": None}


async def _weekly(db, sid):
    """近 4 周（每周一个点，从旧到新）的做题量和正确率"""
    rows = await _rows(db, f"""
        SELECT floor(extract(epoch FROM (now() - a.answered_at)) / 604800)::int w, count(*) n, count(*) FILTER (WHERE a.is_correct) c
        {_BASE} AND a.answered_at >= now() - interval '28 days' GROUP BY 1""", sid=sid)
    by = {r["w"]: r for r in rows}
    out = []
    for w in (3, 2, 1, 0):
        r = by.get(w)
        out.append({"weeks_ago": w, "answered": r["n"] if r else 0, "accuracy": _pct(r["c"], r["n"]) if r else None})
    return out


def _slope(weeks):
    pts = [(i, w["accuracy"]) for i, w in enumerate(weeks) if w["accuracy"] is not None and w["answered"] >= 3]
    if len(pts) < 2:
        return None
    n = len(pts)
    mx = sum(x for x, _ in pts) / n
    my = sum(y for _, y in pts) / n
    den = sum((x - mx) ** 2 for x, _ in pts)
    return round(sum((x - mx) * (y - my) for x, y in pts) / den, 2) if den else None


def _summary(basic, cog, mastery, beh, ai, weeks, answered_30, weights=None, diagnosis=None, insights=None):
    sess = beh["_sessions"]
    now = datetime.now(timezone.utc)
    s14 = sum(1 for s in sess if s["started_at"] >= now - timedelta(days=14))
    prev14 = sum(1 for s in sess if now - timedelta(days=28) <= s["started_at"] < now - timedelta(days=14))
    slope = _slope(weeks)
    last = beh["last_active_date"]
    idle = None
    if last:
        today = datetime.now(timezone(timedelta(hours=8))).date()
        idle = (today - datetime.fromisoformat(last).date()).days

    if answered_30 < 20:
        status, reason = "数据不足", f"近 30 天只答了 {answered_30} 道题，样本太少，暂不下结论"
    elif (idle is not None and idle >= 7) or (prev14 >= 2 and s14 < prev14 / 2):
        status, reason = "近期懈怠", f"已 {idle} 天没有训练" if idle is not None and idle >= 7 else f"近 14 天训练 {s14} 次，不足前 14 天（{prev14} 次）的一半"
    elif slope is not None and slope > 2:
        status, reason = "稳步提升", f"近 4 周正确率平均每周上升 {slope} 个百分点"
    elif slope is not None and slope < -2:
        status, reason = "遇到瓶颈", f"近 4 周正确率平均每周下降 {abs(slope)} 个百分点"
    else:
        status, reason = "状态平稳", "近 4 周正确率变化不大" if slope is not None else "近 4 周有效数据不足以判断趋势，暂按平稳处理"

    w = weights or {"frequency": 40, "streak": 20, "complete": 25, "careful": 15}
    w_freq, w_streak, w_comp, w_care = (w["frequency"] / 100, w["streak"] / 100, w["complete"] / 100, w["careful"] / 100)
    f = min(1.0, beh["sessions_30d"] / 12)
    st = min(1.0, beh["streak_days"] / 7)
    comp = (beh["complete_rate"] or 0) / 100
    # 认真作答：「快而错」（用时最短的三分之一题里答错的）占全部答题的比例越低越高，40% 及以上为 0；没有答题记录为 0
    fw = beh["fast_wrong_ratio"]
    careful = None if fw is None or beh["fast_wrong_samples"] < MIN_CAREFUL_SAMPLES else 1 - min(1.0, fw / 40)
    if careful is None:   # 样本不够：这一项不计入，其余三项按比例折算到 100 分
        rest = 1 - w_care
        engagement = round((f * w_freq + st * w_streak + comp * w_comp) / rest * 100) if rest > 0 else 0
    else:
        engagement = round((f * w_freq + st * w_streak + comp * w_comp + careful * w_care) * 100)

    from app.services import profile_actions
    ctx = {"diagnosis": diagnosis or {"answered": 0, "blank_rate": None, "blank_by_type": [], "repeat": {"questions": 0, "gain": None}, "type_time": []},
           "mastery": mastery, "behavior": beh, "retention": (diagnosis or {}).get("retention"), "status": status,
           "wrong_pending": mastery["wrong_pending"], "insights": insights or {},
           "cognitive": {**cog, "primary_weakness_label": POWER_LABELS.get(cog.get("primary_weakness") or "")}}
    tips = profile_actions.build_actions(ctx)
    return {
        "status": status, "status_reason": reason, "engagement_score": engagement,
        "engagement_parts": {"frequency": round(f * 100), "streak": round(st * 100), "complete": round(comp * 100), "careful": None if careful is None else round(careful * 100)},
        "trend": {"weeks": weeks, "slope": slope}, "tips": tips,
    }


async def get_profile(db: AsyncSession, student_id: int) -> dict:
    basic = await _basic(db, student_id)
    cog = await _cognitive(db, student_id)
    mastery = await _mastery(db, student_id, basic["grade"], basic["semester"])
    beh = await _behavior(db, student_id)
    ai = await _ai(db, student_id)
    traits = await _traits(db, student_id)
    cog["power_trend"] = await _power_trend(db, student_id)
    diagnosis = await _diagnosis(db, student_id)
    insights = await _insights(db, student_id)
    weeks = await _weekly(db, student_id)
    n30 = (await _one(db, f"SELECT count(*) n {_BASE} AND a.answered_at >= now() - interval '30 days'", sid=student_id))["n"]
    from app.services import profile_config, profile_warning_service
    summary = _summary(basic, cog, mastery, beh, ai, weeks, n30, await profile_config.get_weights(db), diagnosis, insights)
    beh.pop("_sessions", None)
    await profile_warning_service.sync(db, student_id, basic)
    warnings = await profile_warning_service.list_warnings(db, student_id)
    return {
        "generated_at": datetime.now(timezone.utc),
        "summary": summary, "basic": basic, "cognitive": cog, "mastery": mastery,
        "behavior": beh, "diagnosis": diagnosis, "insights": insights, "ai_interaction": ai, "traits": traits,
        "warnings": warnings,
    }
