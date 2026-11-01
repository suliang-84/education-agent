"""五力测试题业务逻辑"""
from datetime import datetime, UTC

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.core.exceptions import AppException
from app.models.cognitive import CognitiveTestQuestion

LETTERS = 'ABCDEFGH'


def _assign_keys(answers: list[dict]) -> list[dict]:
    """按顺序为答案分配 key（A/B/C/D…）"""
    return [{**a, 'key': LETTERS[i]} for i, a in enumerate(answers)]


async def get_list(db: AsyncSession, status: str | None = None, keyword: str | None = None):
    # 管理后台列表按创建时间倒序（同一时间按 id 倒序保证稳定）
    q = select(CognitiveTestQuestion).where(CognitiveTestQuestion.deleted_at.is_(None)).order_by(
        CognitiveTestQuestion.created_at.desc(), CognitiveTestQuestion.id.desc()
    )
    if status:
        q = q.where(CognitiveTestQuestion.status == status)
    if keyword:
        kw = f'%{keyword}%'
        from sqlalchemy import or_
        q = q.where(or_(
            CognitiveTestQuestion.stem.ilike(kw),
            CognitiveTestQuestion.description.ilike(kw),
        ))
    rows = (await db.execute(q)).scalars().all()
    published_count = (await db.execute(
        select(func.count()).where(CognitiveTestQuestion.status == 'published')
    )).scalar_one()
    return rows, published_count


async def create(db: AsyncSession, data, operator_id: int) -> CognitiveTestQuestion:
    # 计算新 question_no（当前最大值 + 1）
    max_no = (await db.execute(
        select(func.max(CognitiveTestQuestion.question_no))
    )).scalar_one() or 0

    answers = [dict(a.model_dump()) for a in data.answers]
    answers = _assign_keys(answers)
    q = CognitiveTestQuestion(
        question_no=max_no + 1,
        description=data.description,
        stem=data.stem,
        image_url=data.image_url,
        answers=answers,
        reference_time_sec=data.reference_time_sec,
        status='archived',   # 测试题只有「已启用 / 已停用」两态，新建即已停用，启用后才参与测试
        created_by=operator_id,
        updated_by=operator_id,
    )
    db.add(q)
    await db.flush()
    return q


async def update_question(db: AsyncSession, question_id: int, data, operator_id: int) -> CognitiveTestQuestion:
    # 在进入 async DB 操作前，先将 Pydantic 对象序列化为纯 dict（避免 greenlet 上下文问题）
    new_answers = None
    if data.answers is not None:
        new_answers = _assign_keys([
            {'text': a.text, 'force_weights': dict(a.force_weights)}
            for a in data.answers
        ])

    q = (await db.execute(
        select(CognitiveTestQuestion).where(
            CognitiveTestQuestion.id == question_id, CognitiveTestQuestion.deleted_at.is_(None)
        )
    )).scalar_one_or_none()
    if not q:
        raise AppException('题目不存在', 404)
    if q.status != 'archived':
        raise AppException('仅已停用的题目可编辑，请先停用', 403)

    if data.stem is not None:
        q.stem = data.stem
    if data.description is not None:
        q.description = data.description
    if data.image_url is not None:
        q.image_url = data.image_url
    if data.reference_time_sec is not None:
        q.reference_time_sec = data.reference_time_sec
    if new_answers is not None:
        q.answers = new_answers
        flag_modified(q, 'answers')
    q.updated_by = operator_id
    await db.flush()
    return q


async def change_status(db: AsyncSession, question_id: int, new_status: str, operator_id: int):
    q = (await db.execute(
        select(CognitiveTestQuestion).where(
            CognitiveTestQuestion.id == question_id, CognitiveTestQuestion.deleted_at.is_(None)
        )
    )).scalar_one_or_none()
    if not q:
        raise AppException('题目不存在', 404)

    current = q.status
    if new_status == 'published':
        if current != 'archived':
            raise AppException('当前题目状态不支持此操作', 400)
        published_count = (await db.execute(
            select(func.count()).where(CognitiveTestQuestion.status == 'published')
        )).scalar_one()
        if published_count >= 20:
            raise AppException('已发布题目已达上限（20/20），请先下架一道题目后再发布', 400)
    elif new_status == 'archived':
        if current != 'published':
            raise AppException('当前题目状态不支持此操作', 400)
    else:
        raise AppException('非法状态值', 400)

    q.status = new_status
    q.updated_by = operator_id
    await db.flush()

    published_count = (await db.execute(
        select(func.count()).where(CognitiveTestQuestion.status == 'published')
    )).scalar_one()
    return q, published_count


async def delete_question(db: AsyncSession, question_id: int) -> None:
    q = (await db.execute(
        select(CognitiveTestQuestion).where(
            CognitiveTestQuestion.id == question_id, CognitiveTestQuestion.deleted_at.is_(None)
        )
    )).scalar_one_or_none()
    if not q:
        raise AppException('题目不存在', 404)
    if q.status == 'published':
        raise AppException('已启用题目不可删除，请先停用', 409)

    # 软删除：保留数据（test_answer_records 外键依赖该题，且历史成绩基于快照），不重新编号
    q.deleted_at = datetime.now(UTC)
    await db.flush()


# ── 批量启用 / 停用（接口文档 §9.3.6 / §9.3.7）──────────────────

BATCH_MAX = 200
PUBLISH_LIMIT = 20       # 已发布上限，与 change_status 一致
TEST_MIN_PUBLISHED = 10  # 已发布 ≥ 10 道测试功能可用


def normalize_batch_ids(ids: list) -> list[int]:
    """校验并去重批量 ID，保持提交顺序"""
    if not ids:
        raise AppException('question_ids 不能为空', 400, 'CBATCH-001')
    if any(isinstance(i, bool) or not isinstance(i, int) or i <= 0 for i in ids):
        raise AppException('question_ids 包含非整数或非法值', 400, 'CBATCH-001')
    uniq = list(dict.fromkeys(ids))
    if len(uniq) > BATCH_MAX:
        raise AppException(f'单次最多提交 {BATCH_MAX} 条', 400, 'CBATCH-002')
    return uniq


async def batch_set_status(db: AsyncSession, ids: list[int], activate: bool, operator_id: int) -> dict:
    """批量启用（archived → published）/ 停用（published → archived）

    - 启用受 20 道发布上限约束：按提交顺序占用剩余名额，用尽后返回 skipped + PUBLISH_LIMIT_REACHED
    - 仅 published / archived 两态；已处于目标状态返回 skipped + STATE_UNCHANGED
    - 每题独立 savepoint，单题异常只回滚该题
    """
    from sqlalchemy import text
    # 串行化批量启用，避免并发请求同时读到同一份剩余名额而超发
    await db.execute(text('SELECT pg_advisory_xact_lock(:k)'), {'k': 91003})

    rows = (await db.execute(
        select(CognitiveTestQuestion).where(
            CognitiveTestQuestion.id.in_(ids), CognitiveTestQuestion.deleted_at.is_(None)
        )
    )).scalars().all()
    qs = {q.id: q for q in rows}

    published_count = (await db.execute(
        select(func.count()).where(CognitiveTestQuestion.status == 'published')
    )).scalar_one()
    slots = max(0, PUBLISH_LIMIT - published_count)

    target = 'published' if activate else 'archived'
    source = 'archived' if activate else 'published'
    unchanged_text = '题目已处于启用状态' if activate else '题目已处于停用状态'

    items: list[dict] = []
    for qid in ids:
        q = qs.get(qid)
        if not q:
            items.append({'question_id': qid, 'result': 'skipped', 'reason_code': 'NOT_FOUND',
                          'reason': '题目不存在或已删除'})
            continue
        if q.status == target:
            items.append({'question_id': qid, 'result': 'skipped', 'reason_code': 'STATE_UNCHANGED',
                          'reason': unchanged_text, 'status': q.status})
            continue
        if q.status != source:   # 兜底：非 published / archived 的历史脏数据
            items.append({'question_id': qid, 'result': 'skipped', 'reason_code': 'STATUS_NOT_ALLOWED',
                          'reason': '题目状态异常，无法变更', 'status': q.status})
            continue
        if activate and slots <= 0:
            items.append({'question_id': qid, 'result': 'skipped', 'reason_code': 'PUBLISH_LIMIT_REACHED',
                          'reason': f'已发布题目已达上限（{PUBLISH_LIMIT}/{PUBLISH_LIMIT}）', 'status': q.status})
            continue
        try:
            async with db.begin_nested():
                q.status = target
                q.updated_by = operator_id
                await db.flush()
            if activate:
                slots -= 1
                published_count += 1
            else:
                published_count -= 1
            items.append({'question_id': qid, 'result': 'success', 'status': target})
        except Exception:
            items.append({'question_id': qid, 'result': 'failed', 'reason_code': 'SYSTEM_ERROR',
                          'reason': '系统异常', 'status': q.status})

    return {
        'total': len(items),
        'success_count': sum(1 for i in items if i['result'] == 'success'),
        'skipped_count': sum(1 for i in items if i['result'] == 'skipped'),
        'failed_count': sum(1 for i in items if i['result'] == 'failed'),
        'published_count': published_count,
        'test_available': published_count >= TEST_MIN_PUBLISHED,
        'items': items,
    }
