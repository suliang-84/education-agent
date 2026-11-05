"""学生画像预警：按规则配置判断触发，并把结果落到 student_warnings（支持「已处理」）。

触发在管理员打开学生画像页时同步计算；条件不再成立的未处理预警自动关闭；
管理员标记「已处理」后，同一规则 7 天内不再重复触发。
"""
from datetime import datetime, timedelta, timezone

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.profile import StudentWarning
from app.services import profile_config
from app.services.profile_service import _BASE, TZ, _one, _pct, _rows

logger = logging.getLogger(__name__)
LEVEL_ORDER = {"critical": 0, "attention": 1, "notice": 2}
RETRIGGER_DAYS = 7


async def _metrics(db: AsyncSession, sid: int, student: dict) -> dict:
    m: dict = {"is_minor": bool(student["is_minor"])}
    today = datetime.now(timezone(timedelta(hours=8))).date()

    last = await _one(db, f"SELECT max((a.answered_at AT TIME ZONE '{TZ}')::date) d {_BASE}", sid=sid)
    base_day = last["d"] if last and last["d"] else (student["created_at"].astimezone(timezone(timedelta(hours=8))).date())
    m["idle_days"] = (today - base_day).days
    m["has_answers"] = bool(last and last["d"])

    for name, lo, hi in (("recent", 0, 14), ("prev", 14, 28)):
        r = await _one(db, f"""SELECT count(*) n, count(*) FILTER (WHERE a.is_correct) c {_BASE}
            AND a.answered_at >= now() - interval '{hi} days' AND a.answered_at < now() - interval '{lo} days'""", sid=sid)
        m[f"{name}_n"], m[f"{name}_acc"] = r["n"], _pct(r["c"], r["n"])

    streaks = await _rows(db, f"""
        SELECT kp.id, kp.name, a.is_correct, a.answered_at
        FROM training_answer_records a
        JOIN training_sessions s ON s.id = a.session_id
        JOIN questions q ON q.id = a.question_id
        CROSS JOIN LATERAL jsonb_array_elements_text(q.knowledge_point_ids) AS t(kid)
        JOIN knowledge_points kp ON kp.id = (CASE WHEN t.kid ~ '^[0-9]+$' THEN t.kid::bigint END)
        WHERE s.student_id=:sid AND COALESCE(a.is_seed_data,false)=false
        ORDER BY kp.id, a.answered_at DESC""", sid=sid)
    by_kp: dict[int, dict] = {}
    for r in streaks:
        e = by_kp.setdefault(r["id"], {"name": r["name"], "flags": []})
        e["flags"].append(bool(r["is_correct"]))
    m["kp_flags"] = by_kp

    sb = await _rows(db, f"""SELECT count(*) n {_BASE} AND NOT a.is_correct GROUP BY a.question_id""", sid=sid)
    m["wrong_counts"] = [r["n"] for r in sb]

    sess = await _one(db, """SELECT COALESCE(sum(total_questions),0) issued FROM training_sessions
        WHERE student_id=:sid AND started_at >= now() - interval '14 days'""", sid=sid)
    ans = await _one(db, f"""SELECT count(*) n {_BASE} AND a.answered_at >= now() - interval '14 days'""", sid=sid)
    m["issued_14"], m["answered_14"] = int(sess["issued"]), ans["n"]

    hrs = await _rows(db, f"""SELECT extract(hour FROM a.answered_at AT TIME ZONE '{TZ}')::int h, count(*) n {_BASE}
        AND a.answered_at >= now() - interval '14 days' GROUP BY 1""", sid=sid)
    tot = sum(r["n"] for r in hrs)
    m["night_ratio"] = _pct(sum(r["n"] for r in hrs if r["h"] >= 22 or r["h"] < 6), tot)

    p = await _one(db, f"""SELECT percentile_cont(0.33) WITHIN GROUP (ORDER BY a.time_spent_sec) p33, count(*) n {_BASE}
        AND a.answered_at >= now() - interval '14 days' AND a.time_spent_sec IS NOT NULL""", sid=sid)
    m["fast_n"] = p["n"] if p else 0
    m["fast_wrong_ratio"] = None
    if p and p["n"] and p["p33"] is not None:
        fw = await _one(db, f"""SELECT count(*) FILTER (WHERE NOT a.is_correct AND a.time_spent_sec <= :p) fw {_BASE}
            AND a.answered_at >= now() - interval '14 days' AND a.time_spent_sec IS NOT NULL""", sid=sid, p=p["p33"])
        m["fast_wrong_ratio"] = _pct(fw["fw"], p["n"])

    prof = await _one(db, "SELECT max(created_at) at FROM five_power_profiles WHERE student_id=:sid", sid=sid)
    m["profile_at"] = prof["at"] if prof else None

    emo = await _one(db, "SELECT emotion_history FROM student_ai_prompt_summaries WHERE student_id=:sid", sid=sid)
    cutoff = datetime.now(timezone.utc) - timedelta(days=14)
    hist = []
    for x in (emo["emotion_history"] if emo and emo["emotion_history"] else []):
        try:
            at = datetime.fromisoformat(x["at"])
        except (KeyError, ValueError, TypeError):
            continue
        if at >= cutoff:
            hist.append({"at": at, "level": x.get("level"), "reason": x.get("reason") or ""})
    m["emotion_history"] = hist     # 近 14 天的情绪判断，从旧到新
    return m


def evaluate(m: dict, confs: dict[str, dict]) -> list[dict]:
    hits: list[dict] = []

    def add(code, level, message, detail=None):
        hits.append({"rule_code": code, "level": level, "message": message, "detail": detail or {}})

    def on(code):
        return confs[code]["enabled"]

    c = confs["NO_TRAIN"]
    if c["enabled"]:
        p, d = c["params"], m["idle_days"]
        tier = "critical" if d >= p["critical_days"] else "attention" if d >= p["attention_days"] else "notice" if d >= p["notice_days"] else None
        if tier:
            add("NO_TRAIN", tier, f"已连续 {d} 天没有训练" if m["has_answers"] else f"注册后 {d} 天一直没有训练", {"days": d})

    c = confs["ACC_DROP"]
    if c["enabled"] and m["recent_n"] >= c["params"]["min_answers"] and m["prev_n"] >= c["params"]["min_answers"]:
        drop = round(m["prev_acc"] - m["recent_acc"], 1)
        if drop >= c["params"]["drop_pp"]:
            add("ACC_DROP", c["level"], f"近 14 天正确率 {m['recent_acc']}%，比前 14 天（{m['prev_acc']}%）下降 {drop} 个百分点",
                {"recent": m["recent_acc"], "prev": m["prev_acc"]})

    c = confs["KP_STREAK_WRONG"]
    if c["enabled"]:
        n = c["params"]["streak"]
        bad = [v["name"] for v in m["kp_flags"].values() if len(v["flags"]) >= n and not any(v["flags"][:n])]
        if bad:
            add("KP_STREAK_WRONG", c["level"], f"以下知识点最近连续答错 {n} 次以上：{'、'.join(bad[:5])}{'等' if len(bad) > 5 else ''}", {"knowledge_points": bad})

    c = confs["STUBBORN_WRONG"]
    if c["enabled"]:
        k = sum(1 for x in m["wrong_counts"] if x >= c["params"]["times"])
        if k:
            add("STUBBORN_WRONG", c["level"], f"有 {k} 道题累计答错 {c['params']['times']} 次以上", {"count": k})

    c = confs["COMPLETION_LOW"]
    if c["enabled"] and m["issued_14"] >= c["params"]["min_issued"]:
        rate = _pct(m["answered_14"], m["issued_14"])
        if rate is not None and rate < c["params"]["min_rate"]:
            add("COMPLETION_LOW", c["level"], f"近 14 天发放 {m['issued_14']} 题，只作答了 {m['answered_14']} 题（{min(rate, 100)}%），经常刚开始就退出",
                {"rate": rate})

    c = confs["LATE_NIGHT"]
    if c["enabled"] and m["is_minor"] and m["recent_n"] >= c["params"]["min_answers"] and m["night_ratio"] is not None and m["night_ratio"] > c["params"]["ratio"]:
        add("LATE_NIGHT", c["level"], f"未成年学生，近 14 天 22 点后答题占 {m['night_ratio']}%", {"ratio": m["night_ratio"]})

    c = confs["FAST_WRONG"]
    if c["enabled"] and m["fast_n"] >= c["params"]["min_answers"] and m["fast_wrong_ratio"] is not None and m["fast_wrong_ratio"] > c["params"]["ratio"]:
        add("FAST_WRONG", c["level"], f"近 14 天「做得快又做错」的题占 {m['fast_wrong_ratio']}%，可能没认真读题", {"ratio": m["fast_wrong_ratio"]})

    c = confs["TEST_MISSING"]
    if c["enabled"] and m["profile_at"] is None:
        add("TEST_MISSING", c["level"], "还没有完成五力测试，没有能力画像")

    c = confs["PROFILE_STALE"]
    if c["enabled"] and m["profile_at"] is not None:
        days = (datetime.now(timezone.utc) - m["profile_at"]).days
        if days > c["params"]["days"]:
            add("PROFILE_STALE", c["level"], f"五力画像已 {days} 天没有更新", {"days": days})

    c = confs["CHAT_NEGATIVE"]
    if c["enabled"] and m["emotion_history"]:
        from app.services.assistant.emotion import LEVEL_LABELS, LEVEL_RANK
        hist = m["emotion_history"]
        need = LEVEL_RANK.get(c["params"]["min_level"], 2)
        n = c["params"]["consecutive"]
        last = hist[-1]
        urgent = last["level"] == "urgent"
        recent = hist[-n:]
        if urgent or (len(recent) >= n and all(LEVEL_RANK.get(x["level"], 0) >= need for x in recent)):
            label = LEVEL_LABELS.get(last["level"], last["level"])
            tail = f"：{last['reason']}" if last["reason"] else ""
            add("CHAT_NEGATIVE", c["level"],
                f"AI 助教对话判断情绪状态为「{label}」{tail}" + ("" if urgent or n == 1 else f"（已连续 {n} 次判断）"),
                {"level": last["level"], "reason": last["reason"], "consecutive": n})
    return hits


async def sync(db: AsyncSession, sid: int, student: dict) -> None:
    """重新计算并同步到 student_warnings（调用方负责 commit）"""
    confs = await profile_config.get_rule_confs(db)
    hits = evaluate(await _metrics(db, sid, student), confs)
    rows = (await db.execute(select(StudentWarning).where(StudentWarning.student_id == sid))).scalars().all()
    open_by = {r.rule_code: r for r in rows if r.status == "open"}
    now = datetime.now(timezone.utc)
    recent_handled = {r.rule_code for r in rows if r.status == "handled" and r.handled_at and r.handled_at > now - timedelta(days=RETRIGGER_DAYS)}
    seen = set()
    for h in hits:
        seen.add(h["rule_code"])
        cur = open_by.get(h["rule_code"])
        if cur:
            cur.level, cur.message, cur.detail = h["level"], h["message"], h["detail"]
        elif h["rule_code"] not in recent_handled:
            db.add(StudentWarning(student_id=sid, rule_code=h["rule_code"], level=h["level"], message=h["message"], detail=h["detail"], status="open"))
    for code, cur in open_by.items():
        if code not in seen:
            cur.status = "closed"
    await db.flush()


def _to_dict(w: StudentWarning) -> dict:
    return {
        "id": w.id, "rule_code": w.rule_code, "rule_name": profile_config.RULE_MAP.get(w.rule_code, {}).get("name", w.rule_code),
        "level": w.level, "level_label": profile_config.LEVELS.get(w.level, w.level), "status": w.status, "message": w.message,
        "triggered_at": w.triggered_at, "handled_at": w.handled_at, "handled_by": w.handled_by, "note": w.note,
    }


async def list_warnings(db: AsyncSession, sid: int) -> dict:
    rows = (await db.execute(select(StudentWarning).where(StudentWarning.student_id == sid, StudentWarning.status.in_(("open", "handled")))
                             .order_by(StudentWarning.triggered_at.desc()))).scalars().all()
    open_ = sorted([w for w in rows if w.status == "open"], key=lambda w: (LEVEL_ORDER.get(w.level, 9), -w.triggered_at.timestamp()))
    handled = [w for w in rows if w.status == "handled"][:10]
    return {"open": [_to_dict(w) for w in open_], "handled": [_to_dict(w) for w in handled]}


async def handle(db: AsyncSession, sid: int, wid: int, admin_id: int | None, note: str | None) -> dict:
    w = (await db.execute(select(StudentWarning).where(StudentWarning.id == wid, StudentWarning.student_id == sid))).scalar_one_or_none()
    if not w:
        raise AppException("预警不存在", 404)
    if w.status != "open":
        raise AppException("该预警已经处理过了", 400)
    note = (note or "").strip()
    if len(note) > 500:
        raise AppException("处理备注不能超过 500 字", 400)
    w.status, w.handled_by, w.handled_at, w.note = "handled", admin_id, datetime.now(timezone.utc), note or None
    await db.flush()
    return _to_dict(w)


async def scan_all(db: AsyncSession) -> dict:
    """扫描全部启用中的学生，重新计算并同步预警（学生列表的预警标记靠它保持最新）。
    单个学生出错只跳过该学生，不影响其他人。"""
    from app.models.student import Student

    students = (await db.execute(
        select(Student.id, Student.is_minor, Student.created_at)
        .where(Student.user_type == "STUDENT", Student.deleted_at.is_(None), Student.is_active == True)  # noqa: E712
    )).all()
    ok = failed = 0
    for sid, is_minor, created_at in students:
        try:
            async with db.begin_nested():
                await sync(db, sid, {"is_minor": is_minor, "created_at": created_at})
            ok += 1
        except Exception:   # noqa: BLE001
            failed += 1
            logger.exception("画像预警扫描失败：student_id=%s", sid)
    await db.commit()
    open_cnt = (await db.execute(select(func.count()).select_from(StudentWarning).where(StudentWarning.status == "open"))).scalar_one()
    return {"students": ok, "failed": failed, "open_warnings": open_cnt}


async def warning_summary(db: AsyncSession, student_ids: list[int]) -> dict[int, dict]:
    """学生列表用：每个学生未处理预警的条数和最高级别"""
    if not student_ids:
        return {}
    rows = (await db.execute(
        select(StudentWarning.student_id, StudentWarning.level, func.count())
        .where(StudentWarning.student_id.in_(student_ids), StudentWarning.status == "open")
        .group_by(StudentWarning.student_id, StudentWarning.level)
    )).all()
    out: dict[int, dict] = {}
    for sid, level, n in rows:
        e = out.setdefault(sid, {"count": 0, "level": level})
        e["count"] += n
        if LEVEL_ORDER.get(level, 9) < LEVEL_ORDER.get(e["level"], 9):
            e["level"] = level
    return out
