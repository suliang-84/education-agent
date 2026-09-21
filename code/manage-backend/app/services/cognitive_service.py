"""五力测试题业务逻辑"""
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.core.exceptions import AppException
from app.models.cognitive import CognitiveTestQuestion

LETTERS = 'ABCDEFGH'


def _assign_keys(answers: list[dict]) -> list[dict]:
    """按顺序为答案分配 key（A/B/C/D…）"""
    return [{**a, 'key': LETTERS[i]} for i, a in enumerate(answers)]


async def _renumber(db: AsyncSession) -> None:
    """将所有题目按 id 升序重新编号（1、2、3…无空缺）"""
    rows = (await db.execute(
        select(CognitiveTestQuestion).order_by(CognitiveTestQuestion.id)
    )).scalars().all()
    for i, q in enumerate(rows, start=1):
        q.question_no = i


async def get_list(db: AsyncSession, status: str | None = None, keyword: str | None = None):
    q = select(CognitiveTestQuestion).order_by(CognitiveTestQuestion.question_no)
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
        status='draft',
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
        select(CognitiveTestQuestion).where(CognitiveTestQuestion.id == question_id)
    )).scalar_one_or_none()
    if not q:
        raise AppException('题目不存在', 404)
    if q.status not in ('draft', 'archived'):
        raise AppException('仅草稿或已下架的题目可编辑', 403)

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
        select(CognitiveTestQuestion).where(CognitiveTestQuestion.id == question_id)
    )).scalar_one_or_none()
    if not q:
        raise AppException('题目不存在', 404)

    current = q.status
    if new_status == 'published':
        if current not in ('draft', 'archived'):
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
        select(CognitiveTestQuestion).where(CognitiveTestQuestion.id == question_id)
    )).scalar_one_or_none()
    if not q:
        raise AppException('题目不存在', 404)
    if q.status == 'published':
        raise AppException('已发布题目不可删除，请先下架', 409)

    await db.delete(q)
    await db.flush()
    # 删除后重新连续编号
    await _renumber(db)
