from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    JSON,
)
from sqlalchemy.orm import relationship
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    business_id = Column(String(30), unique=True, nullable=False, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)


class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True)
    business_id = Column(String(30), unique=True, nullable=False, index=True)
    full_name = Column(String(150), nullable=False)
    email = Column(String(190), unique=True, nullable=False)
    department = Column(String(100), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    hire_date = Column(Date, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    role = relationship("Role")


class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True)
    business_id = Column(String(30), unique=True, nullable=False, index=True)
    name = Column(String(150), unique=True, nullable=False)
    category = Column(String(80), nullable=False)
    description = Column(Text)


class RoleSkillTarget(Base):
    __tablename__ = "role_skill_targets"
    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    target_level = Column(Integer, nullable=False)
    effective_from = Column(Date, nullable=False, default=date.today)
    effective_until = Column(Date)
    __table_args__ = (
        UniqueConstraint(
            "role_id", "skill_id", "effective_from", name="uq_role_skill_effective"
        ),
        CheckConstraint("target_level BETWEEN 1 AND 5", name="ck_target_level"),
        CheckConstraint(
            "effective_until IS NULL OR effective_until >= effective_from",
            name="ck_target_dates",
        ),
    )


class EmployeeSkill(Base):
    __tablename__ = "employee_skills"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    current_level = Column(Integer, nullable=False, default=0)
    assessed_at = Column(DateTime, nullable=False, default=utcnow)
    assessor = Column(String(150), nullable=False, default="system")
    __table_args__ = (
        UniqueConstraint("employee_id", "skill_id", name="uq_employee_skill_current"),
        CheckConstraint("current_level BETWEEN 0 AND 5", name="ck_current_level"),
    )


class SkillAssessment(Base):
    __tablename__ = "skill_assessments"
    id = Column(Integer, primary_key=True)
    business_id = Column(String(40), unique=True, nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    previous_level = Column(Integer)
    assessed_level = Column(Integer, nullable=False)
    assessed_at = Column(DateTime, nullable=False, default=utcnow)
    assessor = Column(String(150), nullable=False)
    source = Column(String(50), nullable=False, default="MANUAL")
    notes = Column(Text)
    __table_args__ = (
        CheckConstraint("assessed_level BETWEEN 0 AND 5", name="ck_assessment_level"),
    )


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True)
    business_id = Column(String(30), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    provider = Column(String(150), nullable=False)
    description = Column(Text)
    cost = Column(Numeric(10, 2), nullable=False, default=Decimal("0"))
    duration_hours = Column(Numeric(7, 2), nullable=False)
    capacity = Column(Integer)
    available_from = Column(Date)
    available_until = Column(Date)
    is_active = Column(Boolean, nullable=False, default=True)
    __table_args__ = (
        CheckConstraint("cost >= 0", name="ck_course_cost"),
        CheckConstraint("duration_hours > 0", name="ck_course_duration"),
        CheckConstraint("capacity IS NULL OR capacity >= 0", name="ck_course_capacity"),
        CheckConstraint(
            "available_until IS NULL OR available_from IS NULL OR available_until >= available_from",
            name="ck_course_dates",
        ),
    )


class CourseSkill(Base):
    __tablename__ = "course_skills"
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    target_level = Column(Integer, nullable=False, default=3)
    __table_args__ = (
        UniqueConstraint("course_id", "skill_id", name="uq_course_skill"),
        CheckConstraint("target_level BETWEEN 1 AND 5", name="ck_course_skill_target"),
    )


class Prerequisite(Base):
    __tablename__ = "prerequisites"
    id = Column(Integer, primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    prerequisite_skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    minimum_level = Column(Integer, nullable=False, default=1)
    __table_args__ = (
        UniqueConstraint(
            "skill_id", "prerequisite_skill_id", name="uq_prerequisite_pair"
        ),
        CheckConstraint(
            "skill_id <> prerequisite_skill_id", name="ck_no_self_prerequisite"
        ),
        CheckConstraint("minimum_level BETWEEN 1 AND 5", name="ck_prereq_level"),
    )


class Budget(Base):
    __tablename__ = "budgets"
    id = Column(Integer, primary_key=True)
    business_id = Column(String(120), unique=True, nullable=False)
    department = Column(String(100), nullable=False)
    fiscal_year = Column(Integer, nullable=False)
    allocated_amount = Column(Numeric(12, 2), nullable=False)
    spent_amount = Column(Numeric(12, 2), nullable=False, default=Decimal("0"))
    __table_args__ = (
        UniqueConstraint("department", "fiscal_year", name="uq_department_year"),
        CheckConstraint("allocated_amount >= 0", name="ck_budget_allocated"),
        CheckConstraint(
            "spent_amount >= 0 AND spent_amount <= allocated_amount",
            name="ck_budget_spent",
        ),
    )


class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(Integer, primary_key=True)
    business_id = Column(String(150), unique=True, nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    enrolled_at = Column(DateTime, nullable=False, default=utcnow)
    status = Column(String(20), nullable=False, default="ENROLLED")
    __table_args__ = (
        UniqueConstraint("employee_id", "course_id", name="uq_employee_course"),
        CheckConstraint(
            "status IN ('ENROLLED','IN_PROGRESS','COMPLETED','CANCELLED')",
            name="ck_enrollment_status",
        ),
    )
    employee = relationship("Employee")
    course = relationship("Course")


class Completion(Base):
    __tablename__ = "completions"
    id = Column(Integer, primary_key=True)
    business_id = Column(String(40), unique=True, nullable=False)
    enrollment_id = Column(
        Integer, ForeignKey("enrollments.id"), unique=True, nullable=False
    )
    completed_at = Column(DateTime, nullable=False, default=utcnow)
    score = Column(Numeric(5, 2))
    outcome = Column(String(30), nullable=False, default="ATTENDED")
    certificate_url = Column(String(500))
    __table_args__ = (
        CheckConstraint(
            "score IS NULL OR (score BETWEEN 0 AND 100)", name="ck_completion_score"
        ),
        CheckConstraint(
            "outcome IN ('ATTENDED','PASSED','FAILED')", name="ck_completion_outcome"
        ),
    )
    enrollment = relationship("Enrollment")


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(Integer, primary_key=True)
    event_type = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_business_id = Column(String(150), nullable=False)
    actor = Column(String(150), nullable=False)
    event_at = Column(DateTime, nullable=False, default=utcnow)
    old_values = Column(JSON)
    new_values = Column(JSON)
    correlation_id = Column(String(80))


class LearningPath(Base):
    __tablename__ = "learning_paths"
    id = Column(Integer, primary_key=True)
    business_id = Column(String(80), unique=True, nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    target_role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=utcnow)
    status = Column(String(20), nullable=False, default="PROPOSED")
    rationale = Column(Text)
    __table_args__ = (
        CheckConstraint(
            "status IN ('PROPOSED','APPROVED','IN_PROGRESS','COMPLETED','CANCELLED')",
            name="ck_learning_path_status",
        ),
    )


class LearningPathCourse(Base):
    __tablename__ = "learning_path_courses"
    id = Column(Integer, primary_key=True)
    learning_path_id = Column(Integer, ForeignKey("learning_paths.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    sequence_no = Column(Integer, nullable=False)
    reason = Column(Text)
    __table_args__ = (
        UniqueConstraint("learning_path_id", "sequence_no", name="uq_path_sequence"),
        UniqueConstraint("learning_path_id", "course_id", name="uq_path_course"),
        CheckConstraint("sequence_no >= 1", name="ck_path_sequence"),
    )
class User(Base):
    __tablename__ = "app_users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(190), unique=True, nullable=False, index=True)
    full_name = Column(String(150), nullable=False)
    password_hash = Column(String(255), nullable=False)

    # Application permissions: Admin, Manager, or Employee
    role = Column(String(20), nullable=False, default="Employee")

    # Optional link to an existing employee record
    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        unique=True,
        nullable=True,
    )

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('Admin', 'Manager', 'Employee')",
            name="ck_app_users_role",
        ),
    )

    employee = relationship("Employee")
