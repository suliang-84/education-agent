"""用户管理业务逻辑服务"""
import secrets
import string
import bcrypt
from collections import defaultdict
from datetime import datetime, UTC

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import (
    Student,
    ParentStudentBinding,
    FivePowerProfile,
    StudentKpStat,
)
from app.models.ai import StudentAiPromptSummary, StudentPromptInsight
from app.models.admin import AdminUser
from app.models.knowledge import Subject, Chapter, KnowledgePoint, Semester
from app.core.exceptions import AppException


def _gen_password(length: int = 12) -> str:
    """生成随机密码：大小写字母 + 数字 + 特殊字符"""
    chars = string.ascii_letters + string.digits + '!@#$'
    while True:
        pwd = ''.join(secrets.choice(chars) for _ in range(length))
        if (
            any(c.isupper() for c in pwd)
            and any(c.islower() for c in pwd)
            and any(c.isdigit() for c in pwd)
        ):
            return pwd


# ── 学生列表 ──────────────────────────────────────────────────

async def get_student_list(
    db: AsyncSession,
    grade: str | None = None,
    has_profile: bool | None = None,
    keyword: str | None = None,
    page: int = 1,
    limit: int = 20,
):
    """返回学生列表，附带 has_five_power_profile、training_count、bound_parents_count"""
    from app.models.training import TrainingSession

    q = select(Student).where(
        Student.user_type == 'STUDENT',
        Student.deleted_at.is_(None),
        Student.is_active == True,
    )
    if grade:
        q = q.where(Student.grade == grade)
    if keyword:
        q = q.where(Student.nickname.ilike(f'%{keyword}%'))

    total_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(total_q)).scalar_one()
    total_pages = max(1, (total + limit - 1) // limit)

    offset = (page - 1) * limit
    q = q.order_by(Student.id.desc()).offset(offset).limit(limit)
    rows = (await db.execute(q)).scalars().all()

    student_ids = [s.id for s in rows]

    # 有五力画像（is_latest）的学生集合
    profile_ids_res = await db.execute(
        select(FivePowerProfile.student_id).where(
            FivePowerProfile.student_id.in_(student_ids),
            FivePowerProfile.is_latest == True,
        )
    )
    profile_set = {r[0] for r in profile_ids_res.all()}

    # 训练次数（按 student_id 分组）
    training_cnt_res = await db.execute(
        select(TrainingSession.student_id, func.count().label('cnt'))
        .where(TrainingSession.student_id.in_(student_ids))
        .group_by(TrainingSession.student_id)
    )
    training_map = {r[0]: r[1] for r in training_cnt_res.all()}

    # 绑定家长数（bind_status == 'active' 且未软删除）
    binding_cnt_res = await db.execute(
        select(ParentStudentBinding.student_id, func.count().label('cnt'))
        .where(
            ParentStudentBinding.student_id.in_(student_ids),
            ParentStudentBinding.bind_status == 'active',
            ParentStudentBinding.deleted_at.is_(None),
        )
        .group_by(ParentStudentBinding.student_id)
    )
    binding_map = {r[0]: r[1] for r in binding_cnt_res.all()}

    items = []
    for s in rows:
        items.append({
            'id': s.id,
            'nickname': s.nickname,
            'grade': s.grade,
            'is_minor': s.is_minor,
            'has_five_power_profile': s.id in profile_set,
            'training_count': training_map.get(s.id, 0),
            'bound_parents_count': binding_map.get(s.id, 0),
            'last_login_at': s.last_login_at,
            'created_at': s.created_at,
        })

    return {'list': items, 'total': total, 'page': page, 'limit': limit, 'total_pages': total_pages}


# ── 家长列表 ──────────────────────────────────────────────────

async def get_parent_list(
    db: AsyncSession,
    keyword: str | None = None,
    page: int = 1,
    limit: int = 20,
):
    q = select(Student).where(
        Student.user_type == 'PARENT',
        Student.deleted_at.is_(None),
        Student.is_active == True,
    )
    if keyword:
        q = q.where(Student.nickname.ilike(f'%{keyword}%'))

    total_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(total_q)).scalar_one()
    total_pages = max(1, (total + limit - 1) // limit)

    offset = (page - 1) * limit
    q = q.order_by(Student.id.desc()).offset(offset).limit(limit)
    rows = (await db.execute(q)).scalars().all()

    parent_ids = [p.id for p in rows]

    # 查绑定关系（bind_status == 'active' 且未软删除）
    binding_res = await db.execute(
        select(ParentStudentBinding).where(
            ParentStudentBinding.parent_id.in_(parent_ids),
            ParentStudentBinding.bind_status == 'active',
            ParentStudentBinding.deleted_at.is_(None),
        )
    )
    bindings = binding_res.scalars().all()

    # 批量查学生信息
    s_ids = list({b.student_id for b in bindings})
    if s_ids:
        students_res = await db.execute(select(Student).where(Student.id.in_(s_ids)))
        student_map = {s.id: s for s in students_res.scalars().all()}
    else:
        student_map = {}

    # 按 parent_id 分组
    binding_map: dict[int, list] = defaultdict(list)
    for b in bindings:
        st = student_map.get(b.student_id)
        binding_map[b.parent_id].append({
            'student_id': b.student_id,
            'nickname': st.nickname if st else None,
            'grade': st.grade if st else None,
            'bind_method': b.bind_method,
            'bind_date': b.created_at,
        })

    items = []
    for p in rows:
        items.append({
            'id': p.id,
            'nickname': p.nickname,
            'is_confirmed': p.is_confirmed,
            'bound_students': binding_map.get(p.id, []),
            'last_login_at': p.last_login_at,
            'created_at': p.created_at,
        })

    return {'list': items, 'total': total, 'page': page, 'limit': limit, 'total_pages': total_pages}


# ── 管理员列表 ────────────────────────────────────────────────

async def get_admin_list(
    db: AsyncSession,
    page: int = 1,
    limit: int = 20,
):
    q = select(AdminUser).where(AdminUser.deleted_at.is_(None))

    total_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(total_q)).scalar_one()
    total_pages = max(1, (total + limit - 1) // limit)

    offset = (page - 1) * limit
    q = q.order_by(AdminUser.id.desc()).offset(offset).limit(limit)
    rows = (await db.execute(q)).scalars().all()

    return {'list': list(rows), 'total': total, 'page': page, 'limit': limit, 'total_pages': total_pages}


# ── 删除管理员（软删除，仅停用状态可删除）────────────────────────
async def delete_admin(db: AsyncSession, admin_id: int, operator_id: int):
    if admin_id == operator_id:
        raise AppException('不能删除自己的账号', 403)

    admin = (await db.execute(
        select(AdminUser).where(AdminUser.id == admin_id, AdminUser.deleted_at.is_(None))
    )).scalar_one_or_none()
    if not admin:
        raise AppException('管理员账号不存在', 404)
    if admin.is_active != 0:
        raise AppException('请先停用该账号后再删除', 403)

    admin.deleted_at = datetime.now(UTC)


# ── 创建管理员 ────────────────────────────────────────────────

async def create_admin(db: AsyncSession, data, operator_id: int):
    existing = (
        await db.execute(select(AdminUser).where(AdminUser.username == data.username))
    ).scalar_one_or_none()
    if existing:
        raise AppException('用户名已存在', 409)

    pwd_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt(rounds=12)).decode()

    admin = AdminUser(
        username=data.username,
        display_name=data.display_name,
        phone=data.phone,  # 生产环境应加密存储
        email=data.email,
        password_hash=pwd_hash,
        role='SUPER_ADMIN',
        is_active=1,
        created_by=operator_id,
    )
    db.add(admin)
    await db.flush()
    return admin


# ── 启用 / 停用管理员 ─────────────────────────────────────────

async def set_admin_status(db: AsyncSession, admin_id: int, is_active: int, operator_id: int):
    if admin_id == operator_id:
        raise AppException('不能修改自己的账号状态', 403)

    admin = (
        await db.execute(select(AdminUser).where(AdminUser.id == admin_id))
    ).scalar_one_or_none()
    if not admin:
        raise AppException('管理员账号不存在', 404)

    admin.is_active = is_active
    return admin


# ── 重置管理员密码 ────────────────────────────────────────────

async def reset_admin_password(db: AsyncSession, admin_id: int):
    admin = (
        await db.execute(select(AdminUser).where(AdminUser.id == admin_id))
    ).scalar_one_or_none()
    if not admin:
        raise AppException('管理员账号不存在', 404)

    admin.password_hash = bcrypt.hashpw(b'123456', bcrypt.gensalt(rounds=12)).decode()
    admin.is_active = 1


# ── 绑定家长 ──────────────────────────────────────────────────

async def bind_parent(db: AsyncSession, student_id: int, parent_phone: str, operator_id: int):
    # 检查学生存在
    student = (
        await db.execute(
            select(Student).where(
                Student.id == student_id,
                Student.user_type == 'STUDENT',
            )
        )
    ).scalar_one_or_none()
    if not student:
        raise AppException('学生不存在', 404)

    # 检查已绑定家长数（active 绑定）
    bound_count = (
        await db.execute(
            select(func.count()).select_from(ParentStudentBinding).where(
                ParentStudentBinding.student_id == student_id,
                ParentStudentBinding.bind_status == 'active',
                ParentStudentBinding.deleted_at.is_(None),
            )
        )
    ).scalar_one()
    if bound_count >= 2:
        raise AppException('该学生已绑定2位家长，无法继续绑定', 409)

    # 查找家长账号（开发阶段 phone 未加密，直接比对）
    parent = (
        await db.execute(
            select(Student).where(
                Student.phone == parent_phone,
                Student.user_type == 'PARENT',
            )
        )
    ).scalar_one_or_none()

    parent_created = False
    if not parent:
        # 自动创建家长账号
        parent = Student(
            openid_hash='',
            phone=parent_phone,
            phone_masked=parent_phone[:3] + '****' + parent_phone[-4:],
            nickname=f'家长{parent_phone[-4:]}',
            user_type='PARENT',
            is_confirmed=False,
            subject_prefs=[],
        )
        db.add(parent)
        await db.flush()
        parent_created = True

    # 检查是否已存在绑定关系（包含软删除的）
    existing_bind = (
        await db.execute(
            select(ParentStudentBinding).where(
                ParentStudentBinding.student_id == student_id,
                ParentStudentBinding.parent_id == parent.id,
                ParentStudentBinding.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if existing_bind:
        raise AppException('该家长已是该学生的绑定家长', 409)

    # 检查家长已绑定学生数
    parent_bind_count = (
        await db.execute(
            select(func.count()).select_from(ParentStudentBinding).where(
                ParentStudentBinding.parent_id == parent.id,
                ParentStudentBinding.bind_status == 'active',
                ParentStudentBinding.deleted_at.is_(None),
            )
        )
    ).scalar_one()
    if parent_bind_count >= 5:
        raise AppException('该家长已绑定5位学生，无法继续绑定', 409)

    binding = ParentStudentBinding(
        student_id=student_id,
        parent_id=parent.id,
        bind_method='ADMIN',
        bind_status='active',
        created_by_admin_id=operator_id,
    )
    db.add(binding)
    await db.flush()
    return binding, parent, parent_created


# ── 解绑（学生侧：从某学生移除某家长）─────────────────────────

async def unbind_parent_from_student(db: AsyncSession, student_id: int, parent_id: int):
    binding = (
        await db.execute(
            select(ParentStudentBinding).where(
                ParentStudentBinding.student_id == student_id,
                ParentStudentBinding.parent_id == parent_id,
                ParentStudentBinding.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if not binding:
        raise AppException('绑定关系不存在', 404)

    binding.bind_status = 'removed'
    binding.deleted_at = datetime.now(UTC)


# ── 解绑（家长侧：从某家长移除某学生）────────────────────────

async def unbind_student_from_parent(db: AsyncSession, parent_id: int, student_id: int):
    await unbind_parent_from_student(db, student_id, parent_id)


# ── 知识点统计 ────────────────────────────────────────────────

async def get_kp_stats(
    db: AsyncSession,
    student_id: int,
    subject_code: str | None = None,
    only_valid: bool = False,
):
    student = (
        await db.execute(select(Student).where(Student.id == student_id))
    ).scalar_one_or_none()
    if not student:
        raise AppException('学生不存在', 404)

    # KnowledgePoint → Chapter → Semester → Subject（知识库层级关系）
    q = (
        select(
            StudentKpStat,
            KnowledgePoint.name.label('kp_name'),
            Chapter.name.label('chapter_name'),
            Subject.code.label('subject_code'),
            Subject.name.label('subject_name'),
        )
        .join(KnowledgePoint, StudentKpStat.knowledge_point_id == KnowledgePoint.id)
        .join(Chapter, KnowledgePoint.chapter_id == Chapter.id)
        .join(Semester, Chapter.semester_id == Semester.id)
        .join(Subject, Semester.grade_id == Subject.id)  # Grade 与 Subject 关联
        .where(StudentKpStat.student_id == student_id)
    )
    if subject_code:
        q = q.where(Subject.code == subject_code)
    if only_valid:
        q = q.where(StudentKpStat.is_stat_valid == True)

    rows = (await db.execute(q)).all()

    # 按学科分组
    subject_map: dict = defaultdict(lambda: {'subject_code': '', 'subject_name': '', 'knowledge_points': []})
    for row in rows:
        stat, kp_name, chapter_name, s_code, s_name = row
        subject_map[s_code]['subject_code'] = s_code
        subject_map[s_code]['subject_name'] = s_name
        subject_map[s_code]['knowledge_points'].append({
            'kp_id': stat.knowledge_point_id,
            'kp_name': kp_name,
            'chapter_name': chapter_name,
            'total_attempts': stat.total_attempts,
            'error_count': stat.error_count if stat.is_stat_valid else None,
            'error_rate': float(stat.error_rate) if stat.is_stat_valid and stat.error_rate else None,
            'is_stat_valid': stat.is_stat_valid,
            'last_practiced_at': stat.last_practiced_at,
        })

    valid_count = sum(1 for r in rows if r[0].is_stat_valid)
    return {
        'student_id': student_id,
        'nickname': student.nickname,
        'grade': student.grade,
        'semester': None,  # Student 模型无 semester 字段
        'stat_summary': {
            'total_kp_count': len(rows),
            'valid_kp_count': valid_count,
            'pending_kp_count': len(rows) - valid_count,
        },
        'subjects': list(subject_map.values()),
    }


# ── AI 提示词摘要 ─────────────────────────────────────────────

async def get_ai_prompt_summary(db: AsyncSession, student_id: int):
    student = (
        await db.execute(select(Student).where(Student.id == student_id))
    ).scalar_one_or_none()
    if not student:
        raise AppException('学生不存在', 404)

    summary = (
        await db.execute(
            select(StudentAiPromptSummary).where(
                StudentAiPromptSummary.student_id == student_id
            )
        )
    ).scalar_one_or_none()

    insights_res = await db.execute(
        select(StudentPromptInsight)
        .where(
            StudentPromptInsight.student_id == student_id,
            StudentPromptInsight.is_active == True,
        )
        .order_by(StudentPromptInsight.created_at.desc())
    )
    insights = insights_res.scalars().all()

    return {
        'student_id': student_id,
        'nickname': student.nickname,
        'is_enabled': summary.is_enabled if summary else True,
        'learning_summary': {
            'content': summary.learning_summary if summary else None,
            'version': summary.learning_summary_version if summary else 0,
            'updated_at': summary.learning_summary_updated_at if summary else None,
        },
        'personal_insight': {
            'content': summary.personal_insight if summary else None,
            'updated_at': summary.personal_insight_updated_at if summary else None,
            'updated_by': summary.insight_updated_by if summary else None,
        },
        'insights': insights,
    }


async def update_personal_insight(db: AsyncSession, student_id: int, content: str):
    student = (
        await db.execute(select(Student).where(Student.id == student_id))
    ).scalar_one_or_none()
    if not student:
        raise AppException('学生不存在', 404)

    summary = (
        await db.execute(
            select(StudentAiPromptSummary).where(
                StudentAiPromptSummary.student_id == student_id
            )
        )
    ).scalar_one_or_none()

    now = datetime.now(UTC)
    if not summary:
        summary = StudentAiPromptSummary(student_id=student_id)
        db.add(summary)
    summary.personal_insight = content
    summary.personal_insight_updated_at = now
    summary.insight_updated_by = 'ADMIN'
    await db.flush()
    return {'updated_at': now, 'updated_by': 'ADMIN'}


async def add_insight_entry(db: AsyncSession, student_id: int, data, operator_id: int):
    student = (
        await db.execute(select(Student).where(Student.id == student_id))
    ).scalar_one_or_none()
    if not student:
        raise AppException('学生不存在', 404)

    entry = StudentPromptInsight(
        student_id=student_id,
        content=data.content,
        insight_type=data.insight_type,
        is_sensitive=data.is_sensitive,
        source='ADMIN',
        added_by_admin_id=operator_id,
    )
    db.add(entry)
    await db.flush()
    return entry


async def get_insight_entries(db: AsyncSession, student_id: int, only_active: bool = True):
    q = select(StudentPromptInsight).where(StudentPromptInsight.student_id == student_id)
    if only_active:
        q = q.where(StudentPromptInsight.is_active == True)
    q = q.order_by(StudentPromptInsight.created_at.desc())
    return (await db.execute(q)).scalars().all()


async def regenerate_learning_summary(db: AsyncSession, student_id: int):
    student = (
        await db.execute(select(Student).where(Student.id == student_id))
    ).scalar_one_or_none()
    if not student:
        raise AppException('学生不存在', 404)

    # 查最新五力画像
    profile = (
        await db.execute(
            select(FivePowerProfile).where(
                FivePowerProfile.student_id == student_id,
                FivePowerProfile.is_latest == True,
            )
        )
    ).scalar_one_or_none()

    # 查训练次数
    from app.models.training import TrainingSession
    training_count = (
        await db.execute(
            select(func.count()).select_from(TrainingSession).where(
                TrainingSession.student_id == student_id
            )
        )
    ).scalar_one()

    # 查有效知识点统计数
    valid_kp_count = (
        await db.execute(
            select(func.count()).select_from(StudentKpStat).where(
                StudentKpStat.student_id == student_id,
                StudentKpStat.is_stat_valid == True,
            )
        )
    ).scalar_one()

    # 构建摘要文本
    grade_map = {
        'G7': '初一', 'G8': '初二', 'G9': '初三',
        'G10': '高一', 'G11': '高二', 'G12': '高三',
    }
    grade_label = grade_map.get(student.grade or '', student.grade or '未知年级')

    profile_text = ''
    if profile:
        # 字段名：insight_final / construct_final / deduce_final / adapt_final / migrate_final
        profile_text = (
            f'五力测试显示洞察力{profile.insight_final}分、'
            f'建构力{profile.construct_final}分、'
            f'推演力{profile.deduce_final}分、'
            f'调适力{profile.adapt_final}分、'
            f'迁移力{profile.migrate_final}分。'
            f'薄弱维度：{profile.primary_weakness or "暂无"}。'
        )

    summary_text = (
        f'学生{student.nickname or "（未知）"}，{grade_label}。'
        f'{profile_text}'
        f'累计训练{training_count}次，'
        f'有效知识点统计{valid_kp_count}个。'
    )

    # 更新数据库记录
    summary = (
        await db.execute(
            select(StudentAiPromptSummary).where(
                StudentAiPromptSummary.student_id == student_id
            )
        )
    ).scalar_one_or_none()

    now = datetime.now(UTC)
    if not summary:
        summary = StudentAiPromptSummary(student_id=student_id)
        db.add(summary)
    summary.learning_summary = summary_text
    summary.learning_summary_version = (summary.learning_summary_version or 0) + 1
    summary.learning_summary_updated_at = now
    await db.flush()

    return {
        'learning_summary': summary_text,
        'version': summary.learning_summary_version,
        'updated_at': now,
    }
