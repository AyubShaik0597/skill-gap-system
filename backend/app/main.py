from datetime import date, datetime, timezone
from contextlib import asynccontextmanager
from decimal import Decimal
import os
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.database import Base, engine, get_db
from app.models import (
    Role,
    Employee,
    Skill,
    RoleSkillTarget,
    EmployeeSkill,
    SkillAssessment,
    Course,
    CourseSkill,
    Prerequisite,
    Budget,
    Enrollment,
    Completion,
    AuditEvent,
    LearningPath,
    LearningPathCourse,
)
from app.schemas import EnrollmentCreate, CompletionCreate, AssessmentCreate
from app.services import audit, gaps_for_employee, recommendations_for_employee
from app.security.dependencies import get_current_user, require_roles
from app.models import User

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="SkillPath Employee Skill Gap & Learning Path System",
    version="1.0.0",
    description="Traceable skill-gap, learning recommendation, enrollment, completion and reassessment workflow.",
    lifespan=lifespan,
)
from app.security.routes import router as auth_router

app.include_router(auth_router)
def ensure_employee_access(
    employee_id: int,
    current_user: User,
) -> None:
    if current_user.role == "Employee":
        if current_user.employee_id != employee_id:
            raise HTTPException(
                status_code=403,
                detail="You cannot access another employee's records.",
            )
origins = [
    x.strip()
    for x in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173",
    ).split(",")
    if x.strip()
]
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"project": "SkillPath", "status": "running", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/api/dashboard/summary")
def dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "Manager")),
):
    return {
        "employees": db.query(Employee).count(),
        "active_employees": db.query(Employee)
        .filter(Employee.is_active.is_(True))
        .count(),
        "roles": db.query(Role).count(),
        "skills": db.query(Skill).count(),
        "courses": db.query(Course).count(),
        "active_courses": db.query(Course).filter(Course.is_active.is_(True)).count(),
        "enrollments": db.query(Enrollment).count(),
        "completions": db.query(Completion).count(),
        "assessments": db.query(SkillAssessment).count(),
        "budgets": db.query(Budget).count(),
    }


@app.get("/api/employees")
def employees(
    search: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(Employee).join(Role, Employee.role_id == Role.id)
    if search:
        q = q.filter(
            (Employee.full_name.ilike(f"%{search}%"))
            | (Employee.business_id.ilike(f"%{search}%"))
            | (Employee.department.ilike(f"%{search}%"))
        )
    return [
        {
            "id": e.id,
            "business_id": e.business_id,
            "full_name": e.full_name,
            "email": e.email,
            "department": e.department,
            "role_id": e.role_id,
            "role": e.role.name,
            "is_active": e.is_active,
        }
        for e in q.order_by(Employee.id).offset(offset).limit(limit).all()
    ]


@app.get("/api/roles")
def roles(db: Session = Depends(get_db)):
    return [
        {
            "id": x.id,
            "business_id": x.business_id,
            "name": x.name,
            "description": x.description,
        }
        for x in db.query(Role).order_by(Role.id).all()
    ]


@app.get("/api/skills")
def skills(limit: int = Query(500, ge=1, le=1000), db: Session = Depends(get_db)):
    return [
        {
            "id": x.id,
            "business_id": x.business_id,
            "name": x.name,
            "category": x.category,
        }
        for x in db.query(Skill).order_by(Skill.id).limit(limit).all()
    ]


@app.get("/api/courses")
def courses(limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)):
    return [
        {
            "id": c.id,
            "business_id": c.business_id,
            "title": c.title,
            "provider": c.provider,
            "cost": float(c.cost),
            "duration_hours": float(c.duration_hours),
            "capacity": c.capacity,
            "available_from": c.available_from,
            "available_until": c.available_until,
            "is_active": c.is_active,
        }
        for c in db.query(Course).order_by(Course.id).limit(limit).all()
    ]


@app.get("/api/employees/{employee_id}/gaps")
def employee_gaps(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_employee_access(employee_id, current_user)

    e = db.get(Employee, employee_id)
    if not e:
        raise HTTPException(404, "Employee not found")

    gaps = gaps_for_employee(db, e)

    return {
        "employee_id": e.id,
        "employee_business_id": e.business_id,
        "employee_name": e.full_name,
        "role": e.role.name,
        "gap_count": len(gaps),
        "gaps": gaps,
    }

@app.get("/api/employees/{employee_id}/recommendations")
def recommendations(
    employee_id: int,
    diagnostics: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_employee_access(employee_id, current_user)

    e = db.get(Employee, employee_id)
    if not e:
        raise HTTPException(404, "Employee not found")

    return recommendations_for_employee(db, e, diagnostics)


@app.get("/api/employees/{employee_id}/career-paths")
def career_paths(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_employee_access(employee_id, current_user)

    e = db.get(Employee, employee_id)
    if not e:
        raise HTTPException(404, "Employee not found")
    current = {
        x.skill_id: x.current_level
        for x in db.query(EmployeeSkill).filter(EmployeeSkill.employee_id == e.id).all()
    }
    out = []
    for role in db.query(Role).filter(Role.id != e.role_id).all():
        targets = (
            db.query(RoleSkillTarget).filter(RoleSkillTarget.role_id == role.id).all()
        )
        if not targets:
            continue
        out.append(
            {
                "role_id": role.id,
                "role": role.name,
                "skills_to_develop": sum(
                    max(0, t.target_level - current.get(t.skill_id, 0)) for t in targets
                ),
                "target_skill_count": len(targets),
            }
        )
    return sorted(out, key=lambda x: (x["skills_to_develop"], x["role"]))


@app.post("/api/employees/{employee_id}/learning-paths")
def create_learning_path(
    employee_id: int,
    target_role_id: int | None = None,
    actor: str = "manager",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("Admin", "Manager")),
):
    try:
        employee = db.get(Employee, employee_id)
        if not employee:
            raise HTTPException(404, "Employee not found")
        role_id = target_role_id or employee.role_id
        target_role = db.get(Role, role_id)
        if not target_role:
            raise HTTPException(404, "Target role not found")
        today = date.today()
        targets = (
            db.query(RoleSkillTarget)
            .filter(
                RoleSkillTarget.role_id == role_id,
                RoleSkillTarget.effective_from <= today,
                (
                    (RoleSkillTarget.effective_until.is_(None))
                    | (RoleSkillTarget.effective_until >= today)
                ),
            )
            .all()
        )
        levels = {
            x.skill_id: x.current_level
            for x in db.query(EmployeeSkill)
            .filter(EmployeeSkill.employee_id == employee.id)
            .all()
        }
        gaps = {
            t.skill_id: max(0, t.target_level - levels.get(t.skill_id, 0))
            for t in targets
            if levels.get(t.skill_id, 0) < t.target_level
        }
        if not gaps:
            raise HTTPException(400, "No skill gaps for the selected target role")
        budget = (
            db.query(Budget)
            .filter(
                Budget.department == employee.department,
                Budget.fiscal_year == today.year,
            )
            .with_for_update()
            .first()
        )
        remaining = (
            budget.allocated_amount - budget.spent_amount if budget else Decimal("0")
        )
        candidates = (
            db.query(Course)
            .join(CourseSkill, CourseSkill.course_id == Course.id)
            .filter(CourseSkill.skill_id.in_(set(gaps)))
            .distinct()
            .all()
        )
        eligible = []
        for course in candidates:
            if (
                not course.is_active
                or (course.available_from and course.available_from > today)
                or (course.available_until and course.available_until < today)
            ):
                continue
            if course.cost > remaining:
                continue
            if (
                course.capacity is not None
                and db.query(Enrollment)
                .filter(
                    Enrollment.course_id == course.id, Enrollment.status != "CANCELLED"
                )
                .count()
                >= course.capacity
            ):
                continue
            maps = (
                db.query(CourseSkill)
                .filter(
                    CourseSkill.course_id == course.id,
                    CourseSkill.skill_id.in_(set(gaps)),
                )
                .all()
            )
            matched = [m for m in maps if levels.get(m.skill_id, 0) < m.target_level]
            if not matched:
                continue
            prereq_ok = True
            for m in (
                db.query(CourseSkill).filter(CourseSkill.course_id == course.id).all()
            ):
                for pre in (
                    db.query(Prerequisite)
                    .filter(Prerequisite.skill_id == m.skill_id)
                    .all()
                ):
                    if levels.get(pre.prerequisite_skill_id, 0) < pre.minimum_level:
                        prereq_ok = False
            if not prereq_ok:
                continue
            eligible.append((course, matched))
        eligible.sort(key=lambda x: (-len(x[1]), x[0].cost, x[0].title))
        selected = []
        covered = set()
        total = Decimal("0")
        for course, matches in eligible:
            newskills = {m.skill_id for m in matches} - covered
            if not newskills:
                continue
            if total + course.cost > remaining:
                continue
            selected.append((course, newskills))
            covered |= newskills
            total += course.cost
            if covered >= set(gaps):
                break
        if not selected:
            raise HTTPException(
                422,
                "No feasible course sequence fits the current prerequisites, availability, capacity and budget",
            )
        seq = db.query(LearningPath).count() + 1
        path = LearningPath(
            business_id=f"LNP-{employee.business_id}-{today.year}-{seq:06d}",
            employee_id=employee.id,
            target_role_id=role_id,
            status="PROPOSED",
            rationale=f"Covers {len(covered)} of {len(gaps)} target-role skill gaps within remaining budget.",
        )
        db.add(path)
        db.flush()
        for idx, (course, skill_ids) in enumerate(selected, 1):
            db.add(
                LearningPathCourse(
                    learning_path_id=path.id,
                    course_id=course.id,
                    sequence_no=idx,
                    reason="Targets "
                    + ", ".join(
                        db.query(Skill.name).filter(Skill.id.in_(skill_ids)).all()[i][0]
                        for i in range(len(skill_ids))
                    ),
                )
            )
        audit(
            db,
            "LEARNING_PATH_PROPOSED",
            "LearningPath",
            path.business_id,
            actor,
            None,
            {
                "target_role_id": role_id,
                "course_ids": [x[0].id for x in selected],
                "estimated_cost": str(total),
            },
        )
        db.commit()
        return {
            "business_id": path.business_id,
            "status": path.status,
            "target_role": target_role.name,
            "covered_skill_count": len(covered),
            "open_gap_skill_count": len(gaps),
            "estimated_cost": float(total),
            "courses": [
                {
                    "sequence": i + 1,
                    "course_id": c.id,
                    "course_business_id": c.business_id,
                    "title": c.title,
                    "cost": float(c.cost),
                    "duration_hours": float(c.duration_hours),
                    "skills_covered": sorted(sids),
                }
                for i, (c, sids) in enumerate(selected)
            ],
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


@app.get("/api/employees/{employee_id}/learning-paths")
def list_learning_paths(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ensure_employee_access(employee_id, current_user)

    if not db.get(Employee, employee_id):
        raise HTTPException(404, "Employee not found")

    paths = (
        db.query(LearningPath)
        .filter(LearningPath.employee_id == employee_id)
        .order_by(LearningPath.id.desc())
        .all()
    )

    result = []
    for p in paths:
        items = (
            db.query(LearningPathCourse, Course)
            .join(Course, Course.id == LearningPathCourse.course_id)
            .filter(LearningPathCourse.learning_path_id == p.id)
            .order_by(LearningPathCourse.sequence_no)
            .all()
        )

        result.append(
            {
                "business_id": p.business_id,
                "target_role_id": p.target_role_id,
                "status": p.status,
                "created_at": p.created_at,
                "rationale": p.rationale,
                "courses": [
                    {
                        "sequence": i.sequence_no,
                        "course_business_id": c.business_id,
                        "title": c.title,
                        "reason": i.reason,
                    }
                    for i, c in items
                ],
            }
        )

    return result

@app.post("/api/enrollments")
def create_enrollment(p: EnrollmentCreate, db: Session = Depends(get_db)):
    try:
        today = date.today()
        e = (
            db.query(Employee)
            .filter(Employee.id == p.employee_id)
            .with_for_update()
            .first()
        )
        c = db.query(Course).filter(Course.id == p.course_id).with_for_update().first()
        if not e:
            raise HTTPException(404, "Employee not found")
        if not c:
            raise HTTPException(404, "Course not found")
        if not e.is_active:
            raise HTTPException(400, "Employee is inactive")
        if not c.is_active:
            raise HTTPException(400, "Course is inactive")
        if c.available_from and c.available_from > today:
            raise HTTPException(400, "Course is not yet available")
        if c.available_until and c.available_until < today:
            raise HTTPException(400, "Course availability expired")
        existing = (
            db.query(Enrollment)
            .filter(Enrollment.employee_id == e.id, Enrollment.course_id == c.id)
            .first()
        )
        if existing and existing.status != "CANCELLED":
            raise HTTPException(409, "Employee already has an active enrollment")
        if (
            c.capacity is not None
            and db.query(Enrollment)
            .filter(Enrollment.course_id == c.id, Enrollment.status != "CANCELLED")
            .count()
            >= c.capacity
        ):
            raise HTTPException(409, "Course capacity reached")
        levels = {
            x.skill_id: x.current_level
            for x in db.query(EmployeeSkill)
            .filter(EmployeeSkill.employee_id == e.id)
            .all()
        }
        for m in db.query(CourseSkill).filter(CourseSkill.course_id == c.id).all():
            for pre in (
                db.query(Prerequisite).filter(Prerequisite.skill_id == m.skill_id).all()
            ):
                if levels.get(pre.prerequisite_skill_id, 0) < pre.minimum_level:
                    raise HTTPException(
                        400,
                        f"Missing prerequisite skill ID {pre.prerequisite_skill_id}; required level {pre.minimum_level}",
                    )
        b = (
            db.query(Budget)
            .filter(Budget.department == e.department, Budget.fiscal_year == today.year)
            .with_for_update()
            .first()
        )
        if not b:
            raise HTTPException(400, "No current-year department budget")
        cost = Decimal(str(c.cost))
        if b.spent_amount + cost > b.allocated_amount:
            raise HTTPException(400, "Insufficient department learning budget")
        old = {"status": existing.status} if existing else None
        if existing:
            existing.status = "ENROLLED"
            existing.enrolled_at = datetime.now(timezone.utc).replace(tzinfo=None)
            en = existing
            event = "ENROLLMENT_REACTIVATED"
        else:
            en = Enrollment(
                business_id=f"ENR-{e.business_id}-{c.business_id}",
                employee_id=e.id,
                course_id=c.id,
                status="ENROLLED",
            )
            db.add(en)
            event = "ENROLLMENT_CREATED"
        b.spent_amount += cost
        db.flush()
        audit(
            db,
            event,
            "Enrollment",
            en.business_id,
            p.actor,
            old,
            {
                "status": "ENROLLED",
                "course_cost": str(cost),
                "department": e.department,
            },
        )
        db.commit()
        db.refresh(en)
        return {
            "id": en.id,
            "business_id": en.business_id,
            "status": en.status,
            "remaining_budget": float(b.allocated_amount - b.spent_amount),
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


@app.post("/api/enrollments/{enrollment_id}/cancel")
def cancel_enrollment(
    enrollment_id: int, actor: str = "employee", db: Session = Depends(get_db)
):
    try:
        e = (
            db.query(Enrollment)
            .filter(Enrollment.id == enrollment_id)
            .with_for_update()
            .first()
        )
        if not e:
            raise HTTPException(404, "Enrollment not found")
        if e.status == "CANCELLED":
            raise HTTPException(409, "Enrollment already cancelled")
        if e.status == "COMPLETED":
            raise HTTPException(400, "Completed enrollment cannot be cancelled")
        b = (
            db.query(Budget)
            .filter(
                Budget.department == e.employee.department,
                Budget.fiscal_year == date.today().year,
            )
            .with_for_update()
            .first()
        )
        if b:
            b.spent_amount = max(
                Decimal("0"), b.spent_amount - Decimal(str(e.course.cost))
            )
        old = {"status": e.status}
        e.status = "CANCELLED"
        audit(
            db,
            "ENROLLMENT_CANCELLED",
            "Enrollment",
            e.business_id,
            actor,
            old,
            {"status": "CANCELLED", "budget_refund": str(e.course.cost)},
        )
        db.commit()
        return {
            "business_id": e.business_id,
            "status": e.status,
            "budget_refund": float(e.course.cost),
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


@app.post("/api/enrollments/{enrollment_id}/complete")
def complete_enrollment(
    enrollment_id: int, p: CompletionCreate, db: Session = Depends(get_db)
):
    try:
        e = (
            db.query(Enrollment)
            .filter(Enrollment.id == enrollment_id)
            .with_for_update()
            .first()
        )
        if not e:
            raise HTTPException(404, "Enrollment not found")
        if e.status == "CANCELLED":
            raise HTTPException(400, "Cancelled enrollment cannot be completed")
        if db.query(Completion).filter(Completion.enrollment_id == e.id).first():
            raise HTTPException(409, "Completion already recorded")
        seq = db.query(Completion).count() + 1
        comp = Completion(
            business_id=f"CMP-{date.today().year}-{seq:06d}",
            enrollment_id=e.id,
            score=p.score,
            outcome=p.outcome,
            certificate_url=p.certificate_url,
        )
        e.status = "COMPLETED"
        db.add(comp)
        db.flush()
        audit(
            db,
            "COURSE_COMPLETED",
            "Completion",
            comp.business_id,
            p.actor,
            None,
            {
                "enrollment": e.business_id,
                "outcome": p.outcome,
                "score": str(p.score) if p.score is not None else None,
            },
        )
        db.commit()
        return {
            "completion_id": comp.id,
            "business_id": comp.business_id,
            "enrollment_status": e.status,
            "outcome": comp.outcome,
            "note": "Completion does not automatically improve proficiency; record reassessment separately.",
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


@app.post("/api/employees/{employee_id}/skills/{skill_id}/assessments")
def reassess(
    employee_id: int, skill_id: int, p: AssessmentCreate, db: Session = Depends(get_db)
):
    try:
        e = db.get(Employee, employee_id)
        s = db.get(Skill, skill_id)
        if not e:
            raise HTTPException(404, "Employee not found")
        if not s:
            raise HTTPException(404, "Skill not found")
        cur = (
            db.query(EmployeeSkill)
            .filter(
                EmployeeSkill.employee_id == employee_id,
                EmployeeSkill.skill_id == skill_id,
            )
            .first()
        )
        old_level = cur.current_level if cur else None
        seq = db.query(SkillAssessment).count() + 1
        a = SkillAssessment(
            business_id=f"ASM-{date.today().year}-{seq:06d}",
            employee_id=employee_id,
            skill_id=skill_id,
            previous_level=old_level,
            assessed_level=p.level,
            assessor=p.assessor,
            source=p.source,
            notes=p.notes,
        )
        db.add(a)
        if cur:
            cur.current_level = p.level
            cur.assessed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            cur.assessor = p.assessor
        else:
            cur = EmployeeSkill(
                employee_id=employee_id,
                skill_id=skill_id,
                current_level=p.level,
                assessed_at=datetime.now(timezone.utc).replace(tzinfo=None),
                assessor=p.assessor,
            )
            db.add(cur)
        db.flush()
        audit(
            db,
            "SKILL_REASSESSED",
            "SkillAssessment",
            a.business_id,
            p.assessor,
            {"level": old_level},
            {"level": p.level, "skill": s.name},
        )
        db.commit()
        return {
            "assessment_id": a.id,
            "business_id": a.business_id,
            "previous_level": old_level,
            "assessed_level": p.level,
            "skill": s.name,
            "updated_at": cur.assessed_at,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


@app.get("/api/employees/{employee_id}/assessments")
def assessment_history(employee_id: int, db: Session = Depends(get_db)):
    if not db.get(Employee, employee_id):
        raise HTTPException(404, "Employee not found")
    rows = (
        db.query(SkillAssessment, Skill)
        .join(Skill, Skill.id == SkillAssessment.skill_id)
        .filter(SkillAssessment.employee_id == employee_id)
        .order_by(SkillAssessment.assessed_at.desc())
        .all()
    )
    return [
        {
            "business_id": a.business_id,
            "skill": s.name,
            "previous_level": a.previous_level,
            "assessed_level": a.assessed_level,
            "assessed_at": a.assessed_at,
            "assessor": a.assessor,
            "source": a.source,
            "notes": a.notes,
        }
        for a, s in rows
    ]


@app.get("/api/budgets")
def budgets(db: Session = Depends(get_db)):
    return [
        {
            "business_id": b.business_id,
            "department": b.department,
            "fiscal_year": b.fiscal_year,
            "allocated": float(b.allocated_amount),
            "spent": float(b.spent_amount),
            "remaining": float(b.allocated_amount - b.spent_amount),
        }
        for b in db.query(Budget).order_by(Budget.department).all()
    ]


@app.get("/api/audit-events")
def audit_events(limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    return [
        {
            "id": a.id,
            "event_type": a.event_type,
            "entity_type": a.entity_type,
            "entity_business_id": a.entity_business_id,
            "actor": a.actor,
            "event_at": a.event_at,
            "old_values": a.old_values,
            "new_values": a.new_values,
        }
        for a in db.query(AuditEvent).order_by(AuditEvent.id.desc()).limit(limit).all()
    ]


@app.get("/api/evaluation/metrics")
def metrics(db: Session = Depends(get_db)):
    active = db.query(Employee).filter(Employee.is_active.is_(True)).count()
    enroll = db.query(Enrollment).filter(Enrollment.status != "CANCELLED").count()
    comps = db.query(Completion).count()
    allocated = sum((b.allocated_amount for b in db.query(Budget).all()), Decimal("0"))
    spent = sum((b.spent_amount for b in db.query(Budget).all()), Decimal("0"))
    gap_count = 0
    for e in db.query(Employee).filter(Employee.is_active.is_(True)).limit(1000).all():
        gap_count += len(gaps_for_employee(db, e))
    return {
        "active_employees": active,
        "active_enrollments": enroll,
        "completions": comps,
        "completion_rate": round(comps / enroll, 4) if enroll else 0,
        "open_skill_gaps_sample_up_to_1000_employees": gap_count,
        "budget_allocated": float(allocated),
        "budget_spent": float(spent),
        "budget_utilization": round(float(spent / allocated), 4) if allocated else 0,
        "note": "Course completion and proficiency improvement are separate outcomes.",
    }
