from datetime import date, timedelta
from decimal import Decimal
from app.database import Base, engine, SessionLocal
from app.models import (
    Role,
    Employee,
    Skill,
    RoleSkillTarget,
    EmployeeSkill,
    Course,
    CourseSkill,
    Prerequisite,
    Budget,
)


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Employee).count():
            print("Demo seed skipped: employees already exist.")
            return
        roles = [
            Role(business_id=f"ROL-{i:04d}", name=n, description=f"{n} role")
            for i, n in enumerate(
                ["Junior Developer", "Backend Developer", "Data Analyst"], 1
            )
        ]
        db.add_all(roles)
        skills = [
            Skill(business_id=f"SKL-{i:06d}", name=n, category=c)
            for i, (n, c) in enumerate(
                [
                    ("Python", "Programming"),
                    ("SQL", "Database"),
                    ("REST APIs", "Backend"),
                    ("Testing", "Quality"),
                    ("Cloud Fundamentals", "Cloud"),
                    ("Communication", "Professional"),
                ],
                1,
            )
        ]
        db.add_all(skills)
        db.flush()
        for r in roles:
            for s in skills[:4]:
                db.add(
                    RoleSkillTarget(
                        role_id=r.id,
                        skill_id=s.id,
                        target_level=3 if r.name != "Backend Developer" else 4,
                    )
                )
        emp = Employee(
            business_id="EMP-000001",
            full_name="Alex Morgan",
            email="alex.morgan@example.test",
            department="Engineering",
            role_id=roles[0].id,
            hire_date=date.today() - timedelta(days=400),
        )
        db.add(emp)
        db.flush()
        for s, l in zip(skills, [2, 1, 0, 2, 0, 3]):
            db.add(EmployeeSkill(employee_id=emp.id, skill_id=s.id, current_level=l))
        courses = [
            Course(
                business_id=f"CRS-{i:06d}",
                title=title,
                provider="SkillPath Academy",
                description="Synthetic demo course",
                cost=Decimal(cost),
                duration_hours=hours,
                capacity=cap,
                available_from=date.today() - timedelta(days=20),
                available_until=date.today() + timedelta(days=180),
                is_active=True,
            )
            for i, (title, cost, hours, cap) in enumerate(
                [
                    ("SQL Foundations", "120.00", 8, 30),
                    ("REST API Development", "250.00", 16, 20),
                    ("Advanced Python", "200.00", 12, 25),
                ],
                1,
            )
        ]
        db.add_all(courses)
        db.flush()
        db.add_all(
            [
                CourseSkill(
                    course_id=courses[0].id, skill_id=skills[1].id, target_level=3
                ),
                CourseSkill(
                    course_id=courses[1].id, skill_id=skills[2].id, target_level=3
                ),
                CourseSkill(
                    course_id=courses[2].id, skill_id=skills[0].id, target_level=4
                ),
                Prerequisite(
                    skill_id=skills[2].id,
                    prerequisite_skill_id=skills[1].id,
                    minimum_level=1,
                ),
            ]
        )
        db.add(
            Budget(
                business_id=f"BUD-Engineering-{date.today().year}",
                department="Engineering",
                fiscal_year=date.today().year,
                allocated_amount=Decimal("5000.00"),
                spent_amount=Decimal("0.00"),
            )
        )
        db.commit()
        print("Demo seed created. Use employee ID 1 in the frontend.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
