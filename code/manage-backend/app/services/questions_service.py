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

    # KP 维度的已发布题目数（knowledge_point_ids 是 JSONB 数组，一题可挂多个知识点）
    kp_rows = (await db.execute(
        select(Question.knowledge_point_ids)
        .where(Question.status == 'published', Question.deleted_at.is_(None))
    )).scalars().all()
    for kp_ids in kp_rows:
        for kp_id in set(kp_ids or []):
            pub_by_kp[kp_id] = pub_by_kp.get(kp_id, 0) + 1

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


async def build_knowledge_catalog(db: AsyncSession) -> str:
    """生成供 LLM 选择的知识体系清单（科目/年级/学期 → 章节 → 知识点，附 ID）"""
    subjects  = (await db.execute(select(Subject).order_by(Subject.id))).scalars().all()
    grades    = (await db.execute(select(Grade).order_by(Grade.id))).scalars().all()
    semesters = (await db.execute(select(Semester).order_by(Semester.id))).scalars().all()
    chapters  = (await db.execute(select(Chapter).order_by(Chapter.id))).scalars().all()
    kps       = (await db.execute(select(KnowledgePoint).order_by(KnowledgePoint.id))).scalars().all()

    sub_map   = {x.id: x for x in subjects}
    grade_map = {x.id: x for x in grades}
    kp_by_ch: dict[int, list] = {}
    for kp in kps:
        kp_by_ch.setdefault(kp.chapter_id, []).append(kp)
    ch_by_sem: dict[int, list] = {}
    for ch in chapters:
        ch_by_sem.setdefault(ch.semester_id, []).append(ch)

    lines: list[str] = []
    for sem in semesters:
        g = grade_map.get(sem.grade_id)
        sub = sub_map.get(g.subject_id) if g else None
        if not g or not sub or not ch_by_sem.get(sem.id):
            continue
        lines.append(f"## {sub.code} / {g.code} / {sem.code}")
        for ch in ch_by_sem[sem.id]:
            lines.append(f"[章节ID {ch.id}] {ch.name}")
            for kp in kp_by_ch.get(ch.id, []):
                lines.append(f"  - [知识点ID {kp.id}] {kp.name}")
    return "\n".join(lines)


_CATALOG_INSTRUCTION = (
    "【知识体系清单】章节与知识点必须从下列清单中选择，不得自创名称：\n"
    "{catalog}\n\n"
    "【归类要求】在输出 JSON 中，subject/grade/semester 使用清单标题里的编码；"
    "chapter 填清单中的章节名称原文，并额外输出 chapter_id（整数，取自清单）；"
    "knowledge_points 填清单中的知识点名称原文，并额外输出 knowledge_point_ids（整数数组，取自清单，"
    "只能选择所选章节下的知识点）。清单中确无合适项时，对应字段填 null / 空数组。\n\n"
)


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
    if params.get('is_active') is not None:
        q = q.where(Question.is_active == params['is_active'])
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
                catalog = await build_knowledge_catalog(db)
                prefix = _CATALOG_INSTRUCTION.format(catalog=catalog) if catalog else ""
                if q.rejection_reason:
                    user_content = f"{prefix}请重新分析以下题目（上次驳回意见：{q.rejection_reason}）：\n\n{q.stem}"
                else:
                    user_content = f"{prefix}请分析以下题目：\n\n{q.stem}"
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
        ai_knowledge_point_ids=[],  # 由 _apply_knowledge_ids_from_codes 解析为 ID 后写入
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
        ai_solution='（模拟解析）本题为应用题，需根据题目信息建立方程并求解。审核时请替换为真实解析过程。',
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


# ── 修改已发布题目内容（不改变状态/启用状态）──────────────────

async def update_content(db: AsyncSession, question_id: int, data) -> Question:
    q = (await db.execute(
        select(Question).where(Question.id == question_id, Question.deleted_at.is_(None))
    )).scalar_one_or_none()
    if not q:
        raise AppException('题目不存在', 404)
    if q.status != 'published':
        raise AppException('仅已发布题目可修改内容', 400)

    weights = data.five_power_weights
    if sum(weights.values()) != 10:
        raise AppException('五力权重之和必须等于10', 400)

    if data.stem is not None:
        q.stem = data.stem
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
    q.primary_power = max(weights, key=weights.get)
    q.transfer_direction = data.transfer_directions
    if data.question_type is not None:
        q.question_type = data.question_type
    if data.answer is not None:
        q.answer = data.answer
    q.embedding_status = 'pending'  # 内容变更，需重新向量化
    flag_modified(q, 'knowledge_point_ids')
    flag_modified(q, 'five_power_weights')
    await db.flush()
    return q


# ── 审核页暂存（不改变题目状态）──────────────────────────────

async def save_review(db: AsyncSession, question_id: int, data) -> Question:
    """保存审核页当前编辑内容：同时写入题目字段与最新分析记录，使刷新后回显一致；状态保持 pending_review"""
    q = (await db.execute(
        select(Question).where(Question.id == question_id, Question.deleted_at.is_(None))
    )).scalar_one_or_none()
    if not q:
        raise AppException('题目不存在', 404)
    if q.status != 'pending_review':
        raise AppException('仅待审核状态的题目可保存审核结果', 400)

    ana = (await db.execute(
        select(QuestionAnalysis)
        .where(QuestionAnalysis.question_id == question_id)
        .order_by(QuestionAnalysis.round.desc())
        .limit(1)
    )).scalar_one_or_none()

    if data.stem is not None:
        q.stem = data.stem
    q.subject_id = data.subject_id
    q.grade_id = data.grade_id
    q.semester_id = data.semester_id
    q.chapter_id = data.chapter_id
    q.knowledge_point_ids = data.knowledge_point_ids
    q.question_type = data.question_type
    q.answer = data.answer
    q.difficulty = data.difficulty
    q.solution = data.solution
    q.common_error = data.common_error
    q.power_solutions = data.power_solutions
    q.five_power_weights = data.five_power_weights
    q.primary_power = max(data.five_power_weights, key=data.five_power_weights.get) if data.five_power_weights else None
    q.transfer_direction = data.transfer_directions
    flag_modified(q, 'knowledge_point_ids')
    flag_modified(q, 'five_power_weights')

    if ana:
        ana.ai_subject_id = data.subject_id
        ana.ai_grade_id = data.grade_id
        ana.ai_semester_id = data.semester_id
        ana.ai_chapter_id = data.chapter_id
        ana.ai_knowledge_point_ids = data.knowledge_point_ids
        ana.ai_question_type = data.question_type
        ana.ai_answer = data.answer
        ana.ai_difficulty = data.difficulty
        ana.ai_solution = data.solution
        ana.ai_common_error = data.common_error
        ana.ai_power_solutions = data.power_solutions
        ana.ai_five_power_weights = data.five_power_weights
        ana.ai_transfer_directions = data.transfer_directions
        for col in ('ai_knowledge_point_ids', 'ai_answer', 'ai_power_solutions',
                    'ai_five_power_weights', 'ai_transfer_directions'):
            flag_modified(ana, col)

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
    """将 AI 返回的科目/年级/学期/单元/知识点解析为数据库 ID，写入题目和分析记录。

    匹配优先级：LLM 返回的 ID（需校验归属）→ 名称模糊匹配 → 由知识点反推章节。
    章节与知识点相互独立：章节未匹配时，仍在整个学期范围内按名称匹配知识点。
    """
    from sqlalchemy import or_

    def _to_int(v):
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    subject_code  = result.get('subject')
    grade_code    = result.get('grade')
    semester_code = result.get('semester')
    chapter_name  = (result.get('chapter') or '').strip()
    kp_names      = [str(n).strip() for n in (result.get('knowledge_points') or []) if str(n).strip()]
    ai_chapter_id = _to_int(result.get('chapter_id'))
    ai_kp_ids     = [i for i in (_to_int(x) for x in (result.get('knowledge_point_ids') or [])) if i]

    # 重新分析时清掉上一轮遗留的章节/知识点，避免脏数据
    q.chapter_id = None
    q.knowledge_point_ids = []
    flag_modified(q, 'knowledge_point_ids')

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
    if not sem:
        return
    q.semester_id = sem.id
    if analysis: analysis.ai_semester_id = sem.id

    # 本学期下全部章节与知识点（数据量小，直接取出在内存中匹配）
    chapters = (await db.execute(
        select(Chapter).where(Chapter.semester_id == sem.id).order_by(Chapter.id)
    )).scalars().all()
    ch_by_id = {c.id: c for c in chapters}
    kps = []
    if ch_by_id:
        kps = (await db.execute(
            select(KnowledgePoint)
            .where(KnowledgePoint.chapter_id.in_(list(ch_by_id)))
            .order_by(KnowledgePoint.id)
        )).scalars().all()
    kp_by_id = {k.id: k for k in kps}

    def _match_kp_by_name(name: str, pool) -> 'KnowledgePoint | None':
        exact = [k for k in pool if k.name == name]
        if exact:
            return exact[0]
        # 双向包含：库中名称含 AI 名称，或 AI 名称含库中名称
        fuzzy = [k for k in pool if name in k.name or k.name in name]
        return fuzzy[0] if fuzzy else None

    # ── 1. 章节：ID → 名称 ──
    chapter = ch_by_id.get(ai_chapter_id) if ai_chapter_id else None
    if not chapter and chapter_name:
        key = chapter_name.replace(':', '：').split('：')[-1].strip() or chapter_name
        chapter = next((c for c in chapters if c.name == chapter_name), None) \
            or next((c for c in chapters if key in c.name or c.name in chapter_name), None)

    # ── 2. 知识点：ID → 名称（优先章节内，其次整个学期）──
    matched: list[KnowledgePoint] = []
    for kid in ai_kp_ids:
        kp = kp_by_id.get(kid)
        if kp and kp not in matched:
            matched.append(kp)
    if not matched:
        in_chapter = [k for k in kps if chapter and k.chapter_id == chapter.id]
        for name in kp_names:
            kp = _match_kp_by_name(name, in_chapter) or _match_kp_by_name(name, kps)
            if kp and kp not in matched:
                matched.append(kp)

    # ── 3. 章节仍未匹配：由知识点反推（取命中最多的章节）──
    if not chapter and matched:
        counts: dict[int, int] = {}
        for k in matched:
            counts[k.chapter_id] = counts.get(k.chapter_id, 0) + 1
        chapter = ch_by_id.get(max(counts, key=counts.get))

    # 知识点必须隶属所选章节，避免跨章节脏数据
    if chapter:
        matched = [k for k in matched if k.chapter_id == chapter.id]
        q.chapter_id = chapter.id
        if analysis: analysis.ai_chapter_id = chapter.id

    ids = [k.id for k in matched]
    q.knowledge_point_ids = ids
    flag_modified(q, 'knowledge_point_ids')
    if analysis:
        analysis.ai_knowledge_point_ids = ids
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


# ── 批量操作（接口文档 §9.1.10）──────────────────────────────────

BATCH_MAX = 200


def normalize_batch_ids(ids: list) -> list[int]:
    """校验并去重批量 ID，保持提交顺序"""
    if not ids:
        raise AppException('question_ids 不能为空', 400, 'QBATCH-001')
    if any(isinstance(i, bool) or not isinstance(i, int) or i <= 0 for i in ids):
        raise AppException('question_ids 包含非法值', 400, 'QBATCH-001')
    uniq = list(dict.fromkeys(ids))
    if len(uniq) > BATCH_MAX:
        raise AppException(f'单次最多提交 {BATCH_MAX} 条', 400, 'QBATCH-002')
    return uniq


def _batch_summary(items: list[dict]) -> dict:
    return {
        'total': len(items),
        'success_count': sum(1 for i in items if i['result'] == 'success'),
        'skipped_count': sum(1 for i in items if i['result'] == 'skipped'),
        'failed_count': sum(1 for i in items if i['result'] == 'failed'),
        'items': items,
    }


async def _load_batch(db: AsyncSession, ids: list[int]) -> dict[int, Question]:
    rows = (await db.execute(
        select(Question).where(Question.id.in_(ids), Question.deleted_at.is_(None))
    )).scalars().all()
    return {q.id: q for q in rows}


def _not_found(qid: int) -> dict:
    return {'question_id': qid, 'result': 'skipped', 'reason_code': 'NOT_FOUND', 'reason': '题目不存在或已删除'}


def _valid_weights(w) -> bool:
    return (
        isinstance(w, dict) and bool(w)
        and all(isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 10 for v in w.values())
        and sum(w.values()) == 10
    )


async def batch_analyze(db: AsyncSession, ids: list[int]) -> tuple[dict, list[tuple[int, int]]]:
    """批量置 analyzing。返回 (结果, [(question_id, round)]) 供路由层 commit 后启动后台分析"""
    qs = await _load_batch(db, ids)
    items, tasks = [], []
    for qid in ids:
        q = qs.get(qid)
        if not q:
            items.append(_not_found(qid))
            continue
        if q.status != 'draft':
            items.append({'question_id': qid, 'result': 'skipped', 'reason_code': 'STATUS_NOT_ALLOWED',
                          'reason': '仅草稿状态的题目可以触发分析', 'status': q.status})
            continue
        try:
            async with db.begin_nested():
                q.status = 'analyzing'
                q.analysis_round = (q.analysis_round or 0) + 1
                await db.flush()
            tasks.append((qid, q.analysis_round))
            items.append({'question_id': qid, 'result': 'success', 'status': 'analyzing'})
        except Exception:
            items.append({'question_id': qid, 'result': 'failed', 'reason_code': 'SYSTEM_ERROR',
                          'reason': '系统异常', 'status': 'draft'})
    return _batch_summary(items), tasks


async def batch_publish(db: AsyncSession, ids: list[int]) -> dict:
    """批量发布：使用各题最新一轮分析结果，每题独立 savepoint"""
    qs = await _load_batch(db, ids)
    items = []
    for qid in ids:
        q = qs.get(qid)
        if not q:
            items.append(_not_found(qid))
            continue
        if q.status != 'pending_review':
            items.append({'question_id': qid, 'result': 'skipped', 'reason_code': 'STATUS_NOT_ALLOWED',
                          'reason': '仅待审核状态的题目可以发布', 'status': q.status})
            continue
        try:
            ana = (await db.execute(
                select(QuestionAnalysis).where(QuestionAnalysis.question_id == qid)
                .order_by(QuestionAnalysis.round.desc()).limit(1)
            )).scalar_one_or_none()
            if (not ana or not ana.ai_subject_id or not ana.ai_grade_id
                    or not _valid_weights(ana.ai_five_power_weights)):
                items.append({'question_id': qid, 'result': 'failed', 'reason_code': 'ANALYSIS_INCOMPLETE',
                              'reason': '分析数据不完整（缺少科目 / 年级 / 五力权重不合法），请进入审核页补充后再发布',
                              'status': q.status})
                continue
            async with db.begin_nested():
                weights = ana.ai_five_power_weights
                q.subject_id = ana.ai_subject_id
                q.grade_id = ana.ai_grade_id
                q.semester_id = ana.ai_semester_id
                q.chapter_id = ana.ai_chapter_id
                q.knowledge_point_ids = list(ana.ai_knowledge_point_ids or [])
                q.difficulty = ana.ai_difficulty
                q.solution = ana.ai_solution
                q.common_error = ana.ai_common_error
                q.power_solutions = ana.ai_power_solutions
                q.five_power_weights = weights
                q.primary_power = max(weights, key=weights.get)
                q.transfer_direction = list(ana.ai_transfer_directions or [])
                q.question_type = ana.ai_question_type
                q.answer = ana.ai_answer
                q.status = 'published'
                flag_modified(q, 'knowledge_point_ids')
                flag_modified(q, 'five_power_weights')
                await db.flush()
            items.append({'question_id': qid, 'result': 'success', 'status': 'published',
                          'embedding_status': q.embedding_status})
        except Exception:
            items.append({'question_id': qid, 'result': 'failed', 'reason_code': 'SYSTEM_ERROR',
                          'reason': '系统异常', 'status': 'pending_review'})
    return _batch_summary(items)


async def batch_delete(db: AsyncSession, ids: list[int]) -> dict:
    qs = await _load_batch(db, ids)
    items = []
    for qid in ids:
        q = qs.get(qid)
        if not q:
            items.append(_not_found(qid))
            continue
        if q.status != 'draft':
            items.append({'question_id': qid, 'result': 'skipped', 'reason_code': 'STATUS_NOT_ALLOWED',
                          'reason': '仅草稿状态的题目可以删除', 'status': q.status})
            continue
        try:
            async with db.begin_nested():
                q.deleted_at = datetime.now(UTC)
                await db.flush()
            items.append({'question_id': qid, 'result': 'success'})
        except Exception:
            items.append({'question_id': qid, 'result': 'failed', 'reason_code': 'SYSTEM_ERROR',
                          'reason': '系统异常', 'status': 'draft'})
    return _batch_summary(items)


async def batch_set_active(db: AsyncSession, ids: list[int], is_active: bool) -> dict:
    """批量启用 / 停用（§9.1.10.4 / §9.1.10.5）：仅 published 题目参与，只改 is_active，不改 status"""
    qs = await _load_batch(db, ids)
    verb = '启用' if is_active else '停用'
    items = []
    for qid in ids:
        q = qs.get(qid)
        if not q:
            items.append(_not_found(qid))
            continue
        if q.status != 'published':
            items.append({'question_id': qid, 'result': 'skipped', 'reason_code': 'STATUS_NOT_ALLOWED',
                          'reason': f'仅已发布的题目可以{verb}', 'status': q.status, 'is_active': q.is_active})
            continue
        if q.is_active == is_active:
            items.append({'question_id': qid, 'result': 'skipped', 'reason_code': 'STATE_UNCHANGED',
                          'reason': f'题目已处于{verb}状态', 'status': q.status, 'is_active': q.is_active})
            continue
        try:
            async with db.begin_nested():
                q.is_active = is_active
                await db.flush()
            items.append({'question_id': qid, 'result': 'success', 'status': q.status, 'is_active': is_active})
        except Exception:
            items.append({'question_id': qid, 'result': 'failed', 'reason_code': 'SYSTEM_ERROR',
                          'reason': '系统异常', 'status': q.status, 'is_active': q.is_active})
    return _batch_summary(items)
