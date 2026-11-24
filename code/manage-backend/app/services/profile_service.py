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
# 学习时长环形图的顺序：和小程序「练习方式」一致，最后是小程序里没有入口的按学期
DIM_ORDER = ["KNOWLEDGE_POINT", "UNIT", "ERROR_QUESTIONS", "FAVORITES", "SMART", "RANDOM", "SEMESTER"]
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
DEFAULT_DAYS = 7          # 默认看近一周（不含今天：今天还没过完，数据不完整，会把对比拉偏）
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
            e = date.fromisoformat(end) if end else today_bj() - timedelta(days=1)
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
        return self.end >= today_bj() - timedelta(days=1)      # 结束日是今天或昨天，都按「近 N 天」叫

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

    def bucket_sql(self, col: str = "a.answered_at") -> str:
        """答题落在第几个趋势点（0 = 最近一天 / 最后一周）。按天：从结束日往前数；按周：从开始日起每 7 天一格，最后一格可能不满一周"""
        day = f"({col} AT TIME ZONE '{TZ}')::date"
        if self.daily:
            return f"(CAST(:end_date AS date) - {day})"
        return f"({self.points - 1} - ({day} - CAST(:start_date AS date)) / 7)"

    @property
    def bucket_params(self) -> dict:
        return {"end_date": self.end} if self.daily else {"start_date": self.start}

    def bucket_of_date(self, d: date) -> int:
        return (self.end - d).days if self.daily else self.points - 1 - (d - self.start).days // 7

    def bucket_of(self, dt: datetime) -> int:
        """和 bucket_sql 同样的分格规则，给内存里的时间用"""
        return self.bucket_of_date(dt.astimezone(BJ).date())

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
    # 上一次「成绩不同」的测试（重复测出一样的结果不算变化），用来看五力较上次测试的变化
    previous = None
    for r in reversed(rows):
        if r is latest:
            continue
        old = {p: r[f"{p.lower()}_final"] for p in POWERS}
        if old != final:
            previous = {"tested_at": r["created_at"], "final": old}
            break
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
        "tested_at": latest["created_at"], "previous_test": previous,
        "final": final, "ability": ability, "preference": pref, "training": training,
        "training_info": {"total_training_count": tp["total_training_count"], "total_question_count": tp["total_question_count"],
                          "last_trained_at": tp["last_trained_at"]} if tp else None,
        "primary_strength": latest["primary_strength"], "primary_weakness": latest["primary_weakness"],
        "secondary_weakness": latest["secondary_weakness"], "preferred_force": latest["preferred_force"],
        "recommended_mode": latest["recommended_mode"],
        "confidence": _r(latest["profile_confidence"], 2),
        "tags": tags,
    }


MIN_POWER_N = 6          # 某一力在所选范围内至少答这么多题，才拿实战表现和测试得分比较
MIN_SHARE_TOTAL = 20     # 做题量占比：范围内总答题至少这么多道才下结论


async def _power_stats(db, sid, rng):
    """各力在所选范围 / 前一段同样长度时间里的做题情况（认知能力洞察用）"""
    rows = await _rows(db, f"""
        SELECT a.power_type p,
               count(*) FILTER (WHERE a.answered_at >= :since AND a.answered_at < :until) n,
               count(*) FILTER (WHERE a.answered_at >= :since AND a.answered_at < :until AND a.is_correct) c,
               count(*) FILTER (WHERE a.answered_at >= :since AND a.answered_at < :until AND coalesce(btrim(a.student_answer), '') = '') blank,
               avg(a.time_spent_sec) FILTER (WHERE a.answered_at >= :since AND a.answered_at < :until) sec,
               count(*) FILTER (WHERE a.answered_at >= :prev AND a.answered_at < :since) n0,
               count(*) FILTER (WHERE a.answered_at >= :prev AND a.answered_at < :since AND a.is_correct) c0
        {_BASE} AND a.power_type IS NOT NULL GROUP BY 1""", sid=sid, prev=rng.prev_since, **rng.params)
    return {r["p"]: dict(r) for r in rows}


def _cognitive_insights(cog, stats, rng):
    """认知能力洞察：测试得分 vs 实战表现、做题量是否偏向某些力、近期变化、五力均衡度。
    样本不够的项不下结论；亮点最多 5 条（需要关注的在前、好的在后）。"""
    final = cog.get("final") or {}
    total = sum((stats.get(p) or {}).get("n", 0) for p in POWERS)
    lab = rng.label
    powers = []
    for p in POWERS:
        st = stats.get(p) or {}
        n, c, n0, c0 = st.get("n", 0) or 0, st.get("c", 0) or 0, st.get("n0", 0) or 0, st.get("c0", 0) or 0
        acc = _pct(c, n) if n >= 3 else None
        delta = _delta(_pct(c, n), _pct(c0, n0)) if n >= 5 and n0 >= 5 else None
        gap = round(acc - final[p], 1) if acc is not None and n >= MIN_POWER_N and final.get(p) is not None else None
        pv = (cog.get("previous_test") or {}).get("final") or {}
        powers.append({
            "key": p, "label": POWER_LABELS[p], "test": final.get(p), "answered": n, "accuracy": acc, "prev_accuracy": _pct(c0, n0) if n0 >= 5 else None,
            "delta": delta, "gap": gap, "share": _pct(n, total) if total else None,
            "blank_rate": _pct(st.get("blank", 0) or 0, n) if n >= MIN_POWER_N else None,
            "avg_seconds": _r(st.get("sec")) if n >= 3 else None,
            "test_change": (final[p] - pv[p]) if pv.get(p) is not None and final.get(p) is not None and final[p] != pv[p] else None,
            "status": "few" if n < MIN_POWER_N else "below" if gap is not None and gap <= -15 else "above" if gap is not None and gap >= 10 else "ok",
        })
    by = {x["key"]: x for x in powers}

    warn, good = [], []
    # ① 最弱的一力，做题量却很少：训练资源错配
    if final:
        wk = min(POWERS, key=lambda p: (final.get(p) if final.get(p) is not None else 999))
        sh = by[wk]["share"]
        if total >= MIN_SHARE_TOTAL and sh is not None and sh < 12 and final.get(wk) is not None:
            warn.append(f"「{POWER_LABELS[wk]}」是测试最弱的一力（{final[wk]} 分），但只占{lab}做题量的 {sh}%，训练偏向了其他能力，建议多安排这一力的题")
    # ② 测试得分和实战的落差
    above_txt = None
    below = [x for x in powers if x["status"] == "below"]
    if below:
        x = min(below, key=lambda y: y["gap"])
        extra = f"，{x['blank_rate']}% 的题没作答就提交" if (x["blank_rate"] or 0) >= 30 else ""
        warn.append(f"「{x['label']}」测试 {x['test']} 分，但{lab}实际做题正确率只有 {x['accuracy']}%（低 {abs(x['gap'])} 个百分点）{extra}——测试里的能力没有在日常做题中发挥出来")
    above = [x for x in powers if x["status"] == "above"]
    if above:
        x = max(above, key=lambda y: y["gap"])
        above_txt = f"「{x['label']}」{lab}做题正确率 {x['accuracy']}%，比测试得分（{x['test']} 分）高 {x['gap']} 个百分点，实战表现好于测试"
    # ③ 较前一段时间的变化
    ch = [x for x in powers if x["delta"] is not None]
    if ch:
        up = max(ch, key=lambda y: y["delta"])
        dn = min(ch, key=lambda y: y["delta"])
        if dn["delta"] <= -10:
            warn.append(f"「{dn['label']}」{lab}正确率 {dn['accuracy']}%，比前 {rng.days} 天下降 {abs(dn['delta'])} 个百分点")
        if up["delta"] >= 10:
            good.append(f"「{up['label']}」{lab}正确率 {up['accuracy']}%，比前 {rng.days} 天提高 {up['delta']} 个百分点")
    # ④ 较上次测试的变化
    tc = [x for x in powers if x["test_change"] is not None and abs(x["test_change"]) >= 3]
    if tc:
        pt = cog["previous_test"]["tested_at"]
        txt = "、".join(f"{x['label']} {'+' if x['test_change'] > 0 else ''}{x['test_change']}" for x in tc)
        (good if sum(x["test_change"] for x in tc) > 0 else warn).append(f"较上次测试（{pt:%m-%d}）：{txt}")
    if above_txt:
        good.append(above_txt)      # 放在近期变化、测试变化之后：这两项更有时效
    # ⑤ 均衡度
    vals = {p: final[p] for p in POWERS if final.get(p) is not None}
    balance = None
    if len(vals) == 5:
        hi, lo = max(vals, key=vals.get), min(vals, key=vals.get)
        spread = vals[hi] - vals[lo]
        level = "偏科明显" if spread >= 25 else "略有偏科" if spread >= 15 else "比较均衡"
        balance = {"spread": spread, "level": level, "strongest": hi, "weakest": lo}
        if spread >= 25:
            warn.append(f"五力差距 {spread} 分（{POWER_LABELS[hi]} {vals[hi]} 分 ➜ {POWER_LABELS[lo]} {vals[lo]} 分），偏科明显，补「{POWER_LABELS[lo]}」比继续强化「{POWER_LABELS[hi]}」收益更大")
        elif spread <= 12:
            good.append(f"五力得分只相差 {spread} 分，发展比较均衡")
    # ⑥ 实战中最稳的一力
    solid = [x for x in powers if x["answered"] >= MIN_POWER_N and (x["accuracy"] or 0) >= 60]
    if solid:
        x = max(solid, key=lambda y: y["accuracy"])
        if not any(f"「{x['label']}」" in t for t in good):
            sec = f"，平均每题 {x['avg_seconds']:g} 秒" if x["avg_seconds"] is not None else ""
            good.append(f"「{x['label']}」是{lab}做题中最稳的一力：正确率 {x['accuracy']}%（{x['answered']} 题）{sec}")
    highlights = [{"tone": "warn", "text": t} for t in warn[:3]] + [{"tone": "good", "text": t} for t in good[:2]]
    return {"powers": powers, "highlights": highlights[:5], "balance": balance, "total_answered": total}


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
        {"key": "sessions", "label": "训练次数", "value": f"{s14} 次", "hint": f"前 {win} 天 {prev14} 次",
         "delta": s14 - prev14, "unit": "次", "prev": f"前 {win} 天 {prev14} 次",
         "tone": "warn" if prev14 >= 2 and s14 < prev14 / 2 else "good" if s14 > prev14 else None},
        {"key": "accuracy", "label": "正确率", "value": "—" if acc30 is None else f"{acc30}%",
         "hint": None if delta_acc is None else f"较前 {days} 天{'+' if delta_acc >= 0 else ''}{delta_acc}pp",
         "delta": delta_acc, "unit": "%", "prev": None if recent.get("acc_prev") is None else f"前 {days} 天正确率 {recent['acc_prev']}%",
         "tone": None if delta_acc is None else "good" if delta_acc >= 5 else "warn" if delta_acc <= -5 else None},
        {"key": "answered", "label": "答题数", "value": f"{recent.get('n', 0)} 题",
         "hint": None if active_days is None else f"活跃 {active_days} 天", "tone": None,
         "delta": recent.get("n", 0) - recent.get("n_prev", 0), "unit": "题", "prev": f"前 {days} 天 {recent.get('n_prev', 0)} 题"},
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
        "trend": {"weeks": weeks, "slope": slope, "delta": delta, "unit": "day" if rng.daily else "week"}, "tips": tips,
        "status_detail": _status_detail(status, beh, mastery, cog, diagnosis, insights, recent, idle, s14, prev14, beh.get("active_days"), rng),
    }


async def _kpi_stats(db, sid, rng):
    """顶部统计卡片用：所选范围和前一段同样长度的时间各算一遍（学习时长、AI 提问）"""
    r = await _one(db, f"""
        SELECT coalesce(sum(t) FILTER (WHERE cur), 0) t1, coalesce(sum(t) FILTER (WHERE prv), 0) t0
        FROM (SELECT a.time_spent_sec t,
                     (a.answered_at >= :since AND a.answered_at < :until) cur,
                     (a.answered_at >= :prev AND a.answered_at < :since) prv
              {_BASE} AND a.answered_at >= :prev AND a.answered_at < :until) x""", sid=sid, prev=rng.prev_since, **rng.params)
    m = await _one(db, """
        SELECT count(*) FILTER (WHERE m.created_at >= :since AND m.created_at < :until) a1,
               count(*) FILTER (WHERE m.created_at >= :prev AND m.created_at < :since) a0
        FROM ai_chat_messages m JOIN ai_chat_sessions cs ON cs.id = m.session_id
        WHERE cs.student_id=:sid AND m.role='student'""", sid=sid, prev=rng.prev_since, **rng.params)
    return {**dict(r), "ai1": m["a1"], "ai0": m["a0"]}


async def _kpi_series(db, sid, rng, beh):
    """顶部统计卡片右侧的小图：所选范围内每个点（按天 / 按周，从旧到新）的数值"""
    n = rng.points
    rows = await _rows(db, f"""
        SELECT {rng.bucket_sql()} w, count(*) n, count(*) FILTER (WHERE a.is_correct) c, coalesce(sum(a.time_spent_sec), 0) t
        {_base(True)} GROUP BY 1""", sid=sid, **rng.bucket_params, **rng.params)
    by = {r["w"]: r for r in rows}
    ai = await _rows(db, f"""
        SELECT {rng.bucket_sql("m.created_at")} w, count(*) n
        FROM ai_chat_messages m JOIN ai_chat_sessions cs ON cs.id = m.session_id
        WHERE cs.student_id=:sid AND m.role='student' AND m.created_at >= :since AND m.created_at < :until GROUP BY 1""",
        sid=sid, **rng.bucket_params, **rng.params)
    aib = {r["w"]: r["n"] for r in ai}
    sess = [0] * n
    for x in beh.get("_sessions") or []:
        if rng.since <= x["started_at"] < rng.until:
            i = rng.bucket_of(x["started_at"])
            if 0 <= i < n:
                sess[n - 1 - i] += 1
    order = range(n - 1, -1, -1)       # 从旧到新
    g = lambda w, k, d=0: (by[w][k] if w in by else d)
    return {
        "study_time": [round(g(w, "t") / 60) for w in order],
        "sessions": sess,
        "answered": [g(w, "n") for w in order],
        "accuracy": [_pct(by[w]["c"], by[w]["n"]) if w in by and by[w]["n"] >= (2 if rng.daily else 3) else None for w in order],
        "ai_asks": [aib.get(w, 0) for w in order],
    }


def _fmt_minutes(sec):
    """学习时长的展示文字。口径必须和「学习时长」标签页的总时长一致（stats.total_minutes 保留 1 位小数，
    前端 fmtMin 再按 < 60 分钟 / ≥ 60 分钟换算），否则同一个数两处会因为取整顺序不同差 0.1 小时"""
    m = round((sec or 0) / 60, 1)
    return f"{m:g} 分钟" if m < 60 else f"{math.floor(m / 6 + 0.5) / 10:g} 小时"


def _kpi_cards(k, beh, recent, rng, series=None):
    """顶部统计小卡片（学习时长、活跃天数、训练次数、答题数、正确率、AI 提问），都随日期范围。
    delta = 较前一段同样长度时间的变化；正确率是比例，前一段答题不足 5 道时不给对比（避免样本太小的假涨跌）。
    good：变大是好事（up）、变小是好事（down）、无好坏（None）"""
    recent = recent or {}
    sess = beh.get("_sessions") or []
    s1 = sum(1 for x in sess if rng.since <= x["started_at"] < rng.until)
    s0 = sum(1 for x in sess if rng.prev_since <= x["started_at"] < rng.since)
    n1, n0 = recent.get("n", 0), recent.get("n_prev", 0)
    acc, acc0 = recent.get("acc"), recent.get("acc_prev")
    acc_delta = round(acc - acc0, 1) if acc is not None and acc0 is not None and n0 >= 5 else None
    ai1, ai0 = k["ai1"], k["ai0"]
    cards = [
        {"key": "study_time", "label": "学习时长", "value": _fmt_minutes(k["t1"]) if n1 else "—",
         "delta": round(k["t1"] / 60) - round(k["t0"] / 60), "unit": "分钟", "good": "up", "tip": "所选范围内每道题作答用时的合计，不含看题后没提交的时间"},
        {"key": "sessions", "label": "训练次数", "value": f"{s1} 次", "delta": s1 - s0, "unit": "次", "good": "up", "tip": "所选范围内开始的训练次数"},
        {"key": "answered", "label": "答题数", "value": f"{n1} 题", "delta": n1 - n0, "unit": "题", "good": "up", "tip": "所选范围内作答的题目数量"},
        {"key": "accuracy", "label": "正确率", "value": "—" if acc is None else f"{acc}%", "delta": acc_delta, "unit": "%", "good": "up",
         "tip": "所选范围内答对的题数 ÷ 作答题数；前一段答题不足 5 道时不显示对比"},
        {"key": "ai_asks", "label": "AI 提问", "value": f"{ai1} 次", "delta": ai1 - ai0 if ai1 + ai0 > 0 else None, "unit": "次", "good": "up",
         "tip": "向 AI 助手提问的消息条数"},
    ]
    for c in cards:
        c["series"] = (series or {}).get(c["key"], [])
    return cards


SUBJECT_ORDER = ["MATH", "PHYSICS", "CHEMISTRY"]


def _study_time_tips(stats, subj, types, tb, rng, wrong_pending):
    """学习时长维度的建议（最多 5 条）：每条都是能直接照着做的一句话，依据都来自上面的统计"""
    tips = []
    a = stats["avg_per_session"]
    if a is not None and a < 5:
        tips.append(f"每次训练平均只有 {a} 分钟，建议把零碎的几次合成一次 10～15 分钟的完整训练，更容易进入状态")
    elif a is not None and a > 40:
        tips.append(f"每次训练平均 {a} 分钟，偏长；建议每 25～30 分钟休息 5 分钟，再继续")
    wk, we = stats["weekday_avg"], stats["weekend_avg"]
    if wk and we and we / wk >= 1.8:
        tips.append(f"学习集中在周末（日均 {we} 分钟，工作日只有 {wk} 分钟）；建议把一部分挪到工作日，每天固定 10～15 分钟，比周末突击效果好")
    elif not we and wk and rng.days >= 7:
        tips.append("周末几乎没有学习记录，可以安排一次 20～30 分钟的复盘训练")
    best, avg = stats["best_day"], stats["avg_per_active_day"]
    if best and avg and stats["active_days"] >= 3 and best["minutes"] >= avg * 2:
        tips.append(f"{best['date'][5:].replace('-', '/')} 一天学了 {best['minutes']} 分钟，是平时的 {round(best['minutes'] / avg, 1)} 倍；建议把这部分量分摊到相邻几天，避免突击")
    need = max(2, rng.days * 4 // 7) if rng.days <= 14 else None
    if need and stats["active_days"] < need and stats["active_days"] > 0:
        tips.append(f"{rng.label}只有 {stats['active_days']} 天在学习，建议每周至少安排 4 天，哪怕每天只有 10 分钟")
    idle = [x["name"] for x in subj if x["code"] in SUBJECT_ORDER and x["minutes"] == 0]
    if idle and len(idle) < len(SUBJECT_ORDER):
        tips.append(f"{'、'.join(idle)}在{rng.label}内没有学习，建议每周至少安排 1～2 次，避免遗忘")
    night = next((b for b in tb if b["key"] == "night"), None)
    tot = sum(b["minutes"] for b in tb)
    if night and tot and night["minutes"] / tot >= 0.2:
        tips.append(f"深夜（22 点以后）学习占 {round(night['minutes'] / tot * 100)}%，建议把时间提前，保证睡眠；睡眠不足会拉低第二天的正确率")
    if types:
        top = max(types, key=lambda x: x["minutes"])
        if (top["share"] or 0) >= 70 and len(types) >= 1:
            tips.append(f"{top['share']:g}% 的时间用在「{top['label']}」，练习方式比较单一；可以穿插错题集和智能训练，覆盖更全面")
        err = next((x for x in types if x["key"] == "ERROR_QUESTIONS"), None)
        if wrong_pending >= 5 and (err is None or (err["share"] or 0) < 10):
            tips.append(f"还有 {wrong_pending} 道错题没有攻克，但错题集只占学习时间的 {0 if err is None else err['share']:g}%；建议每次训练前先花 5 分钟过一遍错题集")
    if not tips:
        tips.append("学习时间的节奏和分配都比较健康，继续保持")
    return tips[:5]


def _study_time_build(rows, subjects, rng, t1, t0, avg_session_sec, hour_rows=None, type_rows=None, wrong_pending=0, prev_best_sec=None, kp_rows=None):
    """学习时长明细（纯计算，方便测试）。rows：每天每个学科的 {d, sid, t(秒), n, c}；subjects：{id: (code, name)}。
    时长 = 每道题的作答用时之和（系统没有记录页面在线时长，这是最接近的口径）。
    prev_best_sec：前一段同样长度时间里，学得最久那一天的秒数（没有学习记录时传 None / 0），用来给「单日最长」做涨跌对比。
    kp_rows：每个学科下每个知识点的 {sid, kid, name, t(秒), n(答题数)}，用来出「知识点学习时长 Top5」。
    一道题挂了几个知识点，用时就各算一份（所以各知识点的时长相加会比总时长大，只用来排名）。"""
    names = {"MATH": "数学", "PHYSICS": "物理", "CHEMISTRY": "化学"}
    def code_of(sid):
        return subjects.get(sid, ("OTHER", "其他"))[0]
    def name_of(code):
        return names.get(code) or next((v[1] for v in subjects.values() if v[0] == code), "其他")
    per_day: dict[date, dict] = {}
    per_subj: dict[str, float] = {}
    for r in rows:
        c = code_of(r["sid"])
        d = per_day.setdefault(r["d"], {"t": 0.0, "n": 0, "c": 0, "by": {}})
        d["t"] += float(r["t"] or 0); d["n"] += r["n"]; d["c"] += r["c"]
        d["by"][c] = d["by"].get(c, 0.0) + float(r["t"] or 0)
        per_subj[c] = per_subj.get(c, 0.0) + float(r["t"] or 0)
    total = sum(per_subj.values())
    codes = [c for c in SUBJECT_ORDER] + sorted(c for c in per_subj if c not in SUBJECT_ORDER)
    # 趋势柱：按天 / 按周，从旧到新，每柱按学科堆叠（分钟）
    n = rng.points
    buckets = [{"label": rng.bucket_label(w), "by": {}} for w in range(n - 1, -1, -1)]
    for d, v in per_day.items():
        i = n - 1 - rng.bucket_of_date(d)
        if 0 <= i < n:
            for c, sec in v["by"].items():
                buckets[i]["by"][c] = buckets[i]["by"].get(c, 0) + sec / 60
    series = [{"label": b["label"], "minutes": {c: round(b["by"].get(c, 0), 1) for c in codes}, "total": round(sum(b["by"].values()), 1)} for b in buckets]
    subj = [{"code": c, "name": name_of(c), "minutes": round(per_subj.get(c, 0) / 60, 1), "share": _pct(per_subj.get(c, 0), total)} for c in codes]

    active = {d: v for d, v in per_day.items() if v["t"] > 0}
    avg_day = total / len(active) if active else None
    best = max(active.items(), key=lambda kv: kv[1]["t"]) if active else None
    # 周末 / 非周末日均 = 该类日子的学习总时长 ÷ 所选范围内该类日子的天数（没学习的天也算，分母不只是「有学习的天」）；
    # 范围里没有这类日子（比如只选了周一到周三）则为 None
    n_wd = sum(1 for i in range(rng.days) if (rng.start + timedelta(days=i)).weekday() < 5)
    n_we = rng.days - n_wd
    wk_total = sum(v["t"] for d, v in per_day.items() if d.weekday() < 5)
    we_total = sum(v["t"] for d, v in per_day.items() if d.weekday() >= 5)
    stats = {
        "total_minutes": round(total / 60, 1), "prev_minutes": round(t0 / 60, 1),
        "delta_pct": round((t1 - t0) / t0 * 100) if t0 and t0 >= 600 else None,     # 前一段不足 10 分钟，比例没意义
        "active_days": len(active), "avg_per_active_day": None if avg_day is None else round(avg_day / 60, 1),
        "best_day": None if not best else {"date": str(best[0]), "minutes": round(best[1]["t"] / 60, 1)},
        "prev_best_minutes": round(prev_best_sec / 60, 1) if prev_best_sec else None,     # 前一段的单日最长；前一段没学习则为 None（不做对比）
        "avg_per_session": None if not avg_session_sec else round(avg_session_sec / 60, 1),
        "weekday_avg": round(wk_total / n_wd / 60, 1) if n_wd else None, "weekend_avg": round(we_total / n_we / 60, 1) if n_we else None,
    }

    hl = []
    if total < 300:
        return {"has_data": False, "range_label": rng.label}
    top = max(subj, key=lambda x: x["minutes"])
    if top["share"] is not None and top["share"] >= 70 and sum(1 for x in subj if x["minutes"] > 0) >= 1:
        idle = [x["name"] for x in subj if x["code"] in SUBJECT_ORDER and x["minutes"] == 0]
        hl.append({"tone": "warn" if idle else "good", "text": f"{rng.label}的学习时间 {top['share']:g}% 花在{top['name']}上" + (f"，{'、'.join(idle)}完全没有学习" if idle else "")})
    elif top["share"] is not None:
        hl.append({"tone": "good", "text": f"时间分配比较均衡，{top['name']}占 {top['share']:g}%"})
    if stats["delta_pct"] is not None and abs(stats["delta_pct"]) >= 20:
        up = stats["delta_pct"] > 0
        hl.append({"tone": "good" if up else "warn", "text": f"总学习时长 {stats['total_minutes']} 分钟，比前一段{'增加' if up else '减少'} {abs(stats['delta_pct'])}%"})
    if best and avg_day and len(active) >= 3 and best[1]["t"] >= avg_day * 2:
        hl.append({"tone": "warn", "text": f"{best[0].month}/{best[0].day} 一天学了 {stats['best_day']['minutes']} 分钟，是平时（{stats['avg_per_active_day']} 分钟）的 {round(best[1]['t'] / avg_day, 1)} 倍，更像是集中突击而不是每天积累"})
    if stats["weekday_avg"] and stats["weekend_avg"]:
        ratio = stats["weekend_avg"] / stats["weekday_avg"]
        if ratio >= 1.8:
            hl.append({"tone": "warn", "text": f"周末日均 {stats['weekend_avg']} 分钟，是工作日（{stats['weekday_avg']} 分钟）的 {round(ratio, 1)} 倍，学习集中在周末"})
        elif ratio <= 0.5:
            hl.append({"tone": "good", "text": f"工作日日均 {stats['weekday_avg']} 分钟，周末反而少（{stats['weekend_avg']} 分钟），平时学习更稳定"})
    days_with_n = [(v["t"], v["c"] / v["n"] * 100, v["n"]) for v in active.values() if v["n"] >= 3]
    if len(days_with_n) >= 4:
        days_with_n.sort(key=lambda x: x[0])
        half = len(days_with_n) // 2
        lo, hi = days_with_n[:half], days_with_n[-half:]
        lo_acc = sum(a * n for _, a, n in lo) / sum(n for *_, n in lo)
        hi_acc = sum(a * n for _, a, n in hi) / sum(n for *_, n in hi)
        if abs(hi_acc - lo_acc) >= 8:
            hl.append({"tone": "good" if hi_acc > lo_acc else "warn",
                       "text": f"学得久的日子正确率 {round(hi_acc)}%，学得短的日子 {round(lo_acc)}%：" + ("时间投入和效果正相关，可以鼓励每次多学一会" if hi_acc > lo_acc else "学得越久反而错得越多，可能有疲劳，建议拆成多次短时训练")})
    if stats["avg_per_session"]:
        a = stats["avg_per_session"]
        if a < 5:
            hl.append({"tone": "warn", "text": f"每次训练平均只有 {a} 分钟，时间偏碎，难以进入状态"})
        elif a > 40:
            hl.append({"tone": "warn", "text": f"每次训练平均 {a} 分钟，偏长，注意中途休息"})
    # 练习方式（类型）时长：type_rows 是「学科 × 练习方式」的 {sid, dim, t(秒), n(训练次数)}。
    # types 是所有学科合起来的（建议里的规则在用），types_by_subject 是每个学科各自的分布（占比按这个学科自己的总时长算）。
    # 一次训练只属于一个学科，所以训练次数可以直接相加
    def type_dist(rs):
        m: dict[str, dict] = {}
        for r in rs:
            e = m.setdefault(r["dim"], {"t": 0.0, "n": 0})
            e["t"] += float(r["t"] or 0)
            e["n"] += int(r["n"] or 0)
        tot = sum(v["t"] for v in m.values())
        return [{"key": k, "label": DIM_LABELS.get(k, k), "minutes": round(m[k]["t"] / 60, 1), "sessions": m[k]["n"], "share": _pct(m[k]["t"], tot)} for k in DIM_ORDER if k in m]
    types = type_dist(type_rows or [])
    by_code: dict[str, list] = {}
    for r in type_rows or []:
        by_code.setdefault(code_of(r.get("sid")), []).append(r)
    types_by_subject = {c: type_dist(v) for c, v in by_code.items()}
    tb = []
    for key, label, lo, hi in TIME_BUCKETS:
        sec = sum(float(r["t"] or 0) for r in (hour_rows or []) if lo <= (r["h"] if r["h"] >= 6 else r["h"] + 24) < hi)
        tb.append({"key": key, "label": label, "range": f"{lo}–{min(hi, 24) if hi <= 24 else str(hi - 24) + '(次日)'}点", "minutes": round(sec / 60, 1)})
    # 知识点学习时长 Top5：按学科分组，每科取周期内用时最长的 5 个知识点（没记录用时的不上榜）
    kp_top: dict[str, list] = {}
    for r in kp_rows or []:
        if float(r["t"] or 0) <= 0:
            continue
        kp_top.setdefault(code_of(r["sid"]), []).append({"id": r["kid"], "name": r["name"], "minutes": round(float(r["t"]) / 60, 1), "answered": r["n"]})
    kp_top = {c: sorted(v, key=lambda x: (-x["minutes"], -x["answered"], x["id"]))[:5] for c, v in kp_top.items()}
    return {"has_data": True, "unit": "day" if rng.daily else "week", "time_buckets": tb, "types": types,
            "types_by_subject": types_by_subject,
            "tips": _study_time_tips(stats, subj, types, tb, rng, wrong_pending), "subjects": subj, "series": series, "stats": stats, "highlights": hl[:5],
            "kp_top": kp_top}


WEEKDAY_LABELS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def _sessions_build(rows, rng, wrong_pending=0, subjects=None, kp_rows=None):
    """训练次数明细（纯计算，方便测试）。
    rows：所选范围和前一段同样长度时间内开始的训练，每条 {started_at, session_status, training_dimension, total_questions, answered, correct}。
    口径说明：
    · 完成 = session_status 为 completed，其余（中途退出 / 提前结束 / 进行中）都算「未完成」；
    · 退出训练不保存（视为放弃）是正常流程，所以不用「完成次数 ÷ 总次数」衡量，而用「作答题数 ÷ 下发题数」（答题完成度）；
    · 日均 / 周末日均 / 非周末日均 都 ÷ 所选范围内对应的天数（没训练的天也算），和学习时长的口径一致；
    · 一次训练归到一个学科：取下发题目里数量最多的学科（实际数据里一次训练都是单科，没作答的训练也能从下发的题目判断）。
    rows 里的 subject_id 是这个学科的 id，subjects 是 {id: (code, name)}；对不上的归到「其他」。
    kp_rows：所选范围内每个学科下每个知识点被训练的次数 {sid, kid, name, n(训练次数), done(其中完成的)}，用来出「知识点训练次数 Top5」。
    一次训练算训练过某知识点 = 这次下发的题目里有题挂了它（一次训练里多道题涉及同一个知识点只算一次）。"""
    cur = [r for r in rows if rng.since <= r["started_at"] < rng.until]
    prv = [r for r in rows if rng.prev_since <= r["started_at"] < rng.since]
    n = len(cur)
    if n == 0:
        return {"has_data": False, "range_label": rng.label}
    day = lambda r: r["started_at"].astimezone(BJ).date()
    ans = lambda r: int(r["answered"] or 0)
    iss = lambda r: int(r["total_questions"] or 0)
    done = lambda r: r["session_status"] == "completed"

    per_day: dict[date, int] = {}
    for r in cur:
        per_day[day(r)] = per_day.get(day(r), 0) + 1
    prv_day: dict[date, int] = {}
    for r in prv:
        prv_day[day(r)] = prv_day.get(day(r), 0) + 1

    def completion(rs):
        issued = sum(iss(r) for r in rs)
        return _pct(sum(min(ans(r), iss(r)) if iss(r) else ans(r) for r in rs), issued) if issued >= 10 else None     # 下发不足 10 题，比例没意义

    def avg_answered(rs):
        a = [ans(r) for r in rs if ans(r) > 0]
        return round(sum(a) / len(a), 1) if a else None

    best = max(per_day.items(), key=lambda kv: (kv[1], kv[0]))            # 次数相同取最近的一天
    n_wd = sum(1 for i in range(rng.days) if (rng.start + timedelta(days=i)).weekday() < 5)
    n_we = rng.days - n_wd
    wk_n = sum(c for d, c in per_day.items() if d.weekday() < 5)
    we_n = sum(c for d, c in per_day.items() if d.weekday() >= 5)
    gap = run = 0                                                       # 范围内最长连续没训练的天数
    for i in range(rng.days):
        run = 0 if (rng.start + timedelta(days=i)) in per_day else run + 1
        gap = max(gap, run)
    full = sum(1 for r in cur if iss(r) and ans(r) >= iss(r))
    none = sum(1 for r in cur if ans(r) == 0)
    stats = {
        "total": n, "prev_total": len(prv), "days": rng.days, "active_days": len(per_day), "done": sum(1 for r in cur if done(r)),
        "avg_per_day": round(n / rng.days, 1), "prev_avg_per_day": round(len(prv) / rng.days, 1) if prv else None,
        "best_day": {"date": str(best[0]), "count": best[1]}, "prev_best_count": max(prv_day.values()) if prv_day else None,
        "completion": completion(cur), "prev_completion": completion(prv),
        "avg_answered": avg_answered(cur), "prev_avg_answered": avg_answered(prv),
        "weekday_avg": round(wk_n / n_wd, 1) if n_wd else None, "weekend_avg": round(we_n / n_we, 1) if n_we else None,
        "max_gap_days": gap,
        "completeness": {"full": full, "partial": n - full - none, "none": none},       # 全部作答 / 作答一部分 / 一题没答
    }

    # 学科：一次训练归到一个学科
    subjects = subjects or {}
    names = {"MATH": "数学", "PHYSICS": "物理", "CHEMISTRY": "化学"}
    code_of = lambda r: subjects.get(r.get("subject_id"), ("OTHER", "其他"))[0]
    per_subj: dict[str, int] = {}
    for r in cur:
        per_subj[code_of(r)] = per_subj.get(code_of(r), 0) + 1
    codes = list(SUBJECT_ORDER) + sorted(c for c in per_subj if c not in SUBJECT_ORDER)
    name_of = lambda c: names.get(c) or next((v[1] for v in subjects.values() if v[0] == c), "其他")
    subj = [{"code": c, "name": name_of(c), "count": per_subj.get(c, 0), "share": _pct(per_subj.get(c, 0), n)} for c in codes]

    # 趋势：按天 / 按周，从旧到新，每个点按学科拆分（同时保留完成 / 未完成）
    pts = rng.points
    buckets = [{"label": rng.bucket_label(w), "done": 0, "undone": 0, "by_subject": {c: 0 for c in codes}} for w in range(pts - 1, -1, -1)]
    for r in cur:
        i = pts - 1 - rng.bucket_of_date(day(r))
        if 0 <= i < pts:
            buckets[i]["done" if done(r) else "undone"] += 1
            buckets[i]["by_subject"][code_of(r)] += 1
    series = [{**b, "total": b["done"] + b["undone"]} for b in buckets]

    # 练习方式：次数、占比、做完的比例（顺序同小程序「练习方式」）
    def type_dist(rs):                                    # 占比按这组训练自己的总数算
        by_dim: dict[str, list] = {}
        for r in rs:
            by_dim.setdefault(r["training_dimension"], []).append(r)
        keys = [k for k in DIM_ORDER if k in by_dim] + sorted(k for k in by_dim if k not in DIM_ORDER)
        return [{"key": k, "label": DIM_LABELS.get(k, k), "count": len(by_dim[k]), "share": _pct(len(by_dim[k]), len(rs)),
                 "done_rate": _pct(sum(1 for r in by_dim[k] if done(r)), len(by_dim[k]))} for k in keys]
    types = type_dist(cur)
    types_by_subject = {c: type_dist([r for r in cur if code_of(r) == c]) for c in per_subj}      # 每个学科各自的分布（占比按这个学科自己的训练数算）

    # 知识点训练次数 Top5：按学科分组，每科取周期内被训练次数最多的 5 个知识点
    kp_top: dict[str, list] = {}
    for r in kp_rows or []:
        if int(r["n"] or 0) <= 0:
            continue
        kp_top.setdefault(code_of({"subject_id": r["sid"]}), []).append({"id": r["kid"], "name": r["name"], "count": int(r["n"]), "done": int(r["done"] or 0)})
    kp_top = {c: sorted(v, key=lambda x: (-x["count"], -x["done"], x["id"]))[:5] for c, v in kp_top.items()}

    # 洞察（最多 5 条）：每条都是能直接照着做的一句话
    tips = []
    if none >= 2 and none / n >= 0.2:
        tips.append(f"{none} 次训练一题都没答就退出了（占 {round(none / n * 100)}%），建议点开后先做第一题，别只是看看就退出")
    partial = n - full - none
    if partial >= 3 and partial / n >= 0.25:
        tips.append(f"{partial} 次训练只做了一部分就退出（占 {round(partial / n * 100)}%）；每次把下发的题做完再退出，答题完成度才上得去")
    need = max(2, rng.days * 4 // 7) if rng.days <= 14 else None
    if need and 0 < len(per_day) < need:
        tips.append(f"{rng.label}只有 {len(per_day)} 天在训练（共 {rng.days} 天），建议每周至少 4 天，哪怕每天只做一组")
    avg_active = n / len(per_day)
    if len(per_day) >= 3 and best[1] >= 3 and best[1] >= avg_active * 2:
        tips.append(f"{best[0].month}/{best[0].day} 一天训练 {best[1]} 次，是有训练那几天平均（{round(avg_active, 1)} 次）的 {round(best[1] / avg_active, 1)} 倍；建议分摊到相邻几天，避免突击")
    wk, we = stats["weekday_avg"], stats["weekend_avg"]
    if wk and we and we / wk >= 1.8:
        tips.append(f"训练集中在周末（周末日均 {we} 次，非周末只有 {wk} 次）；建议每天固定一组，比周末突击效果好")
    elif not we and wk and rng.days >= 7:
        tips.append("周末没有训练记录，可以安排一次复盘训练")
    if gap >= 3 and rng.days >= 7:
        tips.append(f"中间连续 {gap} 天没有训练，间隔太久容易遗忘，建议至少隔天安排一组")
    top = max(types, key=lambda x: x["count"])
    if (top["share"] or 0) >= 70 and n >= 5:
        tips.append(f"{top['share']:g}% 的训练用的是「{top['label']}」，方式比较单一；可以穿插错题集和智能训练")
    err = next((x for x in types if x["key"] == "ERROR_QUESTIONS"), None)
    if wrong_pending >= 5 and (err is None or (err["share"] or 0) < 10):
        tips.append(f"还有 {wrong_pending} 道错题没有攻克，但错题集训练只占 {0 if err is None else err['share']:g}%（{0 if err is None else err['count']} 次）；建议每次训练前先做一组错题集")
    low = [x for x in types if x["count"] >= 4 and x["done_rate"] is not None and stats["done"] / n * 100 - x["done_rate"] >= 25]
    if low:
        w = min(low, key=lambda x: x["done_rate"])
        tips.append(f"「{w['label']}」训练只有 {w['done_rate']:g}% 做完了，明显低于整体（{_pct(stats['done'], n):g}%）；可能题量或难度不合适，值得留意")
    night = sum(1 for r in cur if r["started_at"].astimezone(BJ).hour >= 22 or r["started_at"].astimezone(BJ).hour < 6)
    if n >= 5 and night / n >= 0.2:
        tips.append(f"深夜（22 点以后）开始的训练占 {round(night / n * 100)}%，建议把时间提前，保证睡眠")
    if not tips:
        tips.append("训练的频率和完成度都比较健康，继续保持")
    return {"has_data": True, "unit": "day" if rng.daily else "week", "stats": stats, "subjects": subj, "series": series, "types": types, "types_by_subject": types_by_subject, "kp_top": kp_top, "tips": tips[:5]}


async def _sessions_stats(db, sid, rng, wrong_pending=0):
    """训练次数明细：所选范围和前一段同样长度时间内开始的训练，每条带上实际作答题数 / 答对题数"""
    rows = await _rows(db, """
        SELECT s.started_at, s.session_status, s.training_dimension, s.total_questions, subj.sid subject_id,
               count(a.id) answered, count(a.id) FILTER (WHERE a.is_correct) correct
        FROM training_sessions s
        LEFT JOIN training_answer_records a ON a.session_id = s.id AND COALESCE(a.is_seed_data, false) = false
        -- 这次训练的学科：下发的题目（快照里的 question_ids）里数量最多的学科。没作答的训练也能判断
        LEFT JOIN LATERAL (
            SELECT q.subject_id sid
            FROM jsonb_array_elements_text(CASE WHEN jsonb_typeof(s.question_snapshot->'question_ids') = 'array' THEN s.question_snapshot->'question_ids' ELSE '[]'::jsonb END) e(qid)
            JOIN questions q ON q.id = (CASE WHEN e.qid ~ '^[0-9]+$' THEN e.qid::bigint END)
            WHERE q.subject_id IS NOT NULL GROUP BY q.subject_id ORDER BY count(*) DESC, q.subject_id LIMIT 1
        ) subj ON true
        WHERE s.student_id = :sid AND s.started_at >= :prev AND s.started_at < :until
        GROUP BY s.id, subj.sid""", sid=sid, prev=rng.prev_since, **rng.params)
    subs = {r["id"]: (r["code"], r["name"]) for r in await _rows(db, "SELECT id, code, name FROM subjects")}
    # 知识点训练次数：下发的题目（快照里的 question_ids）挂的知识点；一次训练里同一个知识点只算一次
    kp_rows = await _rows(db, """
        SELECT q.subject_id sid, kp.id kid, kp.name, count(DISTINCT s.id) n, count(DISTINCT s.id) FILTER (WHERE s.session_status = 'completed') done
        FROM training_sessions s
        CROSS JOIN LATERAL jsonb_array_elements_text(CASE WHEN jsonb_typeof(s.question_snapshot->'question_ids') = 'array' THEN s.question_snapshot->'question_ids' ELSE '[]'::jsonb END) e(qid)
        JOIN questions q ON q.id = (CASE WHEN e.qid ~ '^[0-9]+$' THEN e.qid::bigint END)
        CROSS JOIN LATERAL jsonb_array_elements_text(q.knowledge_point_ids) k(kid)
        JOIN knowledge_points kp ON kp.id = (CASE WHEN k.kid ~ '^[0-9]+$' THEN k.kid::bigint END)
        WHERE s.student_id = :sid AND s.started_at >= :since AND s.started_at < :until
        GROUP BY 1, 2, 3""", sid=sid, **rng.params)
    return _sessions_build(rows, rng, wrong_pending, subs, kp_rows)


def _answer_dist(cube, field, labels, code_of, codes):
    """按学科输出「题型 / 难度」分布：每个有答题的学科一份，固定输出全部档位（没做过的是 0）。
    cube 里每行 {sid, qt, df, n(答题数), c(答对数)}；field 是 qt（题型）或 df（难度）；labels 是 {key: 名称}（决定档位和顺序）"""
    out: dict[str, list] = {}
    for c in codes:
        rs = [r for r in cube if code_of(r["sid"]) == c and r[field]]
        tot = sum(int(r["n"] or 0) for r in rs)
        row = lambda k: [r for r in rs if r[field] == k]
        out[c] = [{"key": k, "label": lb, "count": sum(int(r["n"] or 0) for r in row(k)), "correct": sum(int(r["c"] or 0) for r in row(k)),
                   "accuracy": _pct(sum(int(r["c"] or 0) for r in row(k)), sum(int(r["n"] or 0) for r in row(k))),
                   "share": _pct(sum(int(r["n"] or 0) for r in row(k)), tot)} for k, lb in labels.items()]
    return out


def _answers_build(cube, subjects, prev_total, wrong_rows, stubborn_rows, fav_rows, kp_rows):
    """答题数明细（纯计算，方便测试）。
    cube：所选范围内「学科 × 题型 × 难度」的 {sid, qt, df, n(答题数), c(答对数)}；
    wrong_rows：错题 {sid, k(review_status), n}；stubborn_rows：顽固错题（同一道题错 3 次以上）{sid, n}；fav_rows：收藏 {sid, n}；
    kp_rows：所选范围内每个学科下每个知识点的 {sid, kid, name, n, c}；prev_total：前一段同样长度时间的答题数。
    错题 / 顽固错题 / 收藏是「当前状态」，不随日期范围变；答题数、题型、难度、知识点都是所选范围内的。
    待攻克 = review_status 为 unreview，已攻克 = aha_achieved。"""
    subjects = subjects or {}
    names = {"MATH": "数学", "PHYSICS": "物理", "CHEMISTRY": "化学"}
    code_of = lambda sid: subjects.get(sid, ("OTHER", "其他"))[0]
    name_of = lambda c: names.get(c) or next((v[1] for v in subjects.values() if v[0] == c), "其他")
    n = lambda r: int(r["n"] or 0)

    total = sum(n(r) for r in cube)
    correct = sum(int(r["c"] or 0) for r in cube)
    per: dict[str, list[int]] = {}                                      # 学科 -> [答题数, 答对数]
    for r in cube:
        e = per.setdefault(code_of(r["sid"]), [0, 0])
        e[0] += n(r)
        e[1] += int(r["c"] or 0)
    wrong_codes = {code_of(r["sid"]) for r in wrong_rows} | {code_of(r["sid"]) for r in stubborn_rows} | {code_of(r["sid"]) for r in fav_rows}
    codes = list(SUBJECT_ORDER) + sorted(c for c in (set(per) | wrong_codes) if c not in SUBJECT_ORDER)
    subj = [{"code": c, "name": name_of(c), "count": per.get(c, [0, 0])[0], "correct": per.get(c, [0, 0])[1],
             "accuracy": _pct(per.get(c, [0, 0])[1], per.get(c, [0, 0])[0]), "share": _pct(per.get(c, [0, 0])[0], total)} for c in codes]

    # 错题 / 顽固错题 / 收藏：总数 + 每个学科的数量（卡片悬停时看）
    bd = {c: {"pending": 0, "mastered": 0, "stubborn": 0, "favorites": 0} for c in codes}
    for r in wrong_rows:
        key = {"unreview": "pending", "aha_achieved": "mastered"}.get(r["k"])
        if key:
            bd[code_of(r["sid"])][key] += n(r)
    for r in stubborn_rows:
        bd[code_of(r["sid"])]["stubborn"] += n(r)
    for r in fav_rows:
        bd[code_of(r["sid"])]["favorites"] += n(r)
    pending, mastered = sum(v["pending"] for v in bd.values()), sum(v["mastered"] for v in bd.values())
    stubborn, fav = sum(v["stubborn"] for v in bd.values()), sum(v["favorites"] for v in bd.values())
    stats = {"total": total, "prev_total": prev_total, "correct": correct, "accuracy": _pct(correct, total),
             "wrong_pending": pending, "wrong_mastered": mastered, "mastered_rate": _pct(mastered, pending + mastered),
             "stubborn": stubborn, "favorites": fav, "breakdown": bd}

    # 题型 / 难度分布：按学科，固定输出全部题型 / 全部难度（没做过的是 0，看得出「没做过挑战题」）
    types_by_subject = _answer_dist(cube, "qt", TYPE_LABELS, code_of, per)
    difficulty_by_subject = _answer_dist(cube, "df", DIFF_LABELS, code_of, per)

    # 知识点答题数 Top5：按学科，答题数多的在前（并列答对多的在前）
    kp_top: dict[str, list] = {}
    for r in kp_rows:
        if n(r) > 0:
            kp_top.setdefault(code_of(r["sid"]), []).append({"id": r["kid"], "name": r["name"], "count": n(r), "correct": int(r["c"] or 0),
                                                              "accuracy": _pct(int(r["c"] or 0), n(r))})
    kp_top = {c: sorted(v, key=lambda x: (-x["count"], -x["correct"], x["id"]))[:5] for c, v in kp_top.items()}

    # 总结（最多 5 条）：每条都是能直接照着做的一句话
    tips = []
    if pending >= 5:
        tips.append(f"还有 {pending} 道错题没攻克（已攻克 {mastered} 道，攻克率 {stats['mastered_rate']:g}%），建议每周做一组错题集")
    elif pending == 0 and mastered > 0:
        tips.append(f"错题已全部攻克（共 {mastered} 道），继续保持")
    if stubborn >= 1:
        tips.append(f"有 {stubborn} 道顽固错题（同一道题错 3 次以上），需要讲解或换个思路")
    main = [x for x in subj if x["code"] in SUBJECT_ORDER]
    if total >= 20 and main:
        top = max(main, key=lambda x: x["count"])
        rest = [x for x in main if x is not top]
        if (top["share"] or 0) >= 70 and rest:
            tips.append(f"{top['name']}占 {top['share']:g}%（{top['count']} 题），" + "、".join(f"{x['name']} {x['count']} 题" for x in rest) + "，建议各科均衡")
    ok = [x for x in main if x["count"] >= 10 and x["accuracy"] is not None]
    if len(ok) >= 2:
        lo, hi = min(ok, key=lambda x: x["accuracy"]), max(ok, key=lambda x: x["accuracy"])
        if hi["accuracy"] - lo["accuracy"] >= 20:
            tips.append(f"「{lo['name']}」正确率 {lo['accuracy']:g}%，比「{hi['name']}」（{hi['accuracy']:g}%）低 {round(hi['accuracy'] - lo['accuracy'])} 个百分点，最需要补")
    # 题型短板：所有学科合起来，答得够多的题型里正确率最低、且明显低于整体
    by_type: dict[str, list[int]] = {}
    for r in cube:
        if r["qt"]:
            e = by_type.setdefault(r["qt"], [0, 0])
            e[0] += n(r)
            e[1] += int(r["c"] or 0)
    overall = _pct(correct, total)
    weak = [(k, v) for k, v in by_type.items() if v[0] >= 10 and overall is not None and _pct(v[1], v[0]) is not None and overall - _pct(v[1], v[0]) >= 15]
    if weak:
        k, v = min(weak, key=lambda kv: _pct(kv[1][1], kv[1][0]))
        tips.append(f"「{TYPE_LABELS.get(k, k)}」正确率仅 {_pct(v[1], v[0]):g}%（{v[0]} 题），低于整体（{overall:g}%），值得专项练")
    # 难度结构：基本都是基础题
    by_diff = {k: sum(n(r) for r in cube if r["df"] == k) for k in DIFF_LABELS}
    hard = by_diff["advanced"] + by_diff["challenge"]
    if total >= 30 and sum(by_diff.values()) and hard / sum(by_diff.values()) < 0.1:
        tips.append(f"{round(by_diff['basic'] / sum(by_diff.values()) * 100)}% 是基础题，进阶以上仅 {hard} 题，基础稳了可逐步加进阶题")
    # 知识点集中
    allkp: dict[int, list] = {}
    for r in kp_rows:
        e = allkp.setdefault(r["kid"], [r["name"], 0])
        e[1] += n(r)
    if allkp and total >= 30:
        kid, (nm, c) = max(allkp.items(), key=lambda kv: kv[1][1])
        if c / total >= 0.3:
            tips.append(f"「{nm}」答了 {c} 题（占 {round(c / total * 100)}%），可以分散到更多知识点")
    # 答题量变化
    if prev_total >= 10 and total <= prev_total * 0.5:
        tips.append(f"答题量比前一段（{prev_total} 题）减少了 {round((1 - total / prev_total) * 100)}%，节奏慢下来了")
    if fav >= 5:
        tips.append(f"收藏了 {fav} 道题，可以抽时间回头再做一遍")
    if not tips:
        tips.append("答题的覆盖和质量都比较均衡，继续保持")
    return {"has_data": total > 0, "stats": stats, "subjects": subj, "types_by_subject": types_by_subject, "difficulty_by_subject": difficulty_by_subject,
            "kp_top": kp_top, "tips": tips[:5]}


async def _answers_stats(db, sid, rng):
    """答题数明细：所选范围内的答题按「学科 × 题型 × 难度」汇总，加上错题 / 顽固错题 / 收藏 / 知识点 Top5"""
    cube = await _rows(db, f"""
        SELECT q.subject_id sid, q.question_type qt, q.difficulty df, count(*) n, count(*) FILTER (WHERE a.is_correct) c
        {_base(True)} GROUP BY 1, 2, 3""", sid=sid, **rng.params)
    prev = await _one(db, f"SELECT count(*) n {_BASE} AND a.answered_at >= :prev AND a.answered_at < :since", sid=sid, prev=rng.prev_since, since=rng.since)
    wrong = await _rows(db, """
        SELECT q.subject_id sid, w.review_status k, count(*) n FROM wrong_answer_records w JOIN questions q ON q.id = w.question_id
        WHERE w.student_id = :sid GROUP BY 1, 2""", sid=sid)
    stubborn = await _rows(db, f"""
        SELECT x.sid, count(*) n FROM (SELECT q.subject_id sid, a.question_id {_BASE} AND NOT a.is_correct GROUP BY 1, 2 HAVING count(*) >= 3) x GROUP BY 1""", sid=sid)
    fav = await _rows(db, """
        SELECT q.subject_id sid, count(*) n FROM question_favorites f JOIN questions q ON q.id = f.question_id WHERE f.student_id = :sid GROUP BY 1""", sid=sid)
    kp_rows = await _rows(db, """
        SELECT q.subject_id sid, kp.id kid, kp.name, count(*) n, count(*) FILTER (WHERE a.is_correct) c
        FROM training_answer_records a
        JOIN training_sessions s ON s.id = a.session_id
        JOIN questions q ON q.id = a.question_id
        CROSS JOIN LATERAL jsonb_array_elements_text(q.knowledge_point_ids) k(kid)
        JOIN knowledge_points kp ON kp.id = (CASE WHEN k.kid ~ '^[0-9]+$' THEN k.kid::bigint END)
        WHERE s.student_id = :sid AND COALESCE(a.is_seed_data, false) = false AND a.answered_at >= :since AND a.answered_at < :until
        GROUP BY 1, 2, 3""", sid=sid, **rng.params)
    subs = {r["id"]: (r["code"], r["name"]) for r in await _rows(db, "SELECT id, code, name FROM subjects")}
    return _answers_build(cube, subs, prev["n"] if prev else 0, wrong, stubborn, fav, kp_rows)


def _accuracy_build(cube, subjects, prev, causes, kp_rows, semester, trend_rows=None, rng=None, kp_meta=None):
    """正确率明细（纯计算，方便测试）。口径和「学业掌握」标签页一致，但都限定在所选日期范围内，并且按学科拆开。
    cube：「学科 × 题型 × 难度」的 {sid, qt, df, n, c}；prev：前一段同样长度时间的 {n, c}；
    causes：错因构成 {wrong, blank(没作答), rush(秒答)}，认真做仍错 = 错题 − 没作答 − 秒答；
    kp_rows：每个学科下每个知识点 {sid, kid, name, n, c, b(没作答的错题), r(秒答的错题)}；semester：当前学期进度 {practiced, total, rate}；
    trend_rows + rng：趋势用，每个点（按天 / 按周）每个学科的 {w(0 = 最近一天 / 最后一周), sid, n, c}；
    kp_meta：{知识点 id: {trend(走向 up / flat / down), root_kp(可能的前置知识点)}}，和「学业掌握」标签页同一套（那边按全部历史算），给薄弱知识点表格用。
    趋势里某个点答题太少（按天 < 2 题、按周 < 3 题）正确率给 None，不画（样本太小的正确率没意义）。
    薄弱知识点 = 做过 2 次以上、错误率 ≥ 40%；强项 = 做过 2 次以上、错误率 < 40%。"""
    subjects = subjects or {}
    names = {"MATH": "数学", "PHYSICS": "物理", "CHEMISTRY": "化学"}
    code_of = lambda sid: subjects.get(sid, ("OTHER", "其他"))[0]
    name_of = lambda c: names.get(c) or next((v[1] for v in subjects.values() if v[0] == c), "其他")
    n = lambda r: int(r["n"] or 0)
    total = sum(n(r) for r in cube)
    correct = sum(int(r["c"] or 0) for r in cube)
    per: dict[str, list[int]] = {}
    for r in cube:
        e = per.setdefault(code_of(r["sid"]), [0, 0])
        e[0] += n(r)
        e[1] += int(r["c"] or 0)
    codes = list(SUBJECT_ORDER) + sorted(c for c in per if c not in SUBJECT_ORDER)
    subj = [{"code": c, "name": name_of(c), "count": per.get(c, [0, 0])[0], "correct": per.get(c, [0, 0])[1],
             "accuracy": _pct(per.get(c, [0, 0])[1], per.get(c, [0, 0])[0])} for c in codes]
    types_by_subject = _answer_dist(cube, "qt", TYPE_LABELS, code_of, per)
    difficulty_by_subject = _answer_dist(cube, "df", DIFF_LABELS, code_of, per)

    # 知识点：薄弱（错误率 ≥ 40%）/ 强项（错误率 < 40%），每个学科各取 5 个；错因 = 没作答 / 秒答 / 认真做仍错
    kps: dict[str, list] = {}
    for r in kp_rows:
        if n(r) < 2:
            continue
        c_ok, wrong = int(r["c"] or 0), n(r) - int(r["c"] or 0)
        blank, rush = min(int(r.get("b") or 0), wrong), int(r.get("r") or 0)
        kps.setdefault(code_of(r["sid"]), []).append({
            "id": r["kid"], "name": r["name"], "count": n(r), "correct": c_ok, "accuracy": _pct(c_ok, n(r)), "error_rate": _pct(wrong, n(r)),
            "wrong": wrong, "blank": blank, "rush": min(rush, wrong - blank), "thoughtful": max(0, wrong - blank - rush),
            "trend": (kp_meta or {}).get(r["kid"], {}).get("trend"), "root_kp": (kp_meta or {}).get(r["kid"], {}).get("root_kp")})
    weak_all = [x for v in kps.values() for x in v if (x["error_rate"] or 0) >= 40]
    strong_all = [x for v in kps.values() for x in v if (x["error_rate"] or 0) < 40]
    weak_by_subject = {c: sorted([x for x in v if (x["error_rate"] or 0) >= 40], key=lambda x: (-x["error_rate"], -x["wrong"], x["id"]))[:5] for c, v in kps.items()}
    strong_by_subject = {c: sorted([x for x in v if (x["error_rate"] or 0) < 40], key=lambda x: (x["error_rate"], -x["count"], x["id"]))[:5] for c, v in kps.items()}

    wrong = int(causes.get("wrong") or 0) if causes else 0
    blank, rush = int(causes.get("blank") or 0), int(causes.get("rush") or 0)
    acc, prev_acc = _pct(correct, total), (_pct(int(prev["c"] or 0), int(prev["n"] or 0)) if prev and int(prev["n"] or 0) >= 10 else None)
    stats = {"total": total, "correct": correct, "wrong": total - correct, "accuracy": acc, "prev_accuracy": prev_acc, "prev_total": int(prev["n"] or 0) if prev else 0, "prev_correct": int(prev["c"] or 0) if prev_acc is not None else None,
             "weak_kps": len(weak_all), "strong_kps": len(strong_all), "semester": semester or {"practiced": 0, "total": 0, "rate": None},
             "causes": {"wrong": wrong, "blank": blank, "rush": rush, "thoughtful": max(0, wrong - blank - rush)}}

    # 总结（最多 5 条）：每条尽量一行放下
    tips = []
    if acc is not None:
        if prev_acc is not None and abs(acc - prev_acc) >= 3:
            tips.append(f"整体正确率 {acc:g}%，比前一段{'提高' if acc > prev_acc else '下降'}了 {abs(round(acc - prev_acc, 1)):g} 个百分点")
        else:
            tips.append(f"整体正确率 {acc:g}%（共 {total} 题）" + ("，和前一段差不多" if prev_acc is not None else ""))
    if wrong >= 10:
        if blank / wrong >= 0.2:
            tips.append(f"{blank} 道错题是没作答（占错题 {round(blank / wrong * 100)}%），先把题做完比做对更重要")
        elif rush / wrong >= 0.3:
            tips.append(f"{rush} 道错题是 {RUSH_SECONDS} 秒内秒答（占 {round(rush / wrong * 100)}%），建议放慢审题")
        elif (wrong - blank - rush) / wrong >= 0.5:
            tips.append(f"{round((wrong - blank - rush) / wrong * 100)}% 的错题是认真做了仍错，是知识点没吃透，需要讲解")
    if weak_all:
        w = max(weak_all, key=lambda x: (x["error_rate"], x["wrong"]))
        tips.append(f"{len(weak_all)} 个知识点错误率超过 40%，最薄弱是「{w['name']}」（{w['error_rate']:g}%）")
    ok = [x for x in subj if x["code"] in SUBJECT_ORDER and x["count"] >= 10 and x["accuracy"] is not None]
    if len(ok) >= 2:
        lo, hi = min(ok, key=lambda x: x["accuracy"]), max(ok, key=lambda x: x["accuracy"])
        if hi["accuracy"] - lo["accuracy"] >= 20:
            tips.append(f"「{lo['name']}」正确率 {lo['accuracy']:g}%，比「{hi['name']}」（{hi['accuracy']:g}%）低 {round(hi['accuracy'] - lo['accuracy'])} 个百分点，最需要补")
    by_type: dict[str, list[int]] = {}
    for r in cube:
        if r["qt"]:
            e = by_type.setdefault(r["qt"], [0, 0])
            e[0] += n(r)
            e[1] += int(r["c"] or 0)
    low = [(k, v) for k, v in by_type.items() if v[0] >= 10 and acc is not None and _pct(v[1], v[0]) is not None and acc - _pct(v[1], v[0]) >= 15]
    if low:
        k, v = min(low, key=lambda kv: _pct(kv[1][1], kv[1][0]))
        tips.append(f"「{TYPE_LABELS.get(k, k)}」正确率仅 {_pct(v[1], v[0]):g}%（{v[0]} 题），低于整体，值得专项练")
    by_diff = {k: [sum(n(r) for r in cube if r["df"] == k), sum(int(r["c"] or 0) for r in cube if r["df"] == k)] for k in DIFF_LABELS}
    b_acc, a_acc = _pct(by_diff["basic"][1], by_diff["basic"][0]), _pct(by_diff["advanced"][1], by_diff["advanced"][0])
    if by_diff["basic"][0] >= 20 and b_acc is not None and b_acc < 60:
        tips.append(f"基础题正确率只有 {b_acc:g}%，先把基础题做稳，再往进阶走")
    elif by_diff["advanced"][0] >= 10 and a_acc is not None and b_acc is not None and b_acc - a_acc >= 20:
        tips.append(f"进阶题正确率 {a_acc:g}%，比基础题（{b_acc:g}%）低 {round(b_acc - a_acc)} 个百分点")
    sem = stats["semester"]
    if sem.get("total") and (sem.get("rate") or 0) < 30:
        tips.append(f"当前学期只练过 {sem['practiced']}/{sem['total']} 个知识点（{sem['rate']:g}%），可以多覆盖一些")
    if strong_all:
        g = min(strong_all, key=lambda x: (x["error_rate"], -x["count"]))
        tips.append(f"强项是「{g['name']}」（正确率 {g['accuracy']:g}%），可以适当加难")
    if not tips:
        tips.append("正确率整体稳定，继续保持")
    # 正确率趋势：从旧到新，每个点有整体正确率和各学科正确率
    trend = None
    if rng is not None:
        pts, min_n = rng.points, (2 if rng.daily else 3)
        buckets = [{"label": rng.bucket_label(w), "n": 0, "c": 0, "by": {c: [0, 0] for c in codes}} for w in range(pts - 1, -1, -1)]
        for r in trend_rows or []:
            i = pts - 1 - int(r["w"])
            if 0 <= i < pts:
                b = buckets[i]
                b["n"] += n(r)
                b["c"] += int(r["c"] or 0)
                if code_of(r["sid"]) in b["by"]:
                    b["by"][code_of(r["sid"])][0] += n(r)
                    b["by"][code_of(r["sid"])][1] += int(r["c"] or 0)
        trend = {"unit": "day" if rng.daily else "week", "series": [
            {"label": b["label"], "count": b["n"], "accuracy": _pct(b["c"], b["n"]) if b["n"] >= min_n else None,
             "by_subject": {c: {"count": v[0], "accuracy": _pct(v[1], v[0]) if v[0] >= min_n else None} for c, v in b["by"].items()}} for b in buckets]}
    return {"has_data": total > 0, "stats": stats, "subjects": subj, "trend": trend, "types_by_subject": types_by_subject, "difficulty_by_subject": difficulty_by_subject,
            "weak_by_subject": weak_by_subject, "strong_by_subject": strong_by_subject, "tips": tips[:5]}


async def _accuracy_stats(db, sid, rng, semester=None):
    """正确率明细：所选范围内的答题按「学科 × 题型 × 难度」汇总，加上前一段的对比、错因构成、每个学科的薄弱 / 强项知识点"""
    blank_sql = "coalesce(btrim(a.student_answer), '') = ''"
    cube = await _rows(db, f"""
        SELECT q.subject_id sid, q.question_type qt, q.difficulty df, count(*) n, count(*) FILTER (WHERE a.is_correct) c
        {_base(True)} GROUP BY 1, 2, 3""", sid=sid, **rng.params)
    prev = await _one(db, f"SELECT count(*) n, count(*) FILTER (WHERE a.is_correct) c {_BASE} AND a.answered_at >= :prev AND a.answered_at < :since", sid=sid, prev=rng.prev_since, since=rng.since)
    causes = await _one(db, f"""
        SELECT count(*) FILTER (WHERE NOT a.is_correct) wrong, count(*) FILTER (WHERE NOT a.is_correct AND {blank_sql}) blank,
               count(*) FILTER (WHERE NOT a.is_correct AND NOT ({blank_sql}) AND a.time_spent_sec <= :rush) rush
        {_base(True)}""", sid=sid, rush=RUSH_SECONDS, **rng.params)
    kp_rows = await _rows(db, f"""
        SELECT q.subject_id sid, kp.id kid, kp.name, count(*) n, count(*) FILTER (WHERE a.is_correct) c,
               count(*) FILTER (WHERE NOT a.is_correct AND {blank_sql}) b,
               count(*) FILTER (WHERE NOT a.is_correct AND NOT ({blank_sql}) AND a.time_spent_sec <= :rush) r
        FROM training_answer_records a
        JOIN training_sessions s ON s.id = a.session_id
        JOIN questions q ON q.id = a.question_id
        CROSS JOIN LATERAL jsonb_array_elements_text(q.knowledge_point_ids) k(kid)
        JOIN knowledge_points kp ON kp.id = (CASE WHEN k.kid ~ '^[0-9]+$' THEN k.kid::bigint END)
        WHERE s.student_id = :sid AND COALESCE(a.is_seed_data, false) = false AND a.answered_at >= :since AND a.answered_at < :until
        GROUP BY 1, 2, 3""", sid=sid, rush=RUSH_SECONDS, **rng.params)
    trend_rows = await _rows(db, f"""
        SELECT {rng.bucket_sql()} w, q.subject_id sid, count(*) n, count(*) FILTER (WHERE a.is_correct) c
        {_base(True)} GROUP BY 1, 2""", sid=sid, **rng.bucket_params, **rng.params)
    subs = {r["id"]: (r["code"], r["name"]) for r in await _rows(db, "SELECT id, code, name FROM subjects")}
    # 薄弱知识点表格里的「走向」「可能的前置」：和学业掌握标签页同一套知识点统计（按全部历史算）
    kps_all = await _kp_stats(db, sid)
    roots = pa_find_prerequisites(kps_all)
    kp_meta = {k["id"]: {"trend": k["trend"], "root_kp": roots.get(k["id"])} for k in kps_all}
    return _accuracy_build(cube, subs, prev, causes, kp_rows, semester, trend_rows, rng, kp_meta)


PERIODS = [("night", "凌晨", 0, 6), ("morning", "上午", 6, 12), ("afternoon", "下午", 12, 18), ("evening", "晚上", 18, 24)]


def _ai_build(rows, rng, prev_since=None):
    """AI 提问明细（纯计算）。
    rows：所选范围和前一段同样长度时间内的聊天消息，每条 {sid(会话), role, at, aha, rating, strat, strat_name, ask_ans(要答案), mood(聊情绪), summary, started}。
    提问次数 = 学生发的消息数；对话次数 = 有消息的会话数；顿悟 = 被标成顿悟触发的助教回复；场均提问 = 提问数 ÷ 对话次数"""
    prev_since = prev_since or rng.prev_since
    cur = [r for r in rows if r["at"] >= rng.since]
    old = [r for r in rows if r["at"] < rng.since]
    ask = lambda rs: sum(1 for r in rs if r["role"] == "student")
    sess = lambda rs: len({r["sid"] for r in rs})
    aha = lambda rs: sum(1 for r in rs if r["aha"])
    total, sessions, ahas = ask(cur), sess(cur), aha(cur)
    avg = lambda rs: round(ask(rs) / sess(rs), 1) if sess(rs) else None
    stats = {"total": total, "prev_total": ask(old), "sessions": sessions, "prev_sessions": sess(old), "aha": ahas, "prev_aha": aha(old),
             "avg_ask": avg(cur), "prev_avg_ask": avg(old)}
    stu = [r for r in cur if r["role"] == "student"]

    # 提问趋势：每个点（按天 / 按周）的提问数和顿悟数，从旧到新
    by_b: dict[int, list[int]] = {}
    for r in cur:
        e = by_b.setdefault(rng.bucket_of(r["at"]), [0, 0])
        e[0] += r["role"] == "student"
        e[1] += bool(r["aha"])
    series = [{"label": rng.bucket_label(w), "count": by_b.get(w, [0, 0])[0], "aha": by_b.get(w, [0, 0])[1]} for w in range(rng.points - 1, -1, -1)]

    # 提问时段（北京时间）：凌晨 / 上午 / 下午 / 晚上
    per = {k: 0 for k, *_ in PERIODS}
    for r in stu:
        h = r["at"].astimezone(BJ).hour
        for k, _, lo, hi in PERIODS:
            if lo <= h < hi:
                per[k] += 1
    periods = [{"key": k, "label": lb, "range": f"{lo}:00-{hi}:00", "count": per[k], "share": _pct(per[k], total)} for k, lb, lo, hi in PERIODS]

    # 启发策略：助教回复用了哪些策略、学生点赞 / 点踩了多少
    st: dict[str, dict] = {}
    for r in cur:
        if r["role"] == "assistant" and r["strat"]:
            e = st.setdefault(r["strat"], {"id": r["strat"], "name": r["strat_name"] or r["strat"], "uses": 0, "likes": 0, "dislikes": 0})
            e["uses"] += 1
            e["likes"] += r["rating"] == "like"
            e["dislikes"] += r["rating"] == "dislike"
    strategies = sorted(st.values(), key=lambda x: (-x["uses"], -x["likes"], x["id"]))[:5]
    rated = [r for r in cur if r["role"] == "assistant" and r["rating"] in ("like", "dislike")]
    likes = sum(1 for r in rated if r["rating"] == "like")
    like_rate = _pct(likes, len(rated))

    ask_ans = sum(1 for r in stu if r["ask_ans"])
    mood = sum(1 for r in stu if r["mood"])
    top_p = max(periods, key=lambda x: x["count"]) if total else None
    stats.update({"like_rate": like_rate, "rated": len(rated), "ask_answer": ask_ans, "mood": mood})

    tips = []
    if total == 0:
        pass
    else:
        if stats["prev_total"] and total != stats["prev_total"]:
            d = total - stats["prev_total"]
            tips.append(f"提问 {total} 次，较前一周期{'增加' if d > 0 else '减少'} {abs(d)} 次")
        else:
            tips.append(f"提问 {total} 次，来自 {sessions} 次对话，场均 {stats['avg_ask']} 问")
        if ahas:
            tips.append(f"出现 {ahas} 次顿悟（{_pct(ahas, sessions):g}% 的对话），引导式提问见效")
        elif sessions >= 3:
            tips.append(f"{sessions} 次对话都没有出现顿悟，可多用提示引导，少直接讲解")
        if ask_ans:
            tips.append(f"有 {ask_ans} 次直接要答案，建议鼓励先动手再提问")
        if mood:
            tips.append(f"有 {mood} 次聊到心情，可适当关注学习状态")
        if top_p and top_p["count"] and total >= 5:
            tips.append(f"最常在{top_p['label']}提问（{top_p['share']:g}%），可在这个时段多做答疑")
        if like_rate is not None and len(rated) >= 3:
            tips.append(f"助教回复点赞率 {like_rate:g}%（{len(rated)} 条被评价）")
        last = max((r for r in cur if r["summary"]), key=lambda r: r["started"], default=None)
        if last:
            sm = last["summary"].strip()
            tips.append("最近一次：" + (sm if len(sm) <= 42 else sm[:41] + "…"))
    return {"has_data": total > 0 or sessions > 0, "stats": stats, "series": series, "unit": "day" if rng.daily else "week",
            "periods": periods, "strategies": strategies, "tips": tips[:5]}


async def _ai_stats(db, sid, rng):
    rows = await _rows(db, """
        SELECT m.session_id::text sid, m.role, m.created_at "at", COALESCE(m.is_aha_trigger, false) aha, m.student_rating rating,
               m.strategy_id strat, st.strategy_name strat_name,
               (m.role = 'student' AND m.content ~ '答案') ask_ans, (m.role = 'student' AND m.content ~ '心情|难过|压抑|不开心|焦虑|烦|沮丧|低落') mood,
               cs.session_summary summary, cs.started_at started
        FROM ai_chat_messages m
        JOIN ai_chat_sessions cs ON cs.id = m.session_id
        LEFT JOIN ai_heuristic_strategies st ON st.strategy_id = m.strategy_id
        WHERE cs.student_id = :sid AND m.created_at >= :prev AND m.created_at < :until""", sid=sid, prev=rng.prev_since, until=rng.until)
    return _ai_build(rows, rng)


async def _study_time(db, sid, rng, k, beh, wrong_pending=0):
    rows = await _rows(db, f"""
        SELECT (a.answered_at AT TIME ZONE '{TZ}')::date d, q.subject_id sid, coalesce(sum(a.time_spent_sec), 0) t,
               count(*) n, count(*) FILTER (WHERE a.is_correct) c
        {_base(True)} GROUP BY 1, 2""", sid=sid, **rng.params)
    subs = {r["id"]: (r["code"], r["name"]) for r in await _rows(db, "SELECT id, code, name FROM subjects")}
    hours = await _rows(db, f"""
        SELECT extract(hour FROM a.answered_at AT TIME ZONE '{TZ}')::int h, coalesce(sum(a.time_spent_sec), 0) t
        {_base(True)} GROUP BY 1""", sid=sid, **rng.params)
    types = await _rows(db, f"""
        SELECT q.subject_id sid, s.training_dimension dim, coalesce(sum(a.time_spent_sec), 0) t, count(DISTINCT a.session_id) n
        {_base(True)} GROUP BY 1, 2""", sid=sid, **rng.params)
    prev = await _rows(db, f"""
        SELECT (a.answered_at AT TIME ZONE '{TZ}')::date d, coalesce(sum(a.time_spent_sec), 0) t
        {_base(True)} GROUP BY 1""", sid=sid, since=rng.prev_since, until=rng.since)
    prev_best = max((float(r["t"] or 0) for r in prev), default=0)
    kp_rows = await _rows(db, """
        SELECT q.subject_id sid, kp.id kid, kp.name, coalesce(sum(a.time_spent_sec), 0) t, count(*) n
        FROM training_answer_records a
        JOIN training_sessions s ON s.id = a.session_id
        JOIN questions q ON q.id = a.question_id
        CROSS JOIN LATERAL jsonb_array_elements_text(q.knowledge_point_ids) AS k(kid)
        JOIN knowledge_points kp ON kp.id = (CASE WHEN k.kid ~ '^[0-9]+$' THEN k.kid::bigint END)
        WHERE s.student_id = :sid AND COALESCE(a.is_seed_data, false) = false AND a.answered_at >= :since AND a.answered_at < :until
        GROUP BY 1, 2, 3""", sid=sid, **rng.params)
    return _study_time_build(rows, subs, rng, k["t1"], k["t0"], beh.get("avg_seconds_per_session"), hours, types, wrong_pending, prev_best, kp_rows)


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
    if cog.get("has_profile"):
        cog["insights"] = _cognitive_insights(cog, await _power_stats(db, student_id, rng), rng)
    diagnosis = await _diagnosis(db, student_id, rng)
    insights = await _insights(db, student_id, rng)
    weeks = await _trend(db, student_id, rng)
    recent = await _recent_accuracy(db, student_id, rng)
    from app.services import profile_config, profile_warning_service
    summary = _summary(basic, cog, mastery, beh, ai, weeks, recent["n"], await profile_config.get_weights(db), diagnosis, insights, recent, rng)
    kstats = await _kpi_stats(db, student_id, rng)
    kpis = _kpi_cards(kstats, beh, recent, rng, await _kpi_series(db, student_id, rng, beh))
    study_time = await _study_time(db, student_id, rng, kstats, beh, mastery.get("wrong_pending") or 0)
    training = await _sessions_stats(db, student_id, rng, mastery.get("wrong_pending") or 0)
    answers = await _answers_stats(db, student_id, rng)
    accuracy = await _accuracy_stats(db, student_id, rng, mastery.get("semester_progress"))
    ai_asks = await _ai_stats(db, student_id, rng)
    beh.pop("_sessions", None)
    await profile_warning_service.sync(db, student_id, basic)
    warnings = await profile_warning_service.list_warnings(db, student_id)
    return {
        "generated_at": datetime.now(timezone.utc), "range": rng.info(),
        "summary": summary, "kpis": kpis, "study_time": study_time, "training": training, "answers": answers, "accuracy": accuracy, "ai_asks": ai_asks, "basic": basic, "cognitive": cog, "mastery": mastery,
        "behavior": beh, "diagnosis": diagnosis, "insights": insights, "ai_interaction": ai, "traits": traits,
        "warnings": warnings,
    }
