"""学生画像（管理员视图）：把训练、五力、错题、AI 互动等已有数据汇总成一份画像。

一期只用现有表，不依赖日汇总表：直接按单个学生查询。设计见 docs/4.架构设计/09_学生画像设计方案.md。
"""
import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

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
MIN_REVIEW_WRONG = 3        # 「错题复盘」至少要有这么多道错题记录才有意义，不够时这一项不计入
REVIEW_W_MASTERED = 0.6     # 错题复盘 = 错题攻克率 × 60% + 主动复盘 × 40%
RUSH_SECONDS = 3   # 非空作答、用时不超过这个秒数的错题，视为「秒答」（可能没读题或乱选）

# 学习投入度权重默认值见 profile_config.DEFAULT_WEIGHTS（可在配置管理里修改）

_BASE = """
FROM training_answer_records a
JOIN training_sessions s ON s.id = a.session_id
JOIN questions q ON q.id = a.question_id
WHERE s.student_id = :sid AND COALESCE(a.is_seed_data, false) = false
"""


def _base(windowed: bool = False) -> str:
    """答题记录的基础查询；windowed=True 时只看所选日期范围内（:since ≤ 答题时间 < :until）的答题"""
    return _BASE + ("  AND a.answered_at >= :since AND a.answered_at < :until\n" if windowed else "")


BJ = timezone(timedelta(hours=8))
DEFAULT_DAYS = 7          # 默认看近一周
MAX_RANGE_DAYS = 90       # 日期范围最长 90 天


def today_bj() -> date:
    return datetime.now(BJ).date()


@dataclass(frozen=True)
class Range:
    """画像的统计日期范围（北京时间，含起止两天）。答题量、行为、诊断等按它统计；各种阈值按天数折算"""
    start: date
    end: date

    @classmethod
    def last(cls, n: int) -> "Range":
        e = today_bj()
        return cls(e - timedelta(days=n - 1), e)

    @classmethod
    def build(cls, start: str | None, end: str | None) -> "Range":
        try:
            e = date.fromisoformat(end) if end else today_bj()
            st = date.fromisoformat(start) if start else e - timedelta(days=DEFAULT_DAYS - 1)
        except ValueError:
            raise AppException("日期格式应为 YYYY-MM-DD", 400)
        if e > today_bj():
            raise AppException("结束日期不能晚于今天", 400)
        if st > e:
            raise AppException("开始日期不能晚于结束日期", 400)
        if (e - st).days + 1 > MAX_RANGE_DAYS:
            raise AppException(f"日期范围最长 {MAX_RANGE_DAYS} 天", 400)
        return cls(st, e)

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1

    @property
    def since(self) -> datetime:
        return datetime(self.start.year, self.start.month, self.start.day, tzinfo=BJ)

    @property
    def until(self) -> datetime:      # 不含
        return self.since + timedelta(days=self.days)

    @property
    def params(self) -> dict:
        return {"since": self.since, "until": self.until}

    @property
    def prev_since(self) -> datetime:     # 前一段同样长度的时间
        return self.since - timedelta(days=self.days)

    @property
    def is_recent(self) -> bool:
        return self.end == today_bj()

    @property
    def label(self) -> str:
        return f"近 {self.days} 天" if self.is_recent else f"所选 {self.days} 天"

    @property
    def daily(self) -> bool:       # 14 天以内按天看趋势，更长按周
        return self.days <= 14

    @property
    def cmp_len(self) -> int:      # 训练次数对比的窗口：范围本身（14 天内），或范围后半段
        return self.days if self.days <= 14 else math.ceil(self.days / 2)

    @property
    def cmp_label(self) -> str:
        return f"近 {self.cmp_len} 天" if self.is_recent else f"所选范围末 {self.cmp_len} 天"

    @property
    def min_answered(self) -> int:     # 范围内至少答这么多题，才对学习状态下结论（7 天 8 道，30 天 20 道）
        return max(8, min(20, round(self.days * 2 / 3)))

    @property
    def freq_full(self) -> int:        # 训练频次满分所需的训练次数（每 30 天 12 次）
        return max(1, math.ceil(12 * self.days / 30))

    @property
    def review_full(self) -> int:      # 主动复盘满分所需的错题集训练次数（每 30 天 4 次）
        return max(1, round(4 * self.days / 30))

    @property
    def points(self) -> int:
        return self.days if self.daily else math.ceil(self.days / 7)

    def info(self) -> dict:
        return {"start": str(self.start), "end": str(self.end), "days": self.days, "label": self.label, "is_recent": self.is_recent,
                "daily": self.daily, "min_answered": self.min_answered, "freq_full": self.freq_full, "review_full": self.review_full}

    def bucket_sql(self) -> str:
        """答题落在第几个趋势点（0 = 最近一天 / 最后一周）。按天：从结束日往前数；按周：从开始日起每 7 天一格，最后一格可能不满一周"""
        day = f"(a.answered_at AT TIME ZONE '{TZ}')::date"
        if self.daily:
            return f"(CAST(:end_date AS date) - {day})"
        return f"({self.points - 1} - ({day} - CAST(:start_date AS date)) / 7)"

    @property
    def bucket_params(self) -> dict:
        return {"end_date": self.end} if self.daily else {"start_date": self.start}

    def bucket_label(self, i: int) -> str:
        if self.daily:
            d = self.end - timedelta(days=i)
            return "今天" if d == today_bj() else f"{d.month}/{d.day}"
        d = self.start + timedelta(days=(self.points - 1 - i) * 7)
        return f"{d.month}/{d.day}起"


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


async def _mastery(db, sid, grade, semester, rng):
    """答题量 / 正确率 / 题型、难度、科目表现按时间范围统计；错题、知识点掌握、学期进度是「当前状态」，不受时间范围限制"""
    B = _base(True)
    tot = await _one(db, f"SELECT count(*) n, count(*) FILTER (WHERE a.is_correct) c {B}", sid=sid, **rng.params)
    by_type = await _rows(db, f"SELECT q.question_type k, count(*) n, count(*) FILTER (WHERE a.is_correct) c {B} GROUP BY 1", sid=sid, **rng.params)
    by_diff = await _rows(db, f"SELECT q.difficulty k, count(*) n, count(*) FILTER (WHERE a.is_correct) c {B} GROUP BY 1", sid=sid, **rng.params)
    subj = await _rows(db, f"""
        SELECT sb.name k, count(*) n, count(*) FILTER (WHERE a.is_correct) c
        FROM training_answer_records a JOIN training_sessions s ON s.id=a.session_id
        JOIN questions q ON q.id=a.question_id JOIN subjects sb ON sb.id=q.subject_id
        WHERE s.student_id=:sid AND COALESCE(a.is_seed_data,false)=false AND a.answered_at >= :since AND a.answered_at < :until GROUP BY 1""", sid=sid, **rng.params)
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


async def _behavior(db, sid, rng):
    B = _base(True)
    sess = await _rows(db, "SELECT started_at, session_status, is_early_end, training_dimension, total_questions FROM training_sessions WHERE student_id=:sid", sid=sid)
    sw = [s for s in sess if rng.since <= s["started_at"] < rng.until]      # 所选范围内的训练
    finished = [s for s in sw if s["session_status"] in ("completed", "abandoned")]
    completed = sum(1 for s in finished if s["session_status"] == "completed")
    issued = sum(int(s["total_questions"] or 0) for s in sw)
    ans_cnt = await _one(db, f"SELECT count(*) n {B}", sid=sid, **rng.params)
    dims: dict[str, int] = {}
    for s in sw:
        dims[s["training_dimension"]] = dims.get(s["training_dimension"], 0) + 1

    days = await _rows(db, f"SELECT DISTINCT (a.answered_at AT TIME ZONE '{TZ}')::date d {_BASE} ORDER BY 1 DESC", sid=sid)
    dayset = [r["d"] for r in days if r["d"] <= rng.end]     # 连续天数、最近训练日都以范围结束日为准
    streak = 0
    if dayset:
        cur = dayset[0] if (rng.end - dayset[0]).days <= 1 else None
        while cur and cur in dayset:
            streak += 1
            cur -= timedelta(days=1)
    last_day = dayset[0] if dayset else None
    active_days = sum(1 for d in dayset if d >= rng.start)

    hours = await _rows(db, f"SELECT extract(hour FROM a.answered_at AT TIME ZONE '{TZ}')::int h, count(*) n, count(*) FILTER (WHERE a.is_correct) c {B} GROUP BY 1", sid=sid, **rng.params)
    total_h = sum(r["n"] for r in hours) or 0
    buckets = []
    for key, label, lo, hi in TIME_BUCKETS:
        rs = [r for r in hours if lo <= (r["h"] if r["h"] >= 6 else r["h"] + 24) < hi]
        n, c = sum(r["n"] for r in rs), sum(r["c"] for r in rs)
        buckets.append({"key": key, "label": label, "count": n, "ratio": _pct(n, total_h), "accuracy": _pct(c, n)})

    t = await _one(db, f"""
        SELECT avg(a.time_spent_sec) avg_t, percentile_cont(0.33) WITHIN GROUP (ORDER BY a.time_spent_sec) p33,
               count(*) n {B} AND a.time_spent_sec IS NOT NULL""", sid=sid, **rng.params)
    fw = None
    if t and t["n"] and t["p33"] is not None:
        r = await _one(db, f"""
            SELECT count(*) FILTER (WHERE a.time_spent_sec <= :p AND NOT a.is_correct) fw, count(*) n {B}
            AND a.time_spent_sec IS NOT NULL""", sid=sid, p=t["p33"], **rng.params)
        fw = _pct(r["fw"], r["n"])
    per_sess = await _one(db, f"""
        SELECT avg(x.tot) v FROM (SELECT sum(a.time_spent_sec) tot {B} GROUP BY a.session_id) x""", sid=sid, **rng.params)
    return {
        "sessions_range": len(sw), "sessions_total": len(sess), "streak_days": streak, "active_days": active_days,
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


async def _power_trend(db, sid, rng):
    """五力训练趋势，跟随所选日期范围：14 天以内按天（某天某力答题少于 2 道不画点），更长按周（少于 3 道不画点）"""
    min_n = 2 if rng.daily else 3
    rows = await _rows(db, f"""
        SELECT {rng.bucket_sql()} w, a.power_type p, count(*) n, count(*) FILTER (WHERE a.is_correct) c
        {_base(True)} AND a.power_type IS NOT NULL GROUP BY 1, 2""", sid=sid, **rng.bucket_params, **rng.params)
    by = {(r["w"], r["p"]): r for r in rows}
    weeks = []
    for w in range(rng.points - 1, -1, -1):
        item = {"weeks_ago": w, "label": rng.bucket_label(w), "powers": {}}
        for p in POWERS:
            r = by.get((w, p))
            item["powers"][p] = {"answered": r["n"] if r else 0, "accuracy": _pct(r["c"], r["n"]) if r and r["n"] >= min_n else None}
        weeks.append(item)
    total = sum(r["n"] for r in rows)
    return {"weeks": weeks, "answered": total, "unit": "day" if rng.daily else "week", "min_answers": min_n,
            "has_data": any(v["accuracy"] is not None for w in weeks for v in w["powers"].values())}


async def _diagnosis(db, sid, rng):
    """答题诊断：跳题（未作答就提交）、错因构成（时间范围内）；同一道题反复做是否有进步（需要看全部历史，不受时间范围限制）"""
    blank_sql = "coalesce(btrim(a.student_answer), '') = ''"
    B = _base(True)
    tot = await _one(db, f"SELECT count(*) n, count(*) FILTER (WHERE {blank_sql}) blank {B}", sid=sid, **rng.params)
    by_type = await _rows(db, f"SELECT q.question_type k, count(*) n, count(*) FILTER (WHERE {blank_sql}) blank {B} GROUP BY 1", sid=sid, **rng.params)
    wrong = await _one(db, f"""
        SELECT count(*) n, count(*) FILTER (WHERE {blank_sql}) blank,
               count(*) FILTER (WHERE NOT ({blank_sql}) AND a.time_spent_sec <= :rush) rush {B} AND NOT a.is_correct""", sid=sid, rush=RUSH_SECONDS, **rng.params)
    att = await _rows(db, f"""
        SELECT least(x.att, 3) k, count(*) n, count(*) FILTER (WHERE x.is_correct) c FROM (
            SELECT a.is_correct, row_number() OVER (PARTITION BY a.question_id ORDER BY a.answered_at) att,
                   count(*) OVER (PARTITION BY a.question_id) tot {_BASE}) x
        WHERE x.tot >= 2 GROUP BY 1 ORDER BY 1""", sid=sid)
    rep = await _one(db, f"""SELECT count(*) q FROM (SELECT a.question_id {_BASE} GROUP BY 1 HAVING count(*) >= 2) t""", sid=sid)
    tt = await _rows(db, f"""
        SELECT q.question_type k, count(*) FILTER (WHERE a.is_correct) rn, count(*) FILTER (WHERE NOT a.is_correct AND NOT ({blank_sql})) wn,
               avg(a.time_spent_sec) FILTER (WHERE a.is_correct) ar, avg(a.time_spent_sec) FILTER (WHERE NOT a.is_correct AND NOT ({blank_sql})) aw
        {B} GROUP BY 1""", sid=sid, **rng.params)
    ret = await _one(db, """
        SELECT count(*) n, count(*) FILTER (WHERE a.is_correct) c FROM training_answer_records a
        JOIN training_sessions s ON s.id = a.session_id
        JOIN wrong_answer_records w ON w.student_id = s.student_id AND w.question_id = a.question_id AND w.aha_at IS NOT NULL AND a.answered_at > w.aha_at
        WHERE s.student_id = :sid AND COALESCE(a.is_seed_data, false) = false AND a.answered_at >= :since AND a.answered_at < :until""", sid=sid, **rng.params)
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


async def _insights(db, sid, rng):
    """更深入的挖掘：题序疲劳（时间范围内）、看过智能解答后的效果、反复选同一个错误答案（概念性误解）、选项倾向（这三项要看全部历史，不受时间范围限制）"""
    blank_sql = "coalesce(btrim(a.student_answer), '') = ''"
    out: dict = {}

    # ① 题序疲劳：同一次训练里，前半段 vs 后半段
    r = await _rows(db, f"""
        SELECT (a.question_index * 2 >= s.total_questions) AS late, count(*) n, count(*) FILTER (WHERE a.is_correct) c,
               count(*) FILTER (WHERE {blank_sql}) b {_base(True)} AND s.total_questions >= 4 GROUP BY 1""", sid=sid, **rng.params)
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


async def _ai(db, sid, rng):
    msgs = await _one(db, """
        SELECT count(*) FILTER (WHERE m.role='student' AND m.created_at >= :since AND m.created_at < :until) stu,
               count(*) FILTER (WHERE m.role='assistant' AND m.created_at >= :since AND m.created_at < :until) ast,
               count(*) FILTER (WHERE m.is_aha_trigger AND m.created_at >= :since AND m.created_at < :until) aha, max(m.created_at) last_at,
               count(DISTINCT m.session_id) FILTER (WHERE m.created_at >= :since AND m.created_at < :until) sess
        FROM ai_chat_messages m JOIN ai_chat_sessions cs ON cs.id = m.session_id WHERE cs.student_id=:sid""", sid=sid, **rng.params)
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


async def _trend(db, sid, rng):
    """正确率趋势：14 天以内按天，更长按周；从旧到新"""
    rows = await _rows(db, f"""
        SELECT {rng.bucket_sql()} w, count(*) n, count(*) FILTER (WHERE a.is_correct) c
        {_base(True)} GROUP BY 1""", sid=sid, **rng.bucket_params, **rng.params)
    by = {r["w"]: r for r in rows}
    out = []
    for w in range(rng.points - 1, -1, -1):
        r = by.get(w)
        out.append({"weeks_ago": w, "label": rng.bucket_label(w), "answered": r["n"] if r else 0, "accuracy": _pct(r["c"], r["n"]) if r else None})
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

async def _recent_accuracy(db, sid, rng):
    """所选范围 vs 前一段同样长度的时间的答题量和正确率（学习状态用）"""
    r = await _one(db, f"""
        SELECT count(*) FILTER (WHERE a.answered_at >= :since AND a.answered_at < :until) n1,
               count(*) FILTER (WHERE a.answered_at >= :since AND a.answered_at < :until AND a.is_correct) c1,
               count(*) FILTER (WHERE a.answered_at >= :prev AND a.answered_at < :since) n0,
               count(*) FILTER (WHERE a.answered_at >= :prev AND a.answered_at < :since AND a.is_correct) c0
        {_BASE}""", sid=sid, prev=rng.prev_since, **rng.params)
    return {"n": r["n1"], "acc": _pct(r["c1"], r["n1"]), "n_prev": r["n0"], "acc_prev": _pct(r["c0"], r["n0"])}


def _delta(a, b):
    return None if a is None or b is None else round(a - b, 1)


def _status_detail(status, beh, mastery, cog, diagnosis, insights, recent, idle, s14, prev14, active_days, rng=None):
    """学习状态的依据和原因：关键指标 + 归因（好的 / 需要关注的）。只在样本足够时下结论。"""
    rng = rng or Range.last(30)
    days, win = rng.days, rng.cmp_len
    cl = rng.cmp_label
    recent = recent or {}
    acc30, delta_acc = recent.get("acc"), _delta(recent.get("acc"), recent.get("acc_prev"))
    if recent.get("n_prev", 0) < 10:
        delta_acc = None   # 前一个月答题太少，对比没有意义

    metrics = [
        {"key": "idle", "label": "距上次训练", "value": "—" if idle is None else "今天" if idle == 0 else f"{idle} 天",
         "hint": "超过 7 天算懈怠" if idle is not None and idle >= 7 else None, "tone": "warn" if idle is not None and idle >= 7 else None},
        {"key": "sessions", "label": f"{cl}训练", "value": f"{s14} 次", "hint": f"前 {win} 天 {prev14} 次",
         "tone": "warn" if prev14 >= 2 and s14 < prev14 / 2 else "good" if s14 > prev14 else None},
        {"key": "accuracy", "label": f"{rng.label}正确率", "value": "—" if acc30 is None else f"{acc30}%",
         "hint": None if delta_acc is None else f"较前 {days} 天{'+' if delta_acc >= 0 else ''}{delta_acc}pp",
         "tone": None if delta_acc is None else "good" if delta_acc >= 5 else "warn" if delta_acc <= -5 else None},
        {"key": "answered", "label": f"{rng.label}答题", "value": f"{recent.get('n', 0)} 题",
         "hint": None if active_days is None else f"活跃 {active_days} 天", "tone": None},
    ]

    good, warn = [], []
    # ① 训练节奏
    if idle is not None and idle >= 7:
        warn.append(f"已 {idle} 天没有训练，建议先通过家长或班级提醒重新开始，哪怕每天只做 5 道题")
    elif prev14 >= 2 and s14 < prev14 / 2:
        warn.append(f"{cl}训练 {s14} 次，不到前 {win} 天（{prev14} 次）的一半，学习节奏在放缓")
    elif s14 >= max(2, rng.freq_full // 3) and s14 >= prev14:
        good.append(f"{cl}训练 {s14} 次，节奏稳定" + (f"，已连续学习 {beh['streak_days']} 天" if beh.get("streak_days", 0) >= 3 else ""))
    # ② 正确率变化
    if delta_acc is not None:
        if delta_acc >= 5:
            good.append(f"{rng.label}正确率 {acc30}%，比前 {days} 天提高 {delta_acc} 个百分点")
        elif delta_acc <= -5:
            warn.append(f"{rng.label}正确率 {acc30}%，比前 {days} 天下降 {abs(delta_acc)} 个百分点，需要找出下降的原因")
    # ③ 错因（样本够才下结论）
    d = diagnosis or {}
    if d.get("wrong", 0) >= (5 if days <= 14 else 10):
        top = max(d.get("causes") or [{"ratio": 0}], key=lambda c: c.get("ratio") or 0)
        if (top.get("ratio") or 0) >= 40:
            where = {"blank": "没作答就提交，更像是跳题、没投入", "rush": "答得过快，可能没有读题或在乱选",
                     "thoughtful": "认真做了仍然错，是真正的知识缺口"}.get(top.get("key"))
            if where:
                warn.append(f"{top['ratio']}% 的错题属于「{top['label']}」：{where}")
    # ④ 最需要突破的知识点 / 最稳的知识点
    weak = (mastery.get("weak_kps") or [])[:1]
    if weak:
        k = weak[0]
        tr = {"down": "，而且越做越差", "flat": "，反复练习没起色", "up": "，但近期在进步"}.get(k.get("trend"), "")
        warn.append(f"最薄弱的是「{k['name']}」，错误率 {k['error_rate']}%（做过 {k['attempts']} 次）{tr}")
    strong = (mastery.get("strong_kps") or [])[:1]
    if strong and strong[0].get("attempts", 0) >= 3:
        good.append(f"「{strong[0]['name']}」掌握得最好，错误率仅 {strong[0]['error_rate']}%")
    # ⑤ 错题积压
    pending, stubborn = mastery.get("wrong_pending") or 0, mastery.get("stubborn_questions") or 0
    if stubborn >= 3:
        warn.append(f"有 {stubborn} 道顽固错题（同一道题错 3 次以上），单靠重复练习不容易攻克，需要讲解")
    elif pending >= 10:
        warn.append(f"待攻克的错题已积压 {pending} 道")
    elif mastery.get("wrong_mastered_rate") is not None and mastery.get("wrong_mastered", 0) >= 5 and mastery["wrong_mastered_rate"] >= 60:
        good.append(f"错题攻克率 {mastery['wrong_mastered_rate']}%，订正习惯较好")
    # ⑥ 能力短板 / 疲劳
    pw = (cog or {}).get("primary_weakness")
    if pw and (cog.get("final") or {}).get(pw) is not None and POWER_LABELS.get(pw):
        warn.append(f"五力中「{POWER_LABELS[pw]}」最弱（{cog['final'][pw]} 分），可作为补弱训练方向")
    fat = ((insights or {}).get("fatigue") or {}).get("verdict")
    if fat:
        warn.append(fat)

    first, second = (good, warn) if status == "稳步提升" else (warn, good)
    tone = {id(x): ("good" if first is good else "warn") for x in first}
    tone.update({id(x): ("warn" if first is good else "good") for x in second})
    drivers = [{"tone": tone[id(x)], "text": x} for x in (first[:3] + second[:2])][:4]
    return {"metrics": metrics, "drivers": drivers}


def _summary(basic, cog, mastery, beh, ai, weeks, answered_in_range, weights=None, diagnosis=None, insights=None, recent=None, rng=None):
    rng = rng or Range.last(30)
    sess = beh["_sessions"]
    n, win = rng.days, rng.cmp_len
    # 训练次数对比：范围末 win 天 vs 再前 win 天
    cur_from = rng.until - timedelta(days=win)
    s14 = sum(1 for s in sess if cur_from <= s["started_at"] < rng.until)
    prev14 = sum(1 for s in sess if cur_from - timedelta(days=win) <= s["started_at"] < cur_from)
    recent = recent or {}
    # 正确率走向：14 天以内点太少，和前一段同样长度的时间比；更长的看每周的变化斜率
    slope = _slope(weeks) if not rng.daily else None
    delta = None
    if rng.daily and recent.get("n", 0) >= 10 and recent.get("n_prev", 0) >= 10:
        delta = _delta(recent.get("acc"), recent.get("acc_prev"))
    # 较上一个周期（前一段同样长度的时间）的正确率变化，两段各需 ≥ 10 道题；供趋势卡片标题栏展示
    period_delta = _delta(recent.get("acc"), recent.get("acc_prev")) if recent.get("n", 0) >= 10 and recent.get("n_prev", 0) >= 10 else None
    up = (delta is not None and delta >= 5) if rng.daily else (slope is not None and slope > 2)
    down = (delta is not None and delta <= -5) if rng.daily else (slope is not None and slope < -2)
    last = beh["last_active_date"]
    idle = None
    if last:
        idle = (rng.end - datetime.fromisoformat(last).date()).days     # 距范围结束日多少天没训练

    if answered_in_range < rng.min_answered:
        status, reason = "数据不足", f"{rng.label}只答了 {answered_in_range} 道题，样本太少，暂不下结论"
    elif (idle is not None and idle >= 7) or (prev14 >= 2 and s14 < prev14 / 2):
        status, reason = "近期懈怠", f"已 {idle} 天没有训练" if idle is not None and idle >= 7 else f"{rng.cmp_label}训练 {s14} 次，不足前 {win} 天（{prev14} 次）的一半"
    elif up:
        status, reason = "稳步提升", f"{rng.label}正确率比前 {n} 天提高 {delta} 个百分点" if rng.daily else f"{rng.label}内正确率平均每周上升 {slope} 个百分点"
    elif down:
        status, reason = "遇到瓶颈", f"{rng.label}正确率比前 {n} 天下降 {abs(delta)} 个百分点" if rng.daily else f"{rng.label}内正确率平均每周下降 {abs(slope)} 个百分点"
    elif rng.daily:
        status, reason = "状态平稳", f"{rng.label}正确率和前 {n} 天差别不大" if delta is not None else f"{rng.label}和前 {n} 天的答题都不够多，无法对比，暂按平稳处理"
    else:
        status, reason = "状态平稳", f"{rng.label}内正确率变化不大" if slope is not None else f"{rng.label}内有效数据不足以判断趋势，暂按平稳处理"

    from app.services.profile_config import DEFAULT_WEIGHTS
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    f = min(1.0, beh["sessions_range"] / rng.freq_full)
    st = min(1.0, beh["streak_days"] / 7)
    comp = (beh["complete_rate"] or 0) / 100
    # 认真作答：「快而错」（用时最短的三分之一题里答错的）占全部答题的比例越低越高，40% 及以上为 0；没有答题记录为 0
    fw = beh["fast_wrong_ratio"]
    careful = None if fw is None or beh["fast_wrong_samples"] < MIN_CAREFUL_SAMPLES else 1 - min(1.0, fw / 40)
    # 错题复盘：做错之后有没有回头订正（错题攻克率）、有没有主动用错题集训练（时间范围内的次数）；错题太少时不计入
    wrong_total = (mastery.get("wrong_pending") or 0) + (mastery.get("wrong_mastered") or 0)
    mastered_rate = mastery.get("wrong_mastered_rate")
    review_n = sum(1 for s in sess if s["training_dimension"] == "ERROR_QUESTIONS" and rng.since <= s["started_at"] < rng.until)
    review = None if wrong_total < MIN_REVIEW_WRONG or mastered_rate is None else \
        REVIEW_W_MASTERED * mastered_rate / 100 + (1 - REVIEW_W_MASTERED) * min(1.0, review_n / rng.review_full)
    # 样本不够的项不计入，其余项按权重比例折算到 100 分
    parts = {"frequency": f, "streak": st, "complete": comp, "careful": careful, "review": review}
    used = {k: v for k, v in parts.items() if v is not None}
    den = sum(w[k] for k in used)
    engagement = round(sum(v * w[k] for k, v in used.items()) / den * 100) if den > 0 else 0

    from app.services import profile_actions
    ctx = {"diagnosis": diagnosis or {"answered": 0, "blank_rate": None, "blank_by_type": [], "repeat": {"questions": 0, "gain": None}, "type_time": []},
           "mastery": mastery, "behavior": beh, "retention": (diagnosis or {}).get("retention"), "status": status,
           "wrong_pending": mastery["wrong_pending"], "insights": insights or {},
           "cognitive": {**cog, "primary_weakness_label": POWER_LABELS.get(cog.get("primary_weakness") or "")}}
    tips = profile_actions.build_actions(ctx)
    return {
        "status": status, "status_reason": reason, "engagement_score": engagement,
        "engagement_parts": {"frequency": round(f * 100), "streak": round(st * 100), "complete": round(comp * 100), "careful": None if careful is None else round(careful * 100),
                             "review": None if review is None else round(review * 100), "review_sessions": review_n,
                             "review_wrong_total": wrong_total},
        "trend": {"weeks": weeks, "slope": slope, "delta": delta, "period_delta": period_delta, "unit": "day" if rng.daily else "week"}, "tips": tips,
        "status_detail": _status_detail(status, beh, mastery, cog, diagnosis, insights, recent, idle, s14, prev14, beh.get("active_days"), rng),
    }


async def get_profile(db: AsyncSession, student_id: int, start: str | None = None, end: str | None = None) -> dict:
    """start / end：统计日期范围（YYYY-MM-DD，北京时间，含起止两天；默认近 7 天，最长 90 天）。
    答题量、正确率、行为、诊断、AI 互动、学习状态、投入度等按这个范围统计；
    错题、知识点掌握、学期进度、五力测试、个人特质、预警这类「当前状态」不随范围变化"""
    rng = Range.build(start, end)
    basic = await _basic(db, student_id)
    cog = await _cognitive(db, student_id)
    mastery = await _mastery(db, student_id, basic["grade"], basic["semester"], rng)
    beh = await _behavior(db, student_id, rng)
    ai = await _ai(db, student_id, rng)
    traits = await _traits(db, student_id)
    cog["power_trend"] = await _power_trend(db, student_id, rng)
    diagnosis = await _diagnosis(db, student_id, rng)
    insights = await _insights(db, student_id, rng)
    weeks = await _trend(db, student_id, rng)
    recent = await _recent_accuracy(db, student_id, rng)
    from app.services import profile_config, profile_warning_service
    summary = _summary(basic, cog, mastery, beh, ai, weeks, recent["n"], await profile_config.get_weights(db), diagnosis, insights, recent, rng)
    beh.pop("_sessions", None)
    await profile_warning_service.sync(db, student_id, basic)
    warnings = await profile_warning_service.list_warnings(db, student_id)
    return {
        "generated_at": datetime.now(timezone.utc), "range": rng.info(),
        "summary": summary, "basic": basic, "cognitive": cog, "mastery": mastery,
        "behavior": beh, "diagnosis": diagnosis, "insights": insights, "ai_interaction": ai, "traits": traits,
        "warnings": warnings,
    }
