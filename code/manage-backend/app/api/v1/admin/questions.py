"""题库管理路由 — §9.1"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.question import Question

from app.core.response import ok_response
from app.dependencies import get_current_admin, get_db
from app.models.admin import AdminUser
from app.schemas.questions import QuestionCreateReq, PublishPayload, RejectReq
from app.services import audit_service, questions_service

router = APIRouter()


@router.get("/knowledge-tree", summary="五级知识体系树")
async def get_knowledge_tree(
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    tree = await questions_service.get_knowledge_tree(db)
    return ok_response({"tree": tree})


@router.get("/questions", summary="题目列表")
async def list_questions(
    subject_id: int | None = Query(None),
    grade_id: int | None = Query(None),
    semester_id: int | None = Query(None),
    chapter_id: int | None = Query(None),
    knowledge_point_id: int | None = Query(None),
    status: str | None = Query(None),
    difficulty: str | None = Query(None),
    keyword: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    params = dict(
        subject_id=subject_id, grade_id=grade_id, semester_id=semester_id,
        chapter_id=chapter_id, knowledge_point_id=knowledge_point_id,
        status=status, difficulty=difficulty, keyword=keyword,
        page=page, limit=limit,
    )
    data = await questions_service.get_list(db, params)
    items = [_question_to_dict(q) for q in data['list']]
    return ok_response({**data, 'list': items})



@router.get("/questions/stats", summary="题目状态统计")
async def question_stats(
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    result = (await db.execute(
        select(
            func.count().label('total'),
            func.sum(case((Question.status == 'draft', 1), else_=0)).label('draft'),
            func.sum(case((Question.status == 'analyzing', 1), else_=0)).label('analyzing'),
            func.sum(case((Question.status == 'pending_review', 1), else_=0)).label('pending_review'),
            func.sum(case((Question.status == 'published', 1), else_=0)).label('published'),
            func.sum(case((Question.status == 'archived', 1), else_=0)).label('archived'),
        ).where(Question.deleted_at.is_(None))
    )).one()
    return ok_response({
        'total': result.total or 0,
        'draft': result.draft or 0,
        'analyzing': result.analyzing or 0,
        'pending_review': result.pending_review or 0,
        'published': result.published or 0,
        'archived': result.archived or 0,
    })


@router.get("/questions/{question_id}", summary="题目详情（含分析结果）")
async def get_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    data = await questions_service.get_one(db, question_id)
    q = data['question']
    ana = data['latest_analysis']
    return ok_response({
        **_question_to_dict(q),
        'latest_analysis': _analysis_to_dict(ana) if ana else None,
    })


@router.post("/questions", summary="录入题干（创建题目）")
async def create_question(
    body: QuestionCreateReq,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    q = await questions_service.create(db, body, current_admin.id)
    qid, qstatus = q.id, q.status
    await audit_service.log(db, current_admin.id, "CREATE_QUESTION",
                            target_type="questions", target_id=str(qid))
    await db.commit()
    return ok_response({"question_id": qid, "status": qstatus}, "题目已保存为草稿")


@router.post("/questions/{question_id}/analyze", summary="触发大模型分析")
async def analyze_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    q = await questions_service.analyze(db, question_id, current_admin.id)
    qid, qstatus, qround = q.id, q.status, q.analysis_round
    await audit_service.log(db, current_admin.id, "ANALYZE_QUESTION",
                            target_type="questions", target_id=str(qid))
    await db.commit()
    return ok_response({"question_id": qid, "status": qstatus, "analysis_round": qround}, "分析完成")


@router.post("/questions/{question_id}/publish", summary="发布题目（审核通过）")
async def publish_question(
    question_id: int,
    body: PublishPayload,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    q = await questions_service.publish(db, question_id, body, current_admin.id)
    qid, qstatus = q.id, q.status
    await audit_service.log(db, current_admin.id, "PUBLISH_QUESTION",
                            target_type="questions", target_id=str(qid))
    await db.commit()
    return ok_response({"question_id": qid, "status": qstatus, "embedding_status": q.embedding_status}, "题目已发布")


@router.post("/questions/{question_id}/reject", summary="驳回题目（自动重新分析）")
async def reject_question(
    question_id: int,
    body: RejectReq,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    q = await questions_service.reject(db, question_id, body.rejection_reason, current_admin.id)
    qid, qstatus, qround = q.id, q.status, q.analysis_round
    await audit_service.log(db, current_admin.id, "REJECT_QUESTION",
                            target_type="questions", target_id=str(qid))
    await db.commit()
    return ok_response({"question_id": qid, "status": qstatus, "analysis_round": qround}, "已驳回并重新触发分析")


@router.patch("/questions/{question_id}/status", summary="下架题目")
async def archive_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    q = await questions_service.archive(db, question_id)
    qid, qstatus = q.id, q.status
    await audit_service.log(db, current_admin.id, "ARCHIVE_QUESTION",
                            target_type="questions", target_id=str(qid))
    await db.commit()
    return ok_response({"question_id": qid, "status": qstatus}, "题目已下架")


@router.delete("/questions/{question_id}", summary="软删除草稿题目")
async def delete_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    await questions_service.delete(db, question_id)
    await audit_service.log(db, current_admin.id, "DELETE_QUESTION",
                            target_type="questions", target_id=str(question_id))
    await db.commit()
    return ok_response(None, "题目已删除")


# ── 序列化辅助 ────────────────────────────────────────────────

def _question_to_dict(q) -> dict:
    return {
        "id": q.id,
        "stem": q.stem,
        "image_url": q.image_url,
        "subject_id": q.subject_id,
        "grade_id": q.grade_id,
        "semester_id": q.semester_id,
        "chapter_id": q.chapter_id,
        "knowledge_point_ids": q.knowledge_point_ids,
        "question_type": q.question_type,
        "answer": q.answer,
        "difficulty": q.difficulty,
        "solution": q.solution,
        "common_error": q.common_error,
        "power_solutions": q.power_solutions,
        "five_power_weights": q.five_power_weights,
        "primary_power": q.primary_power,
        "transfer_direction": q.transfer_direction,
        "status": q.status,
        "analysis_round": q.analysis_round,
        "embedding_status": q.embedding_status,
        "created_by": q.created_by,
        "created_at": q.created_at,
        "updated_at": q.updated_at,
    }


def _analysis_to_dict(a) -> dict:
    return {
        "id": a.id,
        "round": a.round,
        "rejection_reason_used": a.rejection_reason_used,
        "ai_subject_id": a.ai_subject_id,
        "ai_grade_id": a.ai_grade_id,
        "ai_semester_id": a.ai_semester_id,
        "ai_chapter_id": a.ai_chapter_id,
        "ai_knowledge_point_ids": a.ai_knowledge_point_ids,
        "ai_question_type": a.ai_question_type,
        "ai_answer": a.ai_answer,
        "ai_difficulty": a.ai_difficulty,
        "ai_solution": a.ai_solution,
        "ai_common_error": a.ai_common_error,
        "ai_power_solutions": a.ai_power_solutions,
        "ai_five_power_weights": a.ai_five_power_weights,
        "ai_transfer_directions": a.ai_transfer_directions,
        "analysis_status": a.analysis_status,
        "created_at": a.created_at,
    }
