"""小程序端知识点导航模块 — §4"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.response import ok_response
from app.dependencies import get_current_student
from app.models.knowledge import Chapter, Grade, KnowledgePoint, Semester, Subject
from app.models.question import Question
from app.models.student import Student
from app.services.question_pool import kp_overlap, pool_filters

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


SEMESTER_NAMES = {"S1": "上学期", "S2": "下学期"}


@router.get("/outline", summary="按知识点训练：当前年级学期的单元与知识点")
async def get_outline(
    subject_code: str = Query(...),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """
    先看学生资料里的年级、学期：
    - 缺其中任一项 → need_profile = true，并返回可选的年级 / 学期，由小程序弹窗让学生补充；
    - 齐全 → 返回该学科该学期下按单元（章节）分组的知识点，每个知识点带「可抽题数」（已启用题目数）。
    """
    grade_rows = (await db.execute(
        select(Grade).join(Subject, Grade.subject_id == Subject.id)
        .where(Subject.code == subject_code).order_by(Grade.id)
    )).scalars().all()
    grade_options = sorted(
        ({"code": g.code, "name": g.name} for g in grade_rows),
        key=lambda x: int(x["code"][1:]) if x["code"][1:].isdigit() else 99,
    )
    semester_options = [{"code": c, "name": n} for c, n in SEMESTER_NAMES.items()]

    base = {
        "need_profile": False,
        "grade": None,
        "semester": None,
        "grade_options": grade_options,
        "semester_options": semester_options,
        "chapters": [],
    }
    if not student.grade or not student.semester:
        return ok_response({**base, "need_profile": True})

    grade = next((g for g in grade_rows if g.code == student.grade), None)
    base["grade"] = {"code": student.grade, "name": grade.name if grade else student.grade}
    base["semester"] = {"code": student.semester, "name": SEMESTER_NAMES.get(student.semester, student.semester)}
    if not grade:
        return ok_response(base)

    semester = (await db.execute(
        select(Semester).where(Semester.grade_id == grade.id, Semester.code == student.semester)
    )).scalar_one_or_none()
    if not semester:
        return ok_response(base)

    chapters = (await db.execute(
        select(Chapter).where(Chapter.semester_id == semester.id).order_by(Chapter.id)
    )).scalars().all()
    kps = (await db.execute(
        select(KnowledgePoint).where(KnowledgePoint.chapter_id.in_([c.id for c in chapters]))
        .order_by(KnowledgePoint.id)
    )).scalars().all() if chapters else []

    # 每个知识点的可抽题数：后台「启用」、未删除、未归档的题（与创建训练时的抽取池一致）
    counts: dict[int, int] = {}
    if kps:
        rows = (await db.execute(
            select(Question.knowledge_point_ids).where(
                *pool_filters(), kp_overlap([k.id for k in kps]),
            )
        )).scalars().all()
        for ids in rows:
            for kid in set(ids or []):
                counts[kid] = counts.get(kid, 0) + 1

    base["chapters"] = [
        {
            "id": c.id,
            "name": c.name,
            "points": [
                {"id": k.id, "name": k.name, "question_count": counts.get(k.id, 0)}
                for k in kps if k.chapter_id == c.id
            ],
        }
        for c in chapters
    ]
    return ok_response(base)
