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


# ── 触发分析（第一步：改状态，立即返回）────────────────────────

async def set_analyzing(db: AsyncSession, question_id: int) -> Question:
    """将题目状态改为 analyzing 并 flush，供路由层 commit 后立即返回给前端"""
    q = (await db.execute(
        select(Question).where(Question.id == question_id, Question.deleted_at.is_(None))
    )).scalar_one_or_none()
    if not q:
        raise AppException('题目不存在', 404)
    if q.status not in ('draft', 'pending_review'):
        raise AppException('当前状态不支持触发分析', 400)
    q.status = 'analyzing'
    q.analysis_round = (q.analysis_round or 0) + 1
    await db.flush()
    return q


# ── 触发分析（第二步：后台异步跑 LLM）───────────────────────────

async def run_analysis(question_id: int, operator_id: int, analysis_round: int) -> None:
    """后台任务：独立 DB session 调用 LLM，完成后更新题目状态"""
    from app.core.database import AsyncSessionLocal as async_session_factory
    from app.core.config import get_settings
    from app.core.llm import chat_json
    from app.models.ai import SystemConfig

    async with async_session_factory() as db:
        try:
            q = (await db.execute(
                select(Question).where(Question.id == question_id, Question.deleted_at.is_(None))
            )).scalar_one_or_none()
            if not q:
                return

            current_round = analysis_round  # 使用路由层传入的 round，避免时序读取问题

            # 读取 system prompt
            cfg = (await db.execute(
                select(SystemConfig).where(SystemConfig.key == 'question_analysis_prompt')
            )).scalar_one_or_none()
            system_prompt = cfg.value if cfg else ''

            settings = get_settings()
            if settings.LLM_API_KEY:
                if q.rejection_reason:
                    user_content = f"请重新分析以下题目（上次驳回意见：{q.rejection_reason}）：\n\n{q.stem}"
                else:
                    user_content = f"请分析以下题目：\n\n{q.stem}"
                result = await chat_json(system_prompt, user_content)
                analysis = _write_analysis(db, q, result, current_round)
                q.difficulty = result.get('difficulty')
                weights = result.get('five_power_weights') or {}
                if weights:
                    q.five_power_weights = weights
                    flag_modified(q, 'five_power_weights')
                    q.primary_power = max(weights, key=weights.get)
                await _apply_knowledge_ids_from_codes(db, q, result, analysis)
            else:
                _write_mock_analysis(db, q, current_round)
                q.subject_id  = 1
                q.grade_id    = 1
                q.semester_id = 1
                q.difficulty  = 'basic'
                q.five_power_weights = {"INSIGHT": 2, "CONSTRUCT": 4, "DEDUCE": 2, "ADAPT": 1, "MIGRATE": 1}
                flag_modified(q, 'five_power_weights')
                q.primary_power = 'CONSTRUCT'

            q.rejection_reason = None
            q.status = 'pending_review'
            await db.commit()

        except Exception:
            # LLM 失败：回退为草稿
            try:
                from app.core.database import AsyncSessionLocal
                async with AsyncSessionLocal() as db2:
                    q2 = (await db2.execute(
                        select(Question).where(Question.id == question_id)
                    )).scalar_one_or_none()
                    if q2 and q2.status == 'analyzing':
                        q2.status = 'draft'
                        q2.analysis_round = max(0, q2.analysis_round - 1)
                        await db2.commit()
            except Exception:
                pass


def _write_analysis(db, q: Question, result: dict, round_no: int) -> QuestionAnalysis:
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
        ai_knowledge_point_ids=result.get('knowledge_points', []),
        analysis_status='completed',
    )
    db.add(analysis)
    return analysis


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
    q.status = 'draft'
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


async def set_active(db: AsyncSession, question_id: int, is_active: bool) -> Question:
    """切换题目启用状态（停用/启用），仅作用于已发布题目，不影响 status 字段"""
    q = (await db.execute(
        select(Question).where(Question.id == question_id, Question.deleted_at.is_(None))
    )).scalar_one_or_none()
    if not q:
        raise AppException('题目不存在', 404)
    if q.status != 'published':
        raise AppException('仅已发布题目可切换启用状态', 400)
    q.is_active = is_active
    await db.flush()
    return q


# ── 知识体系 code → ID 解析 ───────────────────────────────────

async def _apply_knowledge_ids_from_codes(
    db: AsyncSession, q: Question, result: dict, analysis: 'QuestionAnalysis | None' = None
):
    """将 AI 返回的科目/年级/学期/单元/知识点解析为数据库 ID，写入题目和分析记录"""
    from sqlalchemy import or_
    subject_code  = result.get('subject')
    grade_code    = result.get('grade')
    semester_code = result.get('semester')
    chapter_name  = result.get('chapter', '')
    kp_names      = result.get('knowledge_points', [])

    if not subject_code:
        return
    sub = (await db.execute(
        select(Subject).where(Subject.code == subject_code)
    )).scalar_one_or_none()
    if not sub:
        return
    q.subject_id = sub.id
    if analysis: analysis.ai_subject_id = sub.id

    if not grade_code:
        return
    grade = (await db.execute(
        select(Grade).where(Grade.code == grade_code, Grade.subject_id == sub.id)
    )).scalar_one_or_none()
    if not grade:
        return
    q.grade_id = grade.id
    if analysis: analysis.ai_grade_id = grade.id

    sem = None
    if semester_code:
        sem = (await db.execute(
            select(Semester).where(Semester.code == semester_code, Semester.grade_id == grade.id)
        )).scalar_one_or_none()
        if sem:
            q.semester_id = sem.id
            if analysis: analysis.ai_semester_id = sem.id

    # 单元：按名称模糊匹配
    if chapter_name and sem:
        chapter_key = chapter_name.split('：')[-1].split(':')[-1].strip() if '：' in chapter_name or ':' in chapter_name else chapter_name
        chapters = (await db.execute(
            select(Chapter).where(
                Chapter.semester_id == sem.id,
                or_(
                    Chapter.name.ilike(f'%{chapter_key}%'),
                    Chapter.name.ilike(f'%{chapter_name}%'),
                )
            )
        )).scalars().all()
        if chapters:
            q.chapter_id = chapters[0].id
            if analysis: analysis.ai_chapter_id = chapters[0].id

            # 知识点：在匹配章节下按名称查找
            if kp_names:
                matched_kp_ids = []
                for kp_name in kp_names:
                    kp = (await db.execute(
                        select(KnowledgePoint).where(
                            KnowledgePoint.chapter_id == chapters[0].id,
                            KnowledgePoint.name.ilike(f'%{kp_name}%'),
                        )
                    )).scalar_one_or_none()
                    if kp:
                        matched_kp_ids.append(kp.id)
                if matched_kp_ids:
                    q.knowledge_point_ids = matched_kp_ids
                    flag_modified(q, 'knowledge_point_ids')
                    if analysis:
                        analysis.ai_knowledge_point_ids = matched_kp_ids
                        flag_modified(analysis, 'ai_knowledge_point_ids')


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
