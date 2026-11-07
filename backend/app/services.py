from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models import (
    Employee,
    Skill,
    RoleSkillTarget,
    EmployeeSkill,
    Course,
    CourseSkill,
    Prerequisite,
    Enrollment,
    Budget,
)


def audit(db, event_type, entity_type, business_id, actor, old=None, new=None):
    from app.models import AuditEvent

    db.add(
        AuditEvent(
            event_type=event_type,
            entity_type=entity_type,
            entity_business_id=business_id,
            actor=actor,
            old_values=old,
            new_values=new,
        )
    )


def gaps_for_employee(db: Session, employee: Employee):
    today = date.today()
    targets = (
        db.query(RoleSkillTarget, Skill)
        .join(Skill, Skill.id == RoleSkillTarget.skill_id)
        .filter(
            RoleSkillTarget.role_id == employee.role_id,
            RoleSkillTarget.effective_from <= today,
            (
                (RoleSkillTarget.effective_until.is_(None))
                | (RoleSkillTarget.effective_until >= today)
            ),
        )
        .all()
    )
    current = {
        x.skill_id: x.current_level
        for x in db.query(EmployeeSkill)
        .filter(EmployeeSkill.employee_id == employee.id)
        .all()
    }
    result = []
    for target, skill in targets:
        level = current.get(skill.id, 0)
        gap = max(0, target.target_level - level)
        if gap:
            result.append(
                {
                    "skill_id": skill.id,
                    "skill_business_id": skill.business_id,
                    "skill": skill.name,
                    "current_level": level,
                    "target_level": target.target_level,
                    "gap": gap,
                }
            )
    return sorted(result, key=lambda x: (-x["gap"], x["skill"]))


def recommendations_for_employee(db, employee, diagnostics=False):
    from datetime import date

    gaps = gaps_for_employee(db, employee)
    needed = {g["skill_id"] for g in gaps}
    budget = (
        db.query(Budget)
        .filter(
            Budget.department == employee.department,
            Budget.fiscal_year == date.today().year,
        )
        .first()
    )
    remaining = (
        budget.allocated_amount - budget.spent_amount if budget else Decimal("0")
    )
    candidates = (
        db.query(Course)
        .join(CourseSkill, CourseSkill.course_id == Course.id)
        .filter(CourseSkill.skill_id.in_(needed or {-1}))
        .distinct()
        .all()
    )
    levels = {
        s.skill_id: s.current_level
        for s in db.query(EmployeeSkill)
        .filter(EmployeeSkill.employee_id == employee.id)
        .all()
    }
    recs = []
    rejected = []
    for course in candidates:
        mappings = (
            db.query(CourseSkill)
            .filter(
                CourseSkill.course_id == course.id,
                CourseSkill.skill_id.in_(needed or {-1}),
            )
            .all()
        )
        matched = [m for m in mappings if levels.get(m.skill_id, 0) < m.target_level]
        if not matched:
            continue
        reasons = []
        if not course.is_active:
            reasons.append("COURSE_INACTIVE")
        if course.available_from and course.available_from > date.today():
            reasons.append("NOT_YET_AVAILABLE")
        if course.available_until and course.available_until < date.today():
            reasons.append("AVAILABILITY_EXPIRED")
        if course.cost > remaining:
            reasons.append("BUDGET_EXCEEDED")
        if (
            course.capacity is not None
            and db.query(Enrollment)
            .filter(Enrollment.course_id == course.id, Enrollment.status != "CANCELLED")
            .count()
            >= course.capacity
        ):
            reasons.append("CAPACITY_FULL")
        if (
            db.query(Enrollment)
            .filter(
                Enrollment.employee_id == employee.id,
                Enrollment.course_id == course.id,
                Enrollment.status != "CANCELLED",
            )
            .first()
        ):
            reasons.append("ALREADY_ENROLLED")
        for mapping in (
            db.query(CourseSkill).filter(CourseSkill.course_id == course.id).all()
        ):
            for p in (
                db.query(Prerequisite)
                .filter(Prerequisite.skill_id == mapping.skill_id)
                .all()
            ):
                if levels.get(p.prerequisite_skill_id, 0) < p.minimum_level:
                    reasons.append(
                        f"PREREQUISITE_MISSING:{p.prerequisite_skill_id}:{p.minimum_level}"
                    )
        if reasons:
            rejected.append(
                {
                    "course_id": course.id,
                    "course_business_id": course.business_id,
                    "title": course.title,
                    "reasons": sorted(set(reasons)),
                }
            )
            continue
        recs.append(
            {
                "course_id": course.id,
                "course_business_id": course.business_id,
                "title": course.title,
                "provider": course.provider,
                "cost": float(course.cost),
                "duration_hours": float(course.duration_hours),
                "matched_skills": [
                    g["skill"]
                    for g in gaps
                    if g["skill_id"] in {m.skill_id for m in matched}
                ],
                "matched_skill_count": len(matched),
            }
        )
    recs.sort(key=lambda x: (-x["matched_skill_count"], x["cost"], x["title"]))
    return {
        "remaining_budget": float(remaining),
        "recommendations": recs,
        "rejected_courses": rejected if diagnostics else [],
    }
