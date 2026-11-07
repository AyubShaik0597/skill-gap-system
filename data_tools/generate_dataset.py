#!/usr/bin/env python3
"""Deterministic synthetic SkillPath data generator. Never connects to application DB."""

import argparse, csv, json, random, hashlib, shutil
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

FULL = {
    "roles": 10,
    "employees": 5000,
    "skills": 500,
    "courses": 1000,
    "enrollments": 10000,
}
STARTER = {"roles": 5, "employees": 50, "skills": 25, "courses": 50, "enrollments": 100}
DEPARTMENTS = ["Engineering", "Data", "Operations", "Product", "Customer Success"]
ROLE_NAMES = [
    "Junior Developer",
    "Backend Developer",
    "Frontend Developer",
    "QA Engineer",
    "Data Analyst",
    "Data Engineer",
    "DevOps Engineer",
    "Product Analyst",
    "Support Engineer",
    "Engineering Manager",
]
SKILL_NAMES = [
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "SQL",
    "MySQL",
    "REST APIs",
    "FastAPI",
    "Spring Boot",
    "React",
    "Angular",
    "Docker",
    "Kubernetes",
    "AWS",
    "Azure",
    "Git",
    "Linux",
    "Testing",
    "Playwright",
    "Selenium",
    "Data Analysis",
    "Pandas",
    "Excel",
    "Communication",
    "Problem Solving",
    "System Design",
    "Security",
    "CI/CD",
    "Agile",
    "Project Management",
]
CATEGORIES = [
    "Programming",
    "Database",
    "Backend",
    "Frontend",
    "Cloud",
    "Quality",
    "Data",
    "Professional",
    "DevOps",
    "Architecture",
]


def write_rows(out, name, rows):
    if not rows:
        return
    cols = list(rows[0].keys())
    with (out / f"{name}.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    (out / f"{name}.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )


def generate(scale="starter", seed=20261022, out_dir="generated"):
    cfg = FULL if scale == "full" else STARTER
    rng = random.Random(seed)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for p in out.iterdir():
        if p.is_file():
            p.unlink()
        elif p.is_dir():
            shutil.rmtree(p)
    today = date(2026, 1, 1)
    roles = [
        {
            "id": i,
            "business_id": f"ROL-{i:04d}",
            "name": (
                ROLE_NAMES[i - 1]
                if i <= len(ROLE_NAMES)
                else f"Specialist Role {i:03d}"
            ),
            "description": "Synthetic role profile",
        }
        for i in range(1, cfg["roles"] + 1)
    ]
    skills = []
    for i in range(1, cfg["skills"] + 1):
        name = (
            SKILL_NAMES[i - 1]
            if i <= len(SKILL_NAMES)
            else f"Specialized Skill {i:03d}"
        )
        skills.append(
            {
                "id": i,
                "business_id": f"SKL-{i:06d}",
                "name": name,
                "category": CATEGORIES[(i - 1) % len(CATEGORIES)],
                "description": f"Synthetic competency: {name}",
            }
        )
    departments = DEPARTMENTS[: min(len(DEPARTMENTS), max(1, cfg["roles"] // 2))]
    employees = []
    for i in range(1, cfg["employees"] + 1):
        role_id = rng.randint(1, cfg["roles"])
        dept = departments[(i - 1) % len(departments)]
        employees.append(
            {
                "id": i,
                "business_id": f"EMP-{i:06d}",
                "full_name": f"Employee {i:05d}",
                "email": f"employee{i:05d}@example.test",
                "department": dept,
                "role_id": role_id,
                "hire_date": str(
                    date(2018, 1, 1) + timedelta(days=rng.randint(0, 2900))
                ),
                "is_active": rng.random() > 0.04,
                "created_at": "2026-01-01T00:00:00",
            }
        )
    role_targets = []
    rt_id = 1
    for r in roles:
        count = min(35, cfg["skills"])
        chosen = rng.sample(range(1, cfg["skills"] + 1), count)
        for sid in chosen:
            role_targets.append(
                {
                    "id": rt_id,
                    "role_id": r["id"],
                    "skill_id": sid,
                    "target_level": rng.randint(2, 5),
                    "effective_from": "2026-01-01",
                    "effective_until": "",
                }
            )
            rt_id += 1
    employee_skills = []
    profile = {}
    esid = 1
    for e in employees:
        n = min(
            cfg["skills"], rng.randint(min(8, cfg["skills"]), min(20, cfg["skills"]))
        )
        for sid in rng.sample(range(1, cfg["skills"] + 1), n):
            lvl = rng.randint(0, 5)
            profile[(e["id"], sid)] = lvl
            employee_skills.append(
                {
                    "id": esid,
                    "employee_id": e["id"],
                    "skill_id": sid,
                    "current_level": lvl,
                    "assessed_at": f"2026-{rng.randint(1,10):02d}-{rng.randint(1,28):02d}T12:00:00",
                    "assessor": "synthetic-baseline",
                }
            )
            esid += 1
    prerequisites = []
    # Acyclic graph: higher skill ID may depend only on lower skill ID.
    for sid in range(2, cfg["skills"] + 1):
        if rng.random() < 0.20:
            prereq = rng.randint(1, sid - 1)
            prerequisites.append(
                {
                    "id": len(prerequisites) + 1,
                    "skill_id": sid,
                    "prerequisite_skill_id": prereq,
                    "minimum_level": 1,
                }
            )
    courses = []
    course_skills = []
    for i in range(1, cfg["courses"] + 1):
        start = date(2026, rng.randint(1, 9), rng.randint(1, 20))
        end = min(date(2027, 1, 1), start + timedelta(days=rng.randint(60, 250)))
        courses.append(
            {
                "id": i,
                "business_id": f"CRS-{i:06d}",
                "title": f'{skills[(i-1)%len(skills)]["name"]} {rng.choice(["Foundations","Applied Workshop","Professional Practice","Advanced Lab"])} {i:04d}',
                "provider": rng.choice(
                    [
                        "SkillPath Academy",
                        "Open Learning Lab",
                        "TechWorks Training",
                        "Professional Skills Institute",
                    ]
                ),
                "description": "Synthetic course record for workflow evaluation",
                "cost": f"{rng.randrange(50,801,25):.2f}",
                "duration_hours": f"{rng.randrange(2,41,2):.2f}",
                "capacity": rng.choice([15, 20, 25, 30, 40, 50, None]),
                "available_from": str(start),
                "available_until": str(end),
                "is_active": rng.random() > 0.05,
            }
        )
        for sid in rng.sample(
            range(1, cfg["skills"] + 1), min(rng.randint(1, 3), cfg["skills"])
        ):
            course_skills.append(
                {
                    "id": len(course_skills) + 1,
                    "course_id": i,
                    "skill_id": sid,
                    "target_level": rng.randint(2, 5),
                }
            )
    budgets = []
    for d in departments:
        budgets.append(
            {
                "id": len(budgets) + 1,
                "business_id": f"BUD-{d}-2026",
                "department": d,
                "fiscal_year": 2026,
                "allocated_amount": "2000000.00",
                "spent_amount": "0.00",
            }
        )
    # Baseline enrollments are only created when course is available, prerequisites are satisfied and capacity/budget permits.
    cs_by_course = {}
    for m in course_skills:
        cs_by_course.setdefault(m["course_id"], []).append(m)
    pre_by_skill = {}
    for p in prerequisites:
        pre_by_skill.setdefault(p["skill_id"], []).append(p)
    capacities = {c["id"]: 0 for c in courses}
    used_pairs = set()
    spending = {d: Decimal("0") for d in departments}
    enrollments = []
    completions = []
    completion_seq = 1
    eligible_courses = [c for c in courses if c["is_active"]]
    attempts = 0
    max_attempts = cfg["enrollments"] * 100
    while len(enrollments) < cfg["enrollments"] and attempts < max_attempts:
        attempts += 1
        e = employees[rng.randrange(len(employees))]
        c = eligible_courses[rng.randrange(len(eligible_courses))]
        pair = (e["id"], c["id"])
        if pair in used_pairs:
            continue
        if c["capacity"] is not None and capacities[c["id"]] >= c["capacity"]:
            continue
        if spending[e["department"]] + Decimal(c["cost"]) > Decimal("2000000.00"):
            continue
        mappings = cs_by_course.get(c["id"], [])
        ok = True
        for m in mappings:
            for p in pre_by_skill.get(m["skill_id"], []):
                if (
                    profile.get((e["id"], p["prerequisite_skill_id"]), 0)
                    < p["minimum_level"]
                ):
                    ok = False
                    break
            if not ok:
                break
        if not ok:
            continue
        start = date.fromisoformat(c["available_from"])
        end = date.fromisoformat(c["available_until"])
        enrolled_day = start + timedelta(
            days=rng.randint(0, max(0, (end - start).days))
        )
        status = rng.choices(
            ["COMPLETED", "IN_PROGRESS", "ENROLLED"], weights=[20, 20, 60]
        )[0]
        seq = len(enrollments) + 1
        eid = f'ENR-{e["business_id"]}-{c["business_id"]}'
        enrollments.append(
            {
                "id": seq,
                "business_id": eid,
                "employee_id": e["id"],
                "course_id": c["id"],
                "enrolled_at": f"{enrolled_day}T10:00:00",
                "status": status,
            }
        )
        used_pairs.add(pair)
        capacities[c["id"]] += 1
        spending[e["department"]] += Decimal(c["cost"])
        if status == "COMPLETED":
            score = round(rng.uniform(55, 100), 2)
            outcome = "PASSED" if score >= 70 else "FAILED"
            completions.append(
                {
                    "id": len(completions) + 1,
                    "business_id": f"CMP-2026-{completion_seq:06d}",
                    "enrollment_id": seq,
                    "completed_at": f"{enrolled_day+timedelta(days=rng.randint(1,30))}T15:00:00",
                    "score": f"{score:.2f}",
                    "outcome": outcome,
                    "certificate_url": "",
                }
            )
            completion_seq += 1
    if len(enrollments) < cfg["enrollments"]:
        raise RuntimeError(
            f"Could only create {len(enrollments)} enrollments after {attempts} attempts. Increase capacity or adjust scale."
        )
    for b in budgets:
        b["spent_amount"] = f'{spending[b["department"]]:.2f}'
    tables = {
        "roles": roles,
        "employees": employees,
        "skills": skills,
        "role_skill_targets": role_targets,
        "employee_skills": employee_skills,
        "courses": courses,
        "course_skills": course_skills,
        "prerequisites": prerequisites,
        "enrollments": enrollments,
        "completions": completions,
        "budgets": budgets,
    }
    for name, rows in tables.items():
        write_rows(out, name, rows)
    ground_truth = [
        {
            "case_id": "ANOM-001",
            "issue_type": "RECOMMENDATION_PREREQUISITE_VIOLATION",
            "input_fixture": "employee has skill level below prerequisite minimum",
            "expected_decision": "REJECT_RECOMMENDATION",
            "expected_reason": "PREREQUISITE_MISSING",
            "label": 1,
        },
        {
            "case_id": "ANOM-002",
            "issue_type": "BUDGET_EXCEEDED",
            "input_fixture": "course cost exceeds department remaining budget",
            "expected_decision": "REJECT_ENROLLMENT",
            "expected_reason": "INSUFFICIENT_BUDGET",
            "label": 1,
        },
        {
            "case_id": "ANOM-003",
            "issue_type": "DUPLICATE_COMPLETION",
            "input_fixture": "two completion events reference one enrollment",
            "expected_decision": "REJECT_SECOND_COMPLETION",
            "expected_reason": "COMPLETION_ALREADY_RECORDED",
            "label": 1,
        },
        {
            "case_id": "ANOM-004",
            "issue_type": "GAP_WITHOUT_REASSESSMENT",
            "input_fixture": "course completed but current proficiency has no subsequent assessment event",
            "expected_decision": "KEEP_GAP_OPEN",
            "expected_reason": "REASSESSMENT_REQUIRED",
            "label": 1,
        },
        {
            "case_id": "ANOM-005",
            "issue_type": "COURSE_UNAVAILABLE_IN_PLANNING_PERIOD",
            "input_fixture": "course availability window does not intersect planning period",
            "expected_decision": "EXCLUDE_COURSE",
            "expected_reason": "COURSE_UNAVAILABLE",
            "label": 1,
        },
    ]
    write_rows(out, "ground_truth", ground_truth)
    scenarios = [
        {
            "case_id": x["case_id"],
            "issue_type": x["issue_type"],
            "scenario_data": x["input_fixture"],
            "expected_decision": x["expected_decision"],
            "expected_reason": x["expected_reason"],
        }
        for x in ground_truth
    ]
    write_rows(out, "scenario_fixtures", scenarios)
    # SQL seed is portable-ish MySQL INSERT statements for core baseline tables. Import in parent-to-child order.
    order = [
        "roles",
        "skills",
        "employees",
        "role_skill_targets",
        "employee_skills",
        "courses",
        "course_skills",
        "prerequisites",
        "budgets",
        "enrollments",
        "completions",
    ]
    sql = []
    for table in order:
        for row in tables[table]:
            cols = list(row.keys())
            vals = []
            for v in row.values():
                if v is None:
                    vals.append("NULL")
                elif isinstance(v, (int, float)):
                    vals.append(str(v))
                else:
                    vals.append(
                        "'" + str(v).replace("\\", "\\\\").replace("'", "''") + "'"
                    )
            sql.append(
                f"INSERT INTO `{table}` ({','.join('`'+c+'`' for c in cols)}) VALUES ({','.join(vals)});"
            )
    (out / "seed.sql").write_text("\n".join(sql) + "\n", encoding="utf-8")
    # Data dictionary, source manifest and validation summary are versioned generated artifacts.
    dictionary = """# Data dictionary\n\nLevels use integer scale 0–5. Dates use ISO 8601; monetary values are decimal currency units (INR for demo). Blank values mean not supplied where a field is optional. Business IDs are immutable and unique.\n\n| Entity | Field | Type | Required | Uniqueness / allowed values | Validation |\n|---|---|---|---|---|---|\n"""
    specs = {
        "Employee": [
            ("id", "integer", "yes", "PK", "positive"),
            ("business_id", "string", "yes", "unique EMP-000001", "immutable"),
            ("full_name", "string", "yes", "—", "non-empty"),
            ("email", "string", "yes", "unique", "email-shaped synthetic address"),
            ("department", "string", "yes", "department name", "must have budget"),
            ("role_id", "integer", "yes", "FK Role", "must exist"),
            ("hire_date", "date", "yes", "ISO date", "valid date"),
            ("is_active", "boolean", "yes", "true/false", "boolean"),
            ("created_at", "datetime", "yes", "ISO datetime", "valid timestamp"),
        ],
        "Role": [
            ("id", "integer", "yes", "PK", "positive"),
            ("business_id", "string", "yes", "unique ROL-0001", "immutable"),
            ("name", "string", "yes", "unique", "non-empty"),
            ("description", "string", "no", "—", "text"),
        ],
        "Skill": [
            ("id", "integer", "yes", "PK", "positive"),
            ("business_id", "string", "yes", "unique SKL-000001", "immutable"),
            ("name", "string", "yes", "unique", "non-empty"),
            ("category", "string", "yes", "category enum/list", "non-empty"),
            ("description", "string", "no", "—", "text"),
        ],
        "RoleSkillTarget": [
            ("id", "integer", "yes", "PK", "positive"),
            ("role_id", "integer", "yes", "FK Role", "must exist"),
            ("skill_id", "integer", "yes", "FK Skill", "must exist"),
            ("target_level", "integer", "yes", "1–5", "range check"),
            ("effective_from", "date", "yes", "ISO date", "valid date"),
            ("effective_until", "date", "no", "ISO date", "not before effective_from"),
        ],
        "EmployeeSkill": [
            ("id", "integer", "yes", "PK", "positive"),
            ("employee_id", "integer", "yes", "FK Employee", "must exist"),
            ("skill_id", "integer", "yes", "FK Skill", "must exist"),
            ("current_level", "integer", "yes", "0–5", "range check"),
            ("assessed_at", "datetime", "yes", "ISO datetime", "valid timestamp"),
            ("assessor", "string", "yes", "—", "non-empty"),
        ],
        "Course": [
            ("id", "integer", "yes", "PK", "positive"),
            ("business_id", "string", "yes", "unique CRS-000001", "immutable"),
            ("title", "string", "yes", "—", "non-empty"),
            ("provider", "string", "yes", "—", "non-empty"),
            ("cost", "decimal", "yes", "INR", ">=0"),
            ("duration_hours", "decimal", "yes", "hours", ">0"),
            ("capacity", "integer", "no", "seats", ">=0 when present"),
            ("available_from", "date", "yes", "ISO date", "valid date"),
            ("available_until", "date", "yes", "ISO date", "not before available_from"),
            ("is_active", "boolean", "yes", "true/false", "boolean"),
        ],
        "CourseSkill": [
            ("id", "integer", "yes", "PK", "positive"),
            ("course_id", "integer", "yes", "FK Course", "must exist"),
            ("skill_id", "integer", "yes", "FK Skill", "must exist"),
            ("target_level", "integer", "yes", "1–5", "range check"),
        ],
        "Prerequisite": [
            ("id", "integer", "yes", "PK", "positive"),
            ("skill_id", "integer", "yes", "FK Skill", "must exist"),
            (
                "prerequisite_skill_id",
                "integer",
                "yes",
                "FK Skill",
                "must exist and differ from skill_id",
            ),
            ("minimum_level", "integer", "yes", "1–5", "range check"),
        ],
        "Enrollment": [
            ("id", "integer", "yes", "PK", "positive"),
            ("business_id", "string", "yes", "ENR-EMP-...-CRS-...", "unique immutable"),
            ("employee_id", "integer", "yes", "FK Employee", "must exist"),
            ("course_id", "integer", "yes", "FK Course", "must exist"),
            (
                "enrolled_at",
                "datetime",
                "yes",
                "ISO datetime",
                "within course availability",
            ),
            (
                "status",
                "enum",
                "yes",
                "ENROLLED/IN_PROGRESS/COMPLETED/CANCELLED",
                "valid lifecycle",
            ),
        ],
        "Completion": [
            ("id", "integer", "yes", "PK", "positive"),
            ("business_id", "string", "yes", "CMP-2026-000001", "unique immutable"),
            (
                "enrollment_id",
                "integer",
                "yes",
                "unique FK Enrollment",
                "one completion per enrollment",
            ),
            (
                "completed_at",
                "datetime",
                "yes",
                "ISO datetime",
                "not before enrollment",
            ),
            ("score", "decimal", "no", "0–100", "range check"),
            (
                "outcome",
                "enum",
                "yes",
                "ATTENDED/PASSED/FAILED",
                "outcome distinct from attendance",
            ),
            (
                "certificate_url",
                "string",
                "no",
                "URL",
                "optional certificate reference",
            ),
        ],
        "Budget": [
            ("id", "integer", "yes", "PK", "positive"),
            ("business_id", "string", "yes", "BUD-Department-2026", "unique immutable"),
            ("department", "string", "yes", "department", "unique with fiscal_year"),
            ("fiscal_year", "integer", "yes", "year", "integer"),
            ("allocated_amount", "decimal", "yes", "INR", ">=0"),
            ("spent_amount", "decimal", "yes", "INR", "0 <= spent <= allocated"),
        ],
    }
    for ent, fields in specs.items():
        for f in fields:
            dictionary += f"| {ent} | {f[0]} | {f[1]} | {f[2]} | {f[3]} | {f[4]} |\n"
    (out / "data_dictionary.md").write_text(dictionary, encoding="utf-8")
    manifest = {
        "project": "SkillPath Employee Skill Gap and Learning Path System",
        "seed": seed,
        "scale": scale,
        "counts": {k: len(v) for k, v in tables.items()},
        "generator": "data_tools/generate_dataset.py",
        "provenance": "Entirely synthetic; no external personal data or external datasets used.",
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    source_manifest = {
        "sources": [
            {
                "type": "synthetic",
                "name": "SkillPath deterministic synthetic generator",
                "url": None,
                "version": "1.0.0",
                "retrieval_date": None,
                "license": "Original synthetic records; no third-party dataset used",
                "attribution": "None required",
                "transformations": "Generated from fixed-seed domain rules; identifiers are synthetic",
                "fields_discarded": [],
            }
        ],
        "seed": seed,
        "generator": "data_tools/generate_dataset.py",
    }
    (out / "source_manifest.json").write_text(
        json.dumps(source_manifest, indent=2) + "\n", encoding="utf-8"
    )
    summary = {
        "status": "GENERATED",
        "seed": seed,
        "scale": scale,
        "expected": cfg,
        "actual": {k: len(v) for k, v in tables.items()},
        "ground_truth_cases": len(ground_truth),
        "note": "Run validate_dataset.py for integrity checks. Ground truth is separate from baseline input files.",
    }
    (out / "validation_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--scale", choices=["starter", "full"], default="starter")
    p.add_argument("--seed", type=int, default=20261022)
    p.add_argument("--out", default="generated")
    a = p.parse_args()
    generate(a.scale, a.seed, a.out)
