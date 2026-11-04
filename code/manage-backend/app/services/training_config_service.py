"""训练配置：每种训练方式一份参数（题数 / 题型比例 / 难度比例 / 避开最近做过的题），智能训练另有算法参数；
以及题目分析（大模型）的并发数、超时。

存放位置：
- 训练方式参数：training_dimension_configs（每种方式一行，原地修改）
- 智能训练算法参数：该表的 smart_params（JSONB，只存与默认不同的部分也可，这里存完整一份）
- 题目分析：system_configs 的 question_analysis_concurrency / question_analysis_timeout_sec
"""
from datetime import datetime, timezone

from sqlalchemy import null, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.ai import SystemConfig
from app.models.training import TrainingDimensionConfig
from app.services.question_picker import QUESTION_TYPES
from app.services.smart_training.core import DEFAULT_PARAMS, merge_params

# 可配置的训练方式（顺序即页面展示顺序）。SEMESTER 已废弃，不再出现
DIMENSIONS = [
    ("KNOWLEDGE_POINT", "按知识点训练"),
    ("UNIT", "按单元训练"),
    ("RANDOM", "随机训练"),
    ("ERROR_QUESTIONS", "错题集训练"),
    ("FAVORITES", "收藏夹训练"),
    ("SMART", "智能训练"),
]
DIMENSION_CODES = [d for d, _ in DIMENSIONS]
DIFFICULTIES = ["basic", "advanced", "challenge"]
DEFAULT_DIFFICULTY_RATIO = {"basic": 50, "advanced": 35, "challenge": 15}

ANALYSIS_DEFAULTS = {"question_analysis_concurrency": 3, "question_analysis_timeout_sec": 180}
ANALYSIS_LIMITS = {"question_analysis_concurrency": (1, 10), "question_analysis_timeout_sec": (30, 600)}


def _num(v, name: str, lo: float, hi: float, integer: bool = False) -> float:
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise AppException(f"{name}必须是数字", 400)
    if integer and int(v) != v:
        raise AppException(f"{name}必须是整数", 400)
    if not (lo <= v <= hi):
        raise AppException(f"{name}需在 {lo:g} ~ {hi:g} 之间", 400)
    return int(v) if integer else float(v)


def _ratio(raw, keys: list[str], label: str) -> dict | None:
    """比例：None / 空 = 用默认；否则每项 ≥0 且总和 > 0"""
    if not raw:
        return None
    if not isinstance(raw, dict):
        raise AppException(f"{label}格式不正确", 400)
    out = {}
    for k, v in raw.items():
        if k not in keys:
            raise AppException(f"{label}包含未知项：{k}", 400)
        out[k] = _num(v, label, 0, 1000)
    if sum(out.values()) <= 0:
        raise AppException(f"{label}至少有一项大于 0", 400)
    return out


def validate_smart_params(raw: dict) -> dict:
    """校验智能训练算法参数，返回完整的一份（缺的项用默认值补齐）"""
    if not isinstance(raw, dict):
        raise AppException("智能训练参数格式不正确", 400)
    p = merge_params(raw)
    d = DEFAULT_PARAMS
    slots = {k: _num(p["slots"].get(k), "槽位配比", 0, 100) for k in d["slots"]}
    if sum(slots.values()) <= 0:
        raise AppException("槽位配比至少有一项大于 0", 400)
    weights = {k: _num(p["weights"].get(k), "打分权重", 0, 5) for k in d["weights"]}
    prior = p["prior"]
    if not isinstance(prior, (list, tuple)) or len(prior) != 2:
        raise AppException("平滑先验需要两个数（错、对）", 400)
    intervals = p["review_intervals_days"]
    if not isinstance(intervals, (list, tuple)) or not (1 <= len(intervals) <= 8):
        raise AppException("复习间隔需要 1~8 个天数", 400)
    intervals = [int(_num(x, "复习间隔", 1, 365, integer=True)) for x in intervals]
    return {
        "slots": slots,
        "intent_min_slots": int(_num(p["intent_min_slots"], "近期困惑保底题数", 0, 5, integer=True)),
        "weights": weights,
        "half_life_days": _num(p["half_life_days"], "做题历史半衰期", 1, 365),
        "intent_half_life_days": _num(p["intent_half_life_days"], "聊天困惑半衰期", 1, 365),
        "prior": [_num(prior[0], "平滑先验", 0.1, 20), _num(prior[1], "平滑先验", 0.1, 20)],
        "recent_penalty": _num(p["recent_penalty"], "最近做过的题扣分", 0, 5),
        "temperature": _num(p["temperature"], "随机程度", 0.05, 2),
        "diversity_type": _num(p["diversity_type"], "同题型降权倍数", 0.1, 1),
        "diversity_kp": _num(p["diversity_kp"], "同知识点降权倍数", 0.1, 1),
        "review_intervals_days": sorted(set(intervals)),
    }


def _row_to_dict(code: str, label: str, row: TrainingDimensionConfig | None) -> dict:
    return {
        "dimension": code,
        "label": label,
        "version_number": row.version_number if row else "v1",
        "questions_per_session": row.questions_per_session if row else 5,
        "dedup_window_size": row.dedup_window_size if row else 30,
        "difficulty_ratio": (row.difficulty_ratio if row and row.difficulty_ratio else None),
        "type_ratio": (row.type_ratio if row and row.type_ratio else None),
        "smart_params": merge_params(row.smart_params if row else None) if code == "SMART" else None,
        "is_default_difficulty": not (row and row.difficulty_ratio),
        "is_default_type": not (row and row.type_ratio),
    }


async def _active_row(db: AsyncSession, code: str) -> TrainingDimensionConfig | None:
    return (await db.execute(
        select(TrainingDimensionConfig)
        .where(TrainingDimensionConfig.dimension == code, TrainingDimensionConfig.is_active == True)  # noqa: E712
        .order_by(TrainingDimensionConfig.id.desc())
    )).scalars().first()


async def list_configs(db: AsyncSession) -> dict:
    items = [_row_to_dict(code, label, await _active_row(db, code)) for code, label in DIMENSIONS]
    return {
        "list": items,
        "question_types": QUESTION_TYPES,
        "difficulties": DIFFICULTIES,
        "default_difficulty_ratio": DEFAULT_DIFFICULTY_RATIO,
        "default_smart_params": merge_params(None),
    }


async def update_config(db: AsyncSession, code: str, data: dict, admin_id: int | None) -> dict:
    if code not in DIMENSION_CODES:
        raise AppException("不支持的训练方式", 400)
    label = dict(DIMENSIONS)[code]
    row = await _active_row(db, code)
    if row is None:
        row = TrainingDimensionConfig(
            dimension=code, version_number="v1", is_active=True,
            created_by=admin_id, created_at=datetime.now(timezone.utc),
        )
        db.add(row)
    row.questions_per_session = int(_num(data.get("questions_per_session"), "每次抽取题数", 1, 100, integer=True))
    row.dedup_window_size = int(_num(data.get("dedup_window_size"), "避开最近做过的题数", 0, 500, integer=True))
    # 没配置的比例存 SQL NULL（不是 JSON null），表示用默认
    row.difficulty_ratio = _ratio(data.get("difficulty_ratio"), DIFFICULTIES, "难度比例") or null()
    row.type_ratio = _ratio(data.get("type_ratio"), QUESTION_TYPES, "题型比例") or null()
    if code == "SMART":
        row.smart_params = validate_smart_params(data.get("smart_params") or {})
    await db.flush()
    await db.refresh(row)   # 赋过 SQL NULL 的字段需要重新读一次
    return _row_to_dict(code, label, row)


# ── 题目分析（大模型）配置 ────────────────────────────────────

async def get_analysis_config(db: AsyncSession) -> dict:
    rows = (await db.execute(
        select(SystemConfig).where(SystemConfig.key.in_(list(ANALYSIS_DEFAULTS)))
    )).scalars().all()
    got = {r.key: r.value for r in rows}
    out = {}
    for k, default in ANALYSIS_DEFAULTS.items():
        try:
            out[k] = int(got.get(k, default))
        except (TypeError, ValueError):
            out[k] = default
    return out


async def update_analysis_config(db: AsyncSession, data: dict, admin_id: int | None) -> dict:
    new = {}
    for k, (lo, hi) in ANALYSIS_LIMITS.items():
        name = "批量分析并发数" if k.endswith("concurrency") else "单题分析超时（秒）"
        new[k] = int(_num(data.get(k), name, lo, hi, integer=True))
    existing = {r.key: r for r in (await db.execute(
        select(SystemConfig).where(SystemConfig.key.in_(list(new)))
    )).scalars().all()}
    for k, v in new.items():
        row = existing.get(k)
        if row:
            row.value, row.updated_by = str(v), admin_id
        else:
            db.add(SystemConfig(
                key=k, value=str(v), value_type="number", updated_by=admin_id,
                description="题目分析并发数" if k.endswith("concurrency") else "题目分析单题总超时（秒）",
            ))
    await db.flush()
    return new
