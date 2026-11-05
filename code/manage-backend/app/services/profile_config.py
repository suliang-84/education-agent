"""学生画像的可配置项：预警规则、学习投入度权重。

存放：system_configs 的 profile_warning_rules / profile_engagement_weights（value_type = json）。
没有保存过的项用这里的默认值；页面保存后整份写入。
"""
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.ai import SystemConfig

RULES_KEY = "profile_warning_rules"
WEIGHTS_KEY = "profile_engagement_weights"
LEVELS = {"notice": "提醒", "attention": "关注", "critical": "重点"}

# 每条规则：name 展示名；desc 触发说明；level 默认级别（tiered=True 的规则按档位定级，不可单独改级别）；
# fields 是可调参数（key / 名称 / 单位 / 范围 / 默认值）
RULES: list[dict] = [
    {"code": "NO_TRAIN", "name": "连续未训练", "desc": "超过设定天数没有做题。按天数分三档：提醒 / 关注 / 重点", "tiered": True, "level": "notice",
     "fields": [
         {"key": "notice_days", "label": "提醒（天）", "unit": "天", "min": 1, "max": 365, "default": 3},
         {"key": "attention_days", "label": "关注（天）", "unit": "天", "min": 1, "max": 365, "default": 7},
         {"key": "critical_days", "label": "重点（天）", "unit": "天", "min": 1, "max": 365, "default": 14}]},
    {"code": "ACC_DROP", "name": "正确率下滑", "desc": "近 14 天正确率比前 14 天下降超过设定的百分点", "level": "attention",
     "fields": [
         {"key": "drop_pp", "label": "下降超过", "unit": "个百分点", "min": 1, "max": 100, "default": 10},
         {"key": "min_answers", "label": "每段至少答题", "unit": "道", "min": 1, "max": 500, "default": 10}]},
    {"code": "KP_STREAK_WRONG", "name": "知识点连续答错", "desc": "同一知识点最近连续答错设定的次数", "level": "attention",
     "fields": [{"key": "streak", "label": "连续答错", "unit": "次", "min": 2, "max": 20, "default": 3}]},
    {"code": "STUBBORN_WRONG", "name": "顽固错题", "desc": "同一道题累计答错达到设定次数", "level": "notice",
     "fields": [{"key": "times", "label": "累计答错", "unit": "次", "min": 2, "max": 20, "default": 3}]},
    {"code": "COMPLETION_LOW", "name": "答题完成度低", "desc": "近 14 天作答题数占发放题数的比例低于设定值（经常刚开始就退出）", "level": "notice",
     "fields": [
         {"key": "min_rate", "label": "完成度低于", "unit": "%", "min": 1, "max": 100, "default": 40},
         {"key": "min_issued", "label": "至少发放", "unit": "题", "min": 1, "max": 1000, "default": 20}]},
    {"code": "LATE_NIGHT", "name": "深夜学习过多", "desc": "未成年学生近 14 天 22 点后答题占比超过设定值", "level": "attention",
     "fields": [
         {"key": "ratio", "label": "占比超过", "unit": "%", "min": 1, "max": 100, "default": 30},
         {"key": "min_answers", "label": "至少答题", "unit": "道", "min": 1, "max": 500, "default": 10}]},
    {"code": "FAST_WRONG", "name": "「快而错」偏多", "desc": "近 14 天用时最短的三分之一题目里，答错的占全部答题的比例超过设定值（可能在乱点）", "level": "notice",
     "fields": [
         {"key": "ratio", "label": "占比超过", "unit": "%", "min": 1, "max": 100, "default": 40},
         {"key": "min_answers", "label": "至少答题", "unit": "道", "min": 1, "max": 500, "default": 20}]},
    {"code": "TEST_MISSING", "name": "未完成五力测试", "desc": "学生还没有五力画像", "level": "notice", "fields": []},
    {"code": "PROFILE_STALE", "name": "五力画像过期", "desc": "最近一次五力测试距今超过设定天数", "level": "notice",
     "fields": [{"key": "days", "label": "超过", "unit": "天", "min": 7, "max": 730, "default": 90}]},
    {"code": "CHAT_NEGATIVE", "name": "聊天出现负面情绪", "level": "critical",
     "desc": "AI 助教每次对话摘要更新时，会由大模型根据学生说的话判断一次情绪状态。最近的判断达到设定程度、且连续出现设定次数就预警；判断为「需要重点关注」时不看次数，立即预警。还没有任何判断记录的学生不会触发",
     "fields": [
         {"key": "min_level", "label": "情绪程度达到", "unit": "", "type": "select", "default": "significant",
          "options": [{"value": "mild", "label": "轻度低落"}, {"value": "significant", "label": "明显低落"}, {"value": "urgent", "label": "需要重点关注"}]},
         {"key": "consecutive", "label": "连续判断", "unit": "次", "min": 1, "max": 5, "default": 1}]},
]
RULE_MAP = {r["code"]: r for r in RULES}

DEFAULT_WEIGHTS = {"frequency": 40, "streak": 20, "complete": 25, "careful": 15}
WEIGHT_LABELS = {"frequency": "训练频次", "streak": "连续天数", "complete": "答题完成度", "careful": "认真作答"}


def _default_rule_conf(r: dict) -> dict:
    conf = {"enabled": True, "level": r["level"], "params": {f["key"]: f["default"] for f in r["fields"]}}
    return conf


def merge_rule_conf(code: str, saved: dict | None) -> dict:
    r = RULE_MAP[code]
    conf = _default_rule_conf(r)
    saved = saved or {}
    if "enabled" in saved:
        conf["enabled"] = bool(saved["enabled"])
    if saved.get("level") in LEVELS and not r.get("tiered"):
        conf["level"] = saved["level"]
    for k, v in (saved.get("params") or {}).items():
        if k in conf["params"]:
            conf["params"][k] = v
    return conf


async def _load(db: AsyncSession, key: str):
    row = (await db.execute(select(SystemConfig).where(SystemConfig.key == key))).scalar_one_or_none()
    if not row:
        return None
    try:
        return json.loads(row.value)
    except (TypeError, ValueError):
        return None


async def _save(db: AsyncSession, key: str, value: dict, admin_id: int | None, desc: str):
    row = (await db.execute(select(SystemConfig).where(SystemConfig.key == key))).scalar_one_or_none()
    text = json.dumps(value, ensure_ascii=False)
    if row:
        row.value, row.updated_by = text, admin_id
    else:
        db.add(SystemConfig(key=key, value=text, value_type="json", description=desc, updated_by=admin_id))
    await db.flush()


async def get_rule_confs(db: AsyncSession) -> dict[str, dict]:
    saved = await _load(db, RULES_KEY) or {}
    return {r["code"]: merge_rule_conf(r["code"], saved.get(r["code"])) for r in RULES}


async def get_weights(db: AsyncSession) -> dict[str, int]:
    saved = await _load(db, WEIGHTS_KEY) or {}
    if "careful" not in saved and "hint" in saved:   # 兼容旧配置：「独立作答」(hint) 已改为「认真作答」(careful)
        saved["careful"] = saved["hint"]
    w = dict(DEFAULT_WEIGHTS)
    for k in w:
        if isinstance(saved.get(k), (int, float)):
            w[k] = int(saved[k])
    return w


async def get_config_view(db: AsyncSession) -> dict:
    confs = await get_rule_confs(db)
    return {
        "levels": [{"value": k, "label": v} for k, v in LEVELS.items()],
        "rules": [{
            "code": r["code"], "name": r["name"], "desc": r["desc"], "tiered": bool(r.get("tiered")),
            "fields": r["fields"], **confs[r["code"]],
        } for r in RULES],
        "weights": await get_weights(db),
        "weight_labels": WEIGHT_LABELS,
        "default_weights": DEFAULT_WEIGHTS,
    }


def _num(v, name, lo, hi):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise AppException(f"{name}必须是数字", 400)
    if not (lo <= v <= hi):
        raise AppException(f"{name}需在 {lo:g} ~ {hi:g} 之间", 400)
    return int(v) if float(v).is_integer() else float(v)


async def save_rules(db: AsyncSession, body: dict, admin_id: int | None) -> dict:
    """保存预警规则：body = {rules: {code: {enabled, level, params, keywords}}}"""
    rules_in = body.get("rules")
    if not isinstance(rules_in, dict):
        raise AppException("规则格式不正确", 400)
    out = {}
    for code, conf in rules_in.items():
        if code not in RULE_MAP:
            raise AppException(f"未知的规则：{code}", 400)
        r = RULE_MAP[code]
        if not isinstance(conf, dict):
            raise AppException(f"{r['name']}的配置格式不正确", 400)
        level = conf.get("level", r["level"])
        if level not in LEVELS:
            raise AppException(f"{r['name']}的级别不正确", 400)
        params = {}
        for f in r["fields"]:
            v = (conf.get("params") or {}).get(f["key"], f["default"])
            if f.get("type") == "select":
                if v not in {o["value"] for o in f["options"]}:
                    raise AppException(f"{r['name']}的「{f['label']}」取值不正确", 400)
                params[f["key"]] = v
            else:
                params[f["key"]] = _num(v, f"{r['name']}的「{f['label']}」", f["min"], f["max"])
        if code == "NO_TRAIN" and not (params["notice_days"] < params["attention_days"] < params["critical_days"]):
            raise AppException("连续未训练的三档天数需要依次变大（提醒 < 关注 < 重点）", 400)
        item = {"enabled": bool(conf.get("enabled", True)), "level": level if not r.get("tiered") else r["level"], "params": params}
        out[code] = item
    await _save(db, RULES_KEY, out, admin_id, "学生画像预警规则（启停、级别、阈值）")
    return await get_config_view(db)


async def save_weights(db: AsyncSession, body: dict, admin_id: int | None) -> dict:
    w = {}
    for k in DEFAULT_WEIGHTS:
        w[k] = int(_num(body.get(k), WEIGHT_LABELS[k], 0, 100))
    if sum(w.values()) != 100:
        raise AppException(f"学习投入度权重合计需为 100%，当前为 {sum(w.values())}%", 400)
    await _save(db, WEIGHTS_KEY, w, admin_id, "学生画像学习投入度权重（合计 100）")
    return w
