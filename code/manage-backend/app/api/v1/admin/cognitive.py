"""五力测试题维护路由 — §9.3"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import ok_response
from app.dependencies import get_current_admin, get_db
from app.models.admin import AdminUser
from app.schemas.cognitive import (
    CognitiveQuestionCreateReq,
    CognitiveQuestionUpdateReq,
    StatusChangeReq,
)
from app.services import audit_service, cognitive_service

router = APIRouter()


@router.get("/cognitive-questions", summary="获取测试题目列表")
async def list_questions(
    status: str | None = Query(None),
    keyword: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: AdminUser = Depends(get_current_admin),
):
    rows, published_count = await cognitive_service.get_list(db, status=status, keyword=keyword)
    return ok_response({
        "published_count": published_count,
        "test_available": published_count >= 10,
        "list": [
            {
                "id": q.id,
                "question_no": q.question_no,
                "description": q.description,
                "stem": q.stem,
                "image_url": q.image_url,
                "answers": q.answers,
                "reference_time_sec": q.reference_time_sec,
                "status": q.status,
                "created_by": q.created_by,
                "updated_by": q.updated_by,
                "created_at": q.created_at,
                "updated_at": q.updated_at,
            }
            for q in rows
        ],
    })


@router.post("/cognitive-questions", summary="新增测试题目")
async def create_question(
    body: CognitiveQuestionCreateReq,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    q = await cognitive_service.create(db, body, current_admin.id)
    qid, qstatus = q.id, q.status
    await audit_service.log(db, current_admin.id, "CREATE_COGNITIVE_QUESTION",
                            target_type="cognitive_test_questions", target_id=str(qid))
    await db.commit()
    return ok_response({"id": qid, "status": qstatus}, "题目创建成功")


@router.patch("/cognitive-questions/{question_id}", summary="编辑测试题目")
async def update_question(
    question_id: int,
    body: CognitiveQuestionUpdateReq,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    q = await cognitive_service.update_question(db, question_id, body, current_admin.id)
    qid = q.id
    await audit_service.log(db, current_admin.id, "UPDATE_COGNITIVE_QUESTION",
                            target_type="cognitive_test_questions", target_id=str(qid))
    await db.commit()
    return ok_response({"id": qid}, "题目已更新")


@router.patch("/cognitive-questions/{question_id}/status", summary="变更题目状态")
async def change_status(
    question_id: int,
    body: StatusChangeReq,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    q, published_count = await cognitive_service.change_status(
        db, question_id, body.status, current_admin.id
    )
    qid, qstatus = q.id, q.status
    await audit_service.log(db, current_admin.id, "CHANGE_COGNITIVE_STATUS",
                            target_type="cognitive_test_questions", target_id=str(qid))
    await db.commit()
    msg = "题目已发布" if body.status == "published" else "题目已下架"
    return ok_response({
        "id": qid,
        "status": qstatus,
        "published_count": published_count,
        "test_available": published_count >= 10,
    }, msg)


@router.delete("/cognitive-questions/{question_id}", summary="删除草稿题目")
async def delete_question(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin),
):
    await cognitive_service.delete_question(db, question_id)
    await audit_service.log(db, current_admin.id, "DELETE_COGNITIVE_QUESTION",
                            target_type="cognitive_test_questions", target_id=str(question_id))
    await db.commit()
    return ok_response(None, "草稿题目已删除")
