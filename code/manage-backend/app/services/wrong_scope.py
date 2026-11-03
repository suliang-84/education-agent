"""错题集的数据库查询：当前学期范围、待攻克 / 已攻克的题目、统计树（与 wrong_book 的纯函数配合）"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import Chapter, Grade, KnowledgePoint, Semester, Subject
from app.models.question import Question
from app.models.student import QuestionFavorite, Student, WrongAnswerRecord
from app.services.question_pool import pool_filters
from app.services.wrong_book import MASTERED_STATUSES, PENDING_STATUSES, build_tree

SEMESTER_NAMES = {"S1": "上学期", "S2": "下学期"}


async def semester_structure(db: AsyncSession, student: Student, subject_code: str | None):
    """学生当前年级 + 学期（在指定科目下）的单元与知识点。
    返回 (chapters[(id,name)], kps[(id,name,chapter_id)])；年级 / 学期缺失或该学期没有内容时返回两个空列表。"""
    if not student.grade or not student.semester:
        return [], []
    q = (
        select(Semester.id)
        .join(Grade, Semester.grade_id == Grade.id)
        .join(Subject, Grade.subject_id == Subject.id)
        .where(Grade.code == student.grade, Semester.code == student.semester)
    )
    if subject_code:
        q = q.where(Subject.code == subject_code)
    semester_id = (await db.execute(q)).scalars().first()
    if not semester_id:
        return [], []
    chapters = (await db.execute(
        select(Chapter.id, Chapter.name).where(Chapter.semester_id == semester_id).order_by(Chapter.id)
    )).all()
    if not chapters:
        return [], []
    kps = (await db.execute(
        select(KnowledgePoint.id, KnowledgePoint.name, KnowledgePoint.chapter_id)
        .where(KnowledgePoint.chapter_id.in_([c[0] for c in chapters])).order_by(KnowledgePoint.id)
    )).all()
    return [tuple(c) for c in chapters], [tuple(k) for k in kps]


async def wrong_questions(db: AsyncSession, student_id: int, subject_code: str | None, mastered: bool):
    """该学生待攻克（mastered=False）/ 已攻克（True）的题：[(题目id, [知识点id])]；只含后台已启用的题"""
    q = (
        select(Question.id, Question.knowledge_point_ids)
        .join(WrongAnswerRecord, WrongAnswerRecord.question_id == Question.id)
        .where(
            WrongAnswerRecord.student_id == student_id,
            WrongAnswerRecord.review_status.in_(MASTERED_STATUSES if mastered else PENDING_STATUSES),
            *pool_filters(),
        )
    )
    if subject_code:
        q = q.join(Subject, Question.subject_id == Subject.id).where(Subject.code == subject_code)
    return [(r[0], r[1] or []) for r in (await db.execute(q)).all()]


async def outline(db: AsyncSession, student: Student, subject_code: str):
    """待攻克 / 已攻克两棵「单元 → 知识点」统计树（只含当前学期）"""
    chapters, kps = await semester_structure(db, student, subject_code)
    pending = await wrong_questions(db, student.id, subject_code, mastered=False)
    mastered = await wrong_questions(db, student.id, subject_code, mastered=True)
    return build_tree(chapters, kps, pending), build_tree(chapters, kps, mastered)


async def pending_count(db: AsyncSession, student: Student, subject_code: str | None) -> int:
    """待攻克题数（题目去重）。资料里有年级学期时只算当前学期，与错题集页面最外层「待攻克」一致"""
    pending = await wrong_questions(db, student.id, subject_code, mastered=False)
    if student.grade and student.semester:
        chapters, kps = await semester_structure(db, student, subject_code)
        return build_tree(chapters, kps, pending)["count"]
    return len({q[0] for q in pending})


async def favorite_questions(db: AsyncSession, student_id: int, subject_code: str | None):
    """该学生收藏的题：[(题目id, [知识点id])]；只含后台已启用的题（被停用 / 删除的不显示）"""
    q = (
        select(Question.id, Question.knowledge_point_ids)
        .join(QuestionFavorite, QuestionFavorite.question_id == Question.id)
        .where(QuestionFavorite.student_id == student_id, *pool_filters())
    )
    if subject_code:
        q = q.join(Subject, Question.subject_id == Subject.id).where(Subject.code == subject_code)
    return [(r[0], r[1] or []) for r in (await db.execute(q)).all()]


async def favorites_outline(db: AsyncSession, student: Student, subject_code: str):
    """收藏夹「单元 → 知识点」统计树（只含当前学期）"""
    chapters, kps = await semester_structure(db, student, subject_code)
    return build_tree(chapters, kps, await favorite_questions(db, student.id, subject_code))
