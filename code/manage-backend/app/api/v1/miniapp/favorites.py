"""小程序端题目收藏 / 收藏夹

- 答题页右上角五角星：POST /favorites 收藏，DELETE /favorites/{question_id} 取消收藏（都是幂等的）
- 收藏夹页：GET /favorites/outline 「收藏夹 → 单元 → 知识点」统计树（只含当前学期）
- 点任意一级进入训练：POST /training/session，training_dimension=FAVORITES
"""
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AppException
from app.core.response import ok_response
from app.dependencies import get_current_student
from app.models.knowledge import Grade, Subject
from app.models.question import Question
from app.models.student import QuestionFavorite, Student
from app.services import wrong_scope

router = APIRouter()


class FavoriteReq(BaseModel):
    question_id: int


@router.post("", summary="收藏题目")
async def add_favorite(
    body: FavoriteReq,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    if not (await db.execute(select(Question.id).where(Question.id == body.question_id))).first():
        raise AppException("题目不存在", 404)
    exists = (await db.execute(
        select(QuestionFavorite.id).where(
            QuestionFavorite.student_id == student.id, QuestionFavorite.question_id == body.question_id
        )
    )).first()
    if not exists:
        db.add(QuestionFavorite(student_id=student.id, question_id=body.question_id, created_at=datetime.now(UTC)))
        await db.commit()
    return ok_response({"question_id": body.question_id, "is_favorite": True}, "已收藏")


@router.delete("/{question_id}", summary="取消收藏")
async def remove_favorite(
    question_id: int,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(QuestionFavorite).where(
            QuestionFavorite.student_id == student.id, QuestionFavorite.question_id == question_id
        )
    )
    await db.commit()
    return ok_response({"question_id": question_id, "is_favorite": False}, "已取消收藏")


@router.get("/status", summary="查询一批题目是否已收藏")
async def favorite_status(
    question_ids: str = Query(..., description="题目 id，逗号分隔"),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    ids = [int(x) for x in question_ids.split(",") if x.strip().isdigit()]
    rows = (await db.execute(
        select(QuestionFavorite.question_id).where(
            QuestionFavorite.student_id == student.id, QuestionFavorite.question_id.in_(ids)
        )
    )).scalars().all() if ids else []
    return ok_response({"favorite_ids": list(rows)})


@router.get("/count", summary="收藏题数（入口卡片显示用）")
async def favorite_count(
    subject_code: str = Query(...),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """题目去重；资料里有年级学期时只算当前学期，与收藏夹页最外层一致"""
    if student.grade and student.semester:
        return ok_response({"count": (await wrong_scope.favorites_outline(db, student, subject_code))["count"]})
    qs = await wrong_scope.favorite_questions(db, student.id, subject_code)
    return ok_response({"count": len({q[0] for q in qs})})


@router.get("/outline", summary="收藏夹：单元 → 知识点统计树")
async def favorites_outline(
    subject_code: str = Query(...),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    grade_rows = (await db.execute(
        select(Grade).join(Subject, Grade.subject_id == Subject.id).where(Subject.code == subject_code)
    )).scalars().all()
    grade_options = sorted(
        ({"code": g.code, "name": g.name} for g in grade_rows),
        key=lambda x: int(x["code"][1:]) if x["code"][1:].isdigit() else 99,
    )
    base = {
        "need_profile": False,
        "grade": None,
        "semester": None,
        "grade_options": grade_options,
        "semester_options": [{"code": c, "name": n} for c, n in wrong_scope.SEMESTER_NAMES.items()],
        "tree": {"count": 0, "chapters": []},
    }
    if not student.grade or not student.semester:
        return ok_response({**base, "need_profile": True})
    g = next((x for x in grade_rows if x.code == student.grade), None)
    base["grade"] = {"code": student.grade, "name": g.name if g else student.grade}
    base["semester"] = {
        "code": student.semester,
        "name": wrong_scope.SEMESTER_NAMES.get(student.semester, student.semester),
    }
    base["tree"] = await wrong_scope.favorites_outline(db, student, subject_code)
    return ok_response(base)
