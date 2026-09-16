def test_models_import():
    from app.models import (
        AdminAuditLog,
        AdminUser,
        AiHeuristicStrategy,
        Chapter,
        CognitiveTestQuestion,
        Grade,
        KnowledgePoint,
        Question,
        Semester,
        Student,
        Subject,
        SystemConfig,
        TrainingDimensionConfig,
    )

    # 验证表名映射正确
    assert AdminUser.__tablename__ == "admin_users"
    assert Question.__tablename__ == "questions"
    assert CognitiveTestQuestion.__tablename__ == "cognitive_test_questions"
    assert Subject.__tablename__ == "subjects"
    assert Grade.__tablename__ == "grades"
    assert Semester.__tablename__ == "semesters"
    assert Chapter.__tablename__ == "chapters"
    assert KnowledgePoint.__tablename__ == "knowledge_points"
    assert TrainingDimensionConfig.__tablename__ == "training_dimension_configs"
    assert Student.__tablename__ == "students"
    assert AdminAuditLog.__tablename__ == "admin_audit_logs"
    assert AiHeuristicStrategy.__tablename__ == "ai_heuristic_strategies"
    assert SystemConfig.__tablename__ == "system_configs"


def test_all_models_importable():
    """验证所有 34 张表的 ORM 模型均可导入"""
    from app.models import (
        ParentStudentBinding,
        # Question
        Question,
        Student,
        TrainingSession,
        WrongAnswerRecord,
    )

    # 验证所有表名
    assert ParentStudentBinding.__tablename__ == "parent_student_bindings"
    assert Question.deleted_at is not None  # soft-delete 字段存在
    assert Student.deleted_at is not None  # soft-delete 字段存在
    assert ParentStudentBinding.deleted_at is not None  # soft-delete 字段存在
    assert TrainingSession.__tablename__ == "training_sessions"
    assert WrongAnswerRecord.__tablename__ == "wrong_answer_records"
