"""题库管理业务逻辑"""
from datetime import datetime, UTC
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import attributes
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.core.exceptions import AppException
from app.models.question import Question, QuestionAnalysis
from app.models.knowledge import Subject, Grade, Semester, Chapter, KnowledgePoint


# ── 知识体系树 ────────────────────────────────────────────────

async def get_knowledge_tree(db: AsyncSession) -> list[dict]:
    """返回五级知识体系树，各节点附带已发布题目数量"""
    subjects = (await db.execute(select(Subject).order_by(Subject.id))).scalars().all()
    grades    = (await db.execute(select(Grade).order_by(Grade.subject_id, Grade.id))).scalars().all()
    semesters = (await db.execute(select(Semester).order_by(Semester.grade_id, Semester.id))).scalars().all()
    chapters  = (await db.execute(select(Chapter).order_by(Chapter.semester_id, Chapter.id))).scalars().all()
    kps       = (await db.execute(select(KnowledgePoint).order_by(KnowledgePoint.chapter_id, KnowledgePoint.id))).scalars().all()

    # 已发布题目数统计（按 semester_id）
    pub_by_sem = {}
    pub_by_ch  = {}
    pub_by_kp  = {}
    pub_rows = (await db.execute(
        select(
            Question.semester_id,
            Question.chapter_id,
            func.count().label('cnt')
        ).where(Question.status == 'published', Question.deleted_at.is_(None))
        .group_by(Question.semester_id, Question.chapter_id)
    )).all()
    for row in pub_rows:
        if row.semester_id:
            pub_by_sem[row.semester_id] = pub_by_sem.get(row.semester_id, 0) + row.cnt
        if row.chapter_id:
            pub_by_ch[row.chapter_id] = pub_by_ch.get(row.chapter_id, 0) + row.cnt

    # KP 维度的已发布题目数（knowledge_point_ids 是 JSONB 数组）
    # 简化：不单独统计 KP，KP 节点 published_count = 0（章节已覆盖）

    # 组装树
    kp_map: dict[int, list] = {}
    for kp in kps:
        kp_map.setdefault(kp.chapter_id, []).append({
            "type": "knowledge_point", "id": kp.id, "name": kp.name,
            "published_count": pub_by_kp.get(kp.id, 0), "children": []
        })

    ch_map: dict[int, list] = {}
    for ch in chapters:
        ch_map.setdefault(ch.semester_id, []).append({
            "type": "chapter", "id": ch.id, "name": ch.name,
            "published_count": pub_by_ch.get(ch.id, 0),
            "children": kp_map.get(ch.id, [])
        })

    sem_map: dict[int, list] = {}
    for sem in semesters:
        sem_map.setdefault(sem.grade_id, []).append({
            "type": "semester", "id": sem.id, "name": sem.name, "code": sem.code,
            "published_count": pub_by_sem.get(sem.id, 0),
            "children": ch_map.get(sem.id, [])
        })

    grade_map: dict[int, list] = {}
    for g in grades:
        grade_cnt = sum(s["published_count"] for s in sem_map.get(g.id, []))
        grade_map.setdefault(g.subject_id, []).append({
            "type": "grade", "id": g.id, "name": g.name, "code": g.code,
            "published_count": grade_cnt,
            "children": sem_map.get(g.id, [])
        })

    tree = []
    for sub in subjects:
        sub_cnt = sum(g["published_count"] for g in grade_map.get(sub.id, []))
        tree.append({
            "type": "subject", "id": sub.id, "name": sub.name, "code": sub.code,
            "published_count": sub_cnt,
            "children": grade_map.get(sub.id, [])
        })
    return tree


# ── 题目列表 ──────────────────────────────────────────────────

async def get_list(db: AsyncSession, params: dict) -> dict:
    q = select(Question).where(Question.deleted_at.is_(None))

    if params.get('subject_id'):
        q = q.where(Question.subject_id == params['subject_id'])
    if params.get('grade_id'):
        q = q.where(Question.grade_id == params['grade_id'])
    if params.get('semester_id'):
        q = q.where(Question.semester_id == params['semester_id'])
    if params.get('chapter_id'):
        q = q.where(Question.chapter_id == params['chapter_id'])
    if params.get('knowledge_point_id'):
        q = q.where(Question.knowledge_point_ids.contains([params['knowledge_point_id']]))
    if params.get('status'):
        q = q.where(Question.status == params['status'])
    if params.get('difficulty'):
        q = q.where(Question.difficulty == params['difficulty'])
    if params.get('keyword'):
        kw = f"%{params['keyword']}%"
        q = q.where(Question.stem.ilike(kw))

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    page  = max(1, params.get('page', 1))
    limit = min(1000, max(1, params.get('limit', 20)))
    total_pages = max(1, (total + limit - 1) // limit)

    q = q.order_by(Question.id.desc()).offset((page - 1) * limit).limit(limit)
    rows = (await db.execute(q)).scalars().all()
    return {'list': list(rows), 'total': total, 'page': page, 'limit': limit, 'total_pages': total_pages}


# ── 题目详情（含最新分析结果）────────────────────────────────

async def get_one(db: AsyncSession, question_id: int) -> dict:
    q = (await db.execute(
        select(Question).where(Question.id == question_id, Question.deleted_at.is_(None))
    )).scalar_one_or_none()
    if not q:
        raise AppException('题目不存在', 404)

    latest_analysis = (await db.execute(
        select(QuestionAnalysis)
        .where(QuestionAnalysis.question_id == question_id)
        .order_by(QuestionAnalysis.round.desc())
        .limit(1)
    )).scalar_one_or_none()

    return {'question': q, 'latest_analysis': latest_analysis}


# ── 创建题目 ──────────────────────────────────────────────────

async def create(db: AsyncSession, data, operator_id: int) -> Question:
    q = Question(
        stem=data.stem,
        image_url=data.image_url,
        status='draft',
        analysis_round=0,
        created_by=operator_id,
    )
    db.add(q)
    await db.flush()
    return q


# ── 触发分析 ──────────────────────────────────────────────────

async def analyze(db: AsyncSession, question_id: int, operator_id: int) -> Question:
    q = (await db.execute(
        select(Question).where(Question.id == question_id, Question.deleted_at.is_(None))
    )).scalar_one_or_none()
    if not q:
        raise AppException('题目不存在', 404)
    if q.status not in ('draft', 'pending_review'):
        raise AppException('当前状态不支持触发分析', 400)

    # 读取 system prompt
    from app.models.ai import SystemConfig
    cfg = (await db.execute(
        select(SystemConfig).where(SystemConfig.key == 'question_analysis_prompt')
    )).scalar_one_or_none()
    system_prompt = cfg.value if cfg else ''

    # 更新题目状态
    q.status = 'analyzing'
    q.analysis_round = (q.analysis_round or 0) + 1
    current_round = q.analysis_round
    await db.flush()

    # 尝试调用 Anthropic API
    try:
        from app.core.config import get_settings
        settings = get_settings()
        api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)

        if api_key:
            import anthropic, json
            client = anthropic.Anthropic(api_key=api_key)
            msg = client.messages.create(
                model=getattr(settings, 'ANTHROPIC_MODEL', 'claude-opus-4-6'),
                max_tokens=2048,
                system=system_prompt,
                messages=[{"role": "user", "content": f"请分析以下题目：\n\n{q.stem}"}]
            )
            result = json.loads(msg.content[0].text)
            _write_analysis(db, q, result, current_round)
        else:
            # 无 API Key：写入空白分析，状态置为 pending_review 供手动填写
            _write_mock_analysis(db, q, current_round)

        q.status = 'pending_review'
    except Exception:
        q.status = 'draft'
        q.analysis_round = max(0, current_round - 1)

    await db.flush()
    return q


def _write_analysis(db, q: Question, result: dict, round_no: int):
    analysis = QuestionAnalysis(
        question_id=q.id,
        round=round_no,
        ai_difficulty=result.get('difficulty'),
        ai_solution=result.get('solution'),
        ai_common_error=result.get('common_error') or result.get('typical_error'),
        ai_power_solutions=result.get('power_solutions'),
        ai_five_power_weights=result.get('five_power_weights'),
        ai_transfer_directions=result.get('transfer_directions', []),
        ai_question_type=result.get('question_type'),
        ai_answer=result.get('answer'),
        analysis_status='completed',
    )
    db.add(analysis)


def _write_mock_analysis(db, q: Question, round_no: int):
    """无 API Key 时生成模拟分析数据，供测试完整审核发布流程"""
    analysis = QuestionAnalysis(
        question_id=q.id,
        round=round_no,
        ai_question_type='APPLICATION',
        ai_difficulty='basic',
        ai_answer={
            "type": "APPLICATION",
            "final_answer": "（模拟）请在审核页面手动填写最终答案",
            "key_steps": ["步骤1：审视题意", "步骤2：设未知数", "步骤3：建立方程", "步骤4：求解验证"]
        },
        ai_solution='（模拟解析）本题为应用题，需根据题干信息建立方程并求解。审核时请替换为真实解析过程。',
        ai_common_error='（模拟）学生常见错误：变量设置混乱或方程关系建立不当，导致结果错误。',
        ai_power_solutions={
            "INSIGHT":   "（模拟）引导学生先找题目中的关键数量关系，识别已知与未知条件",
            "CONSTRUCT": "（模拟）从具体数值出发，引导学生逐步用变量替代，建立关系式",
            "DEDUCE":    "（模拟）将推导过程拆成最小步骤，每次只问一步，确保逻辑链不断裂",
            "ADAPT":     "（模拟）让学生代入答案验证，若矛盾则引导从出错步骤局部修正",
            "MIGRATE":   "（模拟）给出同构换皮情境，引导学生发现底层结构相同"
        },
        ai_five_power_weights={
            "INSIGHT": 2,
            "CONSTRUCT": 4,
            "DEDUCE": 2,
            "ADAPT": 1,
            "MIGRATE": 1
        },
        ai_transfer_directions=["（模拟）相似情境A", "（模拟）相似情境B"],
        analysis_status='completed',
    )
    db.add(analysis)


# ── 发布题目 ──────────────────────────────────────────────────

async def publish(db: AsyncSession, question_id: int, data, operator_id: int) -> Question:
    q = (await db.execute(
        select(Question).where(Question.id == question_id, Question.deleted_at.is_(None))
    )).scalar_one_or_none()
    if not q:
        raise AppException('题目不存在', 404)
    if q.status != 'pending_review':
        raise AppException('仅待审核状态的题目可发布', 400)

    weights = data.five_power_weights
    if sum(weights.values()) != 10:
        raise AppException('五力权重之和必须等于10', 400)

    primary_power = max(weights, key=weights.get)

    q.subject_id = data.subject_id
    q.grade_id = data.grade_id
    q.semester_id = data.semester_id
    q.chapter_id = data.chapter_id
    q.knowledge_point_ids = data.knowledge_point_ids
    q.difficulty = data.difficulty
    q.solution = data.solution
    q.common_error = data.common_error
    q.power_solutions = data.power_solutions
    q.five_power_weights = weights
    q.primary_power = primary_power
    q.transfer_direction = data.transfer_directions
    q.question_type = data.question_type
    q.answer = data.answer
    q.status = 'published'
    flag_modified(q, 'knowledge_point_ids')
    flag_modified(q, 'five_power_weights')
    await db.flush()
    return q


# ── 驳回题目 ──────────────────────────────────────────────────

async def reject(db: AsyncSession, question_id: int, reason: str, operator_id: int) -> Question:
    q = (await db.execute(
        select(Question).where(Question.id == question_id, Question.deleted_at.is_(None))
    )).scalar_one_or_none()
    if not q:
        raise AppException('题目不存在', 404)
    if q.status != 'pending_review':
        raise AppException('仅待审核状态的题目可驳回', 400)

    q.rejection_reason = reason
    q.status = 'analyzing'
    q.analysis_round = (q.analysis_round or 0) + 1
    current_round = q.analysis_round
    await db.flush()

    try:
        from app.core.config import get_settings
        from app.models.ai import SystemConfig
        settings = get_settings()
        api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
        cfg = (await db.execute(
            select(SystemConfig).where(SystemConfig.key == 'question_analysis_prompt')
        )).scalar_one_or_none()
        system_prompt = cfg.value if cfg else ''

        if api_key:
            import anthropic, json
            client = anthropic.Anthropic(api_key=api_key)
            msg = client.messages.create(
                model=getattr(settings, 'ANTHROPIC_MODEL', 'claude-opus-4-6'),
                max_tokens=2048,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"请重新分析以下题目（驳回意见：{reason}）：\n\n{q.stem}"
                }]
            )
            result = json.loads(msg.content[0].text)
            _write_analysis(db, q, result, current_round)
        else:
            _write_mock_analysis(db, q, current_round)

        q.status = 'pending_review'
    except Exception:
        q.status = 'draft'
        q.analysis_round = max(0, current_round - 1)

    await db.flush()
    return q


# ── 下架题目 ──────────────────────────────────────────────────

async def archive(db: AsyncSession, question_id: int) -> Question:
    q = (await db.execute(
        select(Question).where(Question.id == question_id, Question.deleted_at.is_(None))
    )).scalar_one_or_none()
    if not q:
        raise AppException('题目不存在', 404)
    if q.status != 'published':
        raise AppException('仅已发布题目可下架', 400)
    q.status = 'archived'
    await db.flush()
    return q


# ── 软删除 ────────────────────────────────────────────────────

async def delete(db: AsyncSession, question_id: int) -> None:
    q = (await db.execute(
        select(Question).where(Question.id == question_id, Question.deleted_at.is_(None))
    )).scalar_one_or_none()
    if not q:
        raise AppException('题目不存在', 404)
    if q.status != 'draft':
        raise AppException('仅草稿状态题目可删除', 409)
    q.deleted_at = datetime.now(UTC)
    await db.flush()
