"""小程序端个人信息模块 — §8"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.response import ok_response
from app.dependencies import get_current_student
from app.models.student import FivePowerProfile, FivePowerTrainingProfile, Student, StudentKpStat
from app.models.knowledge import Subject, KnowledgePoint, Chapter, Semester

router = APIRouter()


class UpdateProfileReq(BaseModel):
    nickname: str | None = None
    grade: str | None = None
    semester: str | None = None


@router.get("/me", summary="获取个人信息")
async def get_me(student: Student = Depends(get_current_student)):
    return ok_response({
        "student_id": student.id,
        "nickname": student.nickname,
        "avatar_url": student.avatar_url,
        "grade": student.grade,
        "semester": student.semester,
        "is_minor": student.is_minor,
        "phone_masked": student.phone_masked,
        "created_at": student.created_at.isoformat() if student.created_at else None,
    })


@router.patch("/me", summary="更新个人信息")
async def update_me(
    body: UpdateProfileReq,
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    if body.nickname is not None:
        student.nickname = body.nickname
    if body.grade is not None:
        student.grade = body.grade
    if body.semester is not None:
        student.semester = body.semester
    await db.commit()
    return ok_response({
        "student_id": student.id,
        "nickname": student.nickname,
        "grade": student.grade,
        "semester": student.semester,
    }, "信息更新成功")


@router.get("/five-power", summary="获取当前五力画像")
async def get_five_power(
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    profile = (
        await db.execute(
            select(FivePowerProfile)
            .where(FivePowerProfile.student_id == student.id, FivePowerProfile.is_latest == True)
        )
    ).scalar_one_or_none()

    training = (
        await db.execute(
            select(FivePowerTrainingProfile).where(FivePowerTrainingProfile.student_id == student.id)
        )
    ).scalar_one_or_none()

    if not profile:
        return ok_response({"has_profile": False, "profile": None, "training_profile": None})

    t = training
    return ok_response({
        "has_profile": True,
        "profile": {
            "profile_id": profile.id,
            "test_count": None,
            "forces": {
                "INSIGHT":    {"ability": profile.insight_ability,   "preference": profile.insight_preference,   "final": profile.insight_final},
                "CONSTRUCT":  {"ability": profile.construct_ability,  "preference": profile.construct_preference,  "final": profile.construct_final},
                "DEDUCE":     {"ability": profile.deduce_ability,     "preference": profile.deduce_preference,     "final": profile.deduce_final},
                "ADAPT":      {"ability": profile.adapt_ability,      "preference": profile.adapt_preference,      "final": profile.adapt_final},
                "MIGRATE":    {"ability": profile.migrate_ability,    "preference": profile.migrate_preference,    "final": profile.migrate_final},
            },
            "primary_weakness": profile.primary_weakness,
            "preferred_force": profile.preferred_force,
            "recommended_mode": profile.recommended_mode,
            "ai_analysis_text": profile.ai_analysis_text,
            "ai_analysis_status": profile.ai_analysis_status,
        },
        "training_profile": {
            "INSIGHT":   t.insight_ability if t else 50,
            "CONSTRUCT": t.construct_ability if t else 50,
            "DEDUCE":    t.deduce_ability if t else 50,
            "ADAPT":     t.adapt_ability if t else 50,
            "MIGRATE":   t.migrate_ability if t else 50,
        } if True else None,
    })


@router.get("/kp-stats", summary="知识点练习统计（学生自查）")
async def get_kp_stats(
    subject_code: str | None = Query(None),
    student: Student = Depends(get_current_student),
    db: AsyncSession = Depends(get_db),
):
    """返回当前年级+学期下各科目知识点练习统计"""
    from app.models.knowledge import Grade

    # 获取当前学期 id
    semester_id = None
    if student.grade and student.semester:
        grade_row = (await db.execute(
            select(Grade.id).join(Subject, Grade.subject_id == Subject.id)
            .where(Grade.code == student.grade)
            .limit(1)
        )).scalar_one_or_none()
        if grade_row:
            semester_row = (await db.execute(
                select(Semester.id).where(
                    Semester.grade_id == grade_row,
                    Semester.code == student.semester,
                )
            )).scalar_one_or_none()
            semester_id = semester_row

    # 查询知识点统计
    stats_q = (
        select(StudentKpStat, KnowledgePoint.name, Chapter.name.label("chapter_name"))
        .join(KnowledgePoint, StudentKpStat.knowledge_point_id == KnowledgePoint.id)
        .join(Chapter, KnowledgePoint.chapter_id == Chapter.id)
        .where(StudentKpStat.student_id == student.id)
    )
    if semester_id:
        stats_q = stats_q.where(Chapter.semester_id == semester_id)

    rows = (await db.execute(stats_q)).all()

    items = [
        {
            "kp_id": stat.id,
            "kp_name": kp_name,
            "chapter_name": chapter_name,
            "total_attempts": stat.total_attempts,
            "error_rate": float(stat.error_rate) if stat.error_rate else None,
            "is_stat_valid": stat.is_stat_valid,
            "last_practiced_at": stat.last_practiced_at.isoformat() if stat.last_practiced_at else None,
        }
        for stat, kp_name, chapter_name in rows
    ]

    return ok_response({"grade": student.grade, "semester": student.semester, "knowledge_points": items})
