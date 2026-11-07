#!/usr/bin/env python3
"""Read-only integrity checks for exported synthetic CSV data."""

import argparse, csv, json
from collections import Counter, defaultdict
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path


def load(folder, name):
    with (Path(folder) / f"{name}.csv").open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def validate(folder):
    p = Path(folder)
    names = [
        "roles",
        "employees",
        "skills",
        "role_skill_targets",
        "employee_skills",
        "courses",
        "course_skills",
        "prerequisites",
        "enrollments",
        "completions",
        "budgets",
    ]
    data = {n: load(p, n) for n in names}
    errors = []
    checks = []

    def check(name, condition, detail=""):
        checks.append({"check": name, "passed": bool(condition), "detail": detail})
        if not condition:
            errors.append(name + (": " + detail if detail else ""))

    for n, rows in data.items():
        ids = [r["id"] for r in rows]
        check(f"{n}: primary key unique", len(ids) == len(set(ids)), f"{len(ids)} rows")
    for n in [
        "employees",
        "skills",
        "courses",
        "enrollments",
        "completions",
        "budgets",
    ]:
        ids = [r.get("business_id", "") for r in data[n]]
        check(
            f"{n}: business ID unique and nonempty",
            all(ids) and len(ids) == len(set(ids)),
        )
    ids = {n: {r["id"] for r in rows} for n, rows in data.items()}
    for table, field, parent in [
        ("employees", "role_id", "roles"),
        ("role_skill_targets", "role_id", "roles"),
        ("role_skill_targets", "skill_id", "skills"),
        ("employee_skills", "employee_id", "employees"),
        ("employee_skills", "skill_id", "skills"),
        ("course_skills", "course_id", "courses"),
        ("course_skills", "skill_id", "skills"),
        ("prerequisites", "skill_id", "skills"),
        ("prerequisites", "prerequisite_skill_id", "skills"),
        ("enrollments", "employee_id", "employees"),
        ("enrollments", "course_id", "courses"),
        ("completions", "enrollment_id", "enrollments"),
    ]:
        check(
            f"{table}.{field} -> {parent}",
            all(r[field] in ids[parent] for r in data[table]),
        )
    pair = Counter((r["employee_id"], r["course_id"]) for r in data["enrollments"])
    check("employee-course pairs unique", all(v == 1 for v in pair.values()))
    comp = Counter(r["enrollment_id"] for r in data["completions"])
    check("one completion per enrollment", all(v == 1 for v in comp.values()))
    enroll = {r["id"]: r for r in data["enrollments"]}
    courses = {r["id"]: r for r in data["courses"]}
    employees = {r["id"]: r for r in data["employees"]}
    check(
        "enrollment statuses valid",
        all(
            r["status"] in {"ENROLLED", "IN_PROGRESS", "COMPLETED", "CANCELLED"}
            for r in data["enrollments"]
        ),
    )
    check(
        "completion outcomes valid",
        all(
            r["outcome"] in {"ATTENDED", "PASSED", "FAILED"}
            for r in data["completions"]
        ),
    )
    check(
        "course cost and duration valid",
        all(
            Decimal(r["cost"]) >= 0 and Decimal(r["duration_hours"]) > 0
            for r in data["courses"]
        ),
    )
    check(
        "proficiency and target levels valid",
        all(0 <= int(r["current_level"]) <= 5 for r in data["employee_skills"])
        and all(
            1 <= int(r["target_level"]) <= 5
            for r in data["role_skill_targets"] + data["course_skills"]
        ),
    )
    check(
        "prerequisite levels valid",
        all(
            1 <= int(r["minimum_level"]) <= 5
            and r["skill_id"] != r["prerequisite_skill_id"]
            for r in data["prerequisites"]
        ),
    )
    check(
        "course availability ordered",
        all(
            date.fromisoformat(r["available_until"])
            >= date.fromisoformat(r["available_from"])
            for r in data["courses"]
        ),
    )
    cap = Counter(
        r["course_id"] for r in data["enrollments"] if r["status"] != "CANCELLED"
    )
    check(
        "course capacity respected",
        all(
            c["capacity"] == ""
            or c["capacity"] == "None"
            or cap[c["id"]] <= int(c["capacity"])
            for c in data["courses"]
        ),
    )
    check(
        "enrollments within course availability",
        all(
            date.fromisoformat(courses[e["course_id"]]["available_from"])
            <= date.fromisoformat(e["enrolled_at"][:10])
            <= date.fromisoformat(courses[e["course_id"]]["available_until"])
            for e in data["enrollments"]
        ),
    )
    completed_ids = {r["enrollment_id"] for r in data["completions"]}
    check(
        "completed status matches completion record",
        all(
            (e["status"] == "COMPLETED") == (e["id"] in completed_ids)
            for e in data["enrollments"]
        ),
    )
    check(
        "completion dates not before enrollment",
        all(
            datetime.fromisoformat(c["completed_at"])
            >= datetime.fromisoformat(enroll[c["enrollment_id"]]["enrolled_at"])
            for c in data["completions"]
        ),
    )
    spending = defaultdict(Decimal)
    for e in data["enrollments"]:
        if e["status"] != "CANCELLED":
            spending[employees[e["employee_id"]]["department"]] += Decimal(
                courses[e["course_id"]]["cost"]
            )
    budgets = {b["department"]: b for b in data["budgets"]}
    check(
        "budget spending reconciles",
        all(
            Decimal(b["spent_amount"]) == spending[d]
            and Decimal(b["spent_amount"]) <= Decimal(b["allocated_amount"])
            for d, b in budgets.items()
        ),
    )
    # prerequisite chain is acyclic by generator construction and each baseline enrollment must satisfy prerequisites
    prereqs = defaultdict(list)
    for x in data["prerequisites"]:
        prereqs[x["skill_id"]].append(x["prerequisite_skill_id"])
    skills_by_course = defaultdict(list)
    for x in data["course_skills"]:
        skills_by_course[x["course_id"]].append(x["skill_id"])
    levels = {
        (r["employee_id"], r["skill_id"]): int(r["current_level"])
        for r in data["employee_skills"]
    }
    violations = []
    for e in data["enrollments"]:
        if e["status"] == "CANCELLED":
            continue
        for sid in skills_by_course[e["course_id"]]:
            for pre in prereqs[sid]:
                if levels.get((e["employee_id"], pre), 0) < 1:
                    violations.append((e["id"], pre))
    check("prerequisite eligibility", not violations, f"{len(violations)} violations")
    check(
        "ground truth separate from core tables",
        (p / "ground_truth.csv").exists() and "ground_truth" not in names,
    )
    check("source manifest present", (p / "source_manifest.json").exists())
    result = {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "checks": checks,
        "counts": {n: len(rows) for n, rows in data.items()},
        "ground_truth_cases": (
            len(load(p, "ground_truth")) if (p / "ground_truth.csv").exists() else 0
        ),
    }
    (p / "validation_summary.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2))
    return not errors


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    args = ap.parse_args()
    raise SystemExit(0 if validate(args.input) else 1)
