"""小程序端错题集模块 — §6

错题集分为「待攻克」和「已攻克」，各自按「单元 → 知识点」三级统计（只含当前学期）。
点任意一级都进入训练（POST /training/session，dimension=ERROR_QUESTIONS）。
原先的错题列表和「AI 复盘」已取消，由答题页的「智能解答」替代。
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.response import ok_response
from app.dependencies import get_current_student
from app.models.knowledge import Grade, Subject
from app.models.student import Student
from app.services import wrong_scope
from sqlalchemy import select

router = APIRouter()


@router.get("/outline", summary="错题集：待攻克 / 已攻克 → 单元 → 知识点")
async def get_outline(
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
        "pending": {"count": 0, "chapters": []},
        "mastered": {"count": 0, "chapters": []},
    }
    if not student.grade or not student.semester:
        return ok_response({**base, "need_profile": True})

    g = next((x for x in grade_rows if x.code == student.grade), None)
    base["grade"] = {"code": student.grade, "name": g.name if g else student.grade}
    base["semester"] = {
        "code": student.semester,
        "name": wrong_scope.SEMESTER_NAMES.get(student.semester, student.semester),
    }
    base["pending"], base["mastered"] = await wrong_scope.outline(db, student, subject_code)
    return ok_response(base)
