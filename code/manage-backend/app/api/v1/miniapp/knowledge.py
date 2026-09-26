"""小程序端知识点导航模块 — §4"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.response import ok_response
from app.dependencies import get_current_student
from app.models.knowledge import Chapter, Grade, KnowledgePoint, Semester, Subject
from app.models.student import Student

router = APIRouter()


@router.get("/subjects", summary="获取学科列表")
async def get_subjects(db: AsyncSession = Depends(get_db)):
    subjects = (await db.execute(select(Subject).order_by(Subject.id))).scalars().all()
    return ok_response([{"id": s.id, "name": s.name, "code": s.code} for s in subjects])


@router.get("/grades", summary="获取年级列表")
async def get_grades(subject_code: str | None = Query(None), db: AsyncSession = Depends(get_db)):
    q = select(Grade).join(Subject, Grade.subject_id == Subject.id)
    if subject_code:
        q = q.where(Subject.code == subject_code)
    grades = (await db.execute(q.order_by(Grade.id))).scalars().all()
    return ok_response([{"id": g.id, "name": g.name, "code": g.code, "subject_id": g.subject_id} for g in grades])


@router.get("/points", summary="获取知识点列表（学生当前学期自动过滤）")
async def get_knowledge_points(
    subject_code: str | None = Query(None),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """根据学生当前年级+学期自动过滤，对学生无感知"""
    q = (
        select(KnowledgePoint, Chapter.name.label("chapter_name"))
        .join(Chapter, KnowledgePoint.chapter_id == Chapter.id)
        .join(Semester, Chapter.semester_id == Semester.id)
        .join(Grade, Semester.grade_id == Grade.id)
        .join(Subject, Grade.subject_id == Subject.id)
    )

    # 按学生当前年级+学期过滤
    if student.grade:
        q = q.where(Grade.code == student.grade)
    if student.semester:
        q = q.where(Semester.code == student.semester)
    if subject_code:
        q = q.where(Subject.code == subject_code)

    rows = (await db.execute(q.order_by(KnowledgePoint.id))).all()

    return ok_response([
        {
            "id": kp.id,
            "name": kp.name,
            "code": kp.code,
            "chapter_name": chapter_name,
            "chapter_id": kp.chapter_id,
        }
        for kp, chapter_name in rows
    ])
