# SkillPath — Employee Skill Gap & Learning Path System

A submission-ready full-stack MVP using **React + Vite**, **FastAPI**, **SQLAlchemy**, and **MySQL**. It covers role-based skill gaps, prerequisite-aware course recommendations, budget/capacity/availability validation, enrollment, completion, explicit reassessment, career-pathway comparison, audit history, metrics, and deterministic synthetic data generation.

## Run locally (Windows PowerShell)
### Backend
1. Install Python 3.11+ and MySQL 8+.
2. In MySQL, run `CREATE DATABASE skillpath_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`
3. `cd backend`; `py -m venv .venv`; `\.venv\Scripts\Activate.ps1`; `pip install -r requirements.txt`.
4. `Copy-Item .env.example .env`; edit local DB credentials. Never commit `.env`.
5. `uvicorn app.main:app --reload`; open `http://127.0.0.1:8000/docs`.
6. In a second backend terminal run `python -m app.seed_demo` once for demo data. It skips seeding if employees already exist and never drops tables.

For isolated testing without MySQL, set `DATABASE_URL=sqlite:///./skillpath_test.db` in `.env` before starting the API.

### Frontend
1. `cd frontend`; `npm install`; `Copy-Item .env.example .env`; `npm run dev`.
2. Open the Vite URL, normally `http://localhost:5173`.

### Synthetic data generator (does not connect to application database)
```powershell
cd data_tools
py generate_dataset.py --scale starter --seed 20261022 --out ../generated
py validate_dataset.py --input ../generated
py reproduce_check.py --scale starter --seed 20261022 --out ../reproducibility
# Required full scale
py generate_dataset.py --scale full --seed 20261022 --out ../generated_full
py validate_dataset.py --input ../generated_full
py reproduce_check.py --scale full --seed 20261022 --out ../reproducibility_full
```
Generator output contains CSV/JSON tables, separate `ground_truth.csv/json`, scenario fixtures, SQL inserts, data dictionary, manifest, and validation summary. Use `--scale starter` for fast local smoke tests and `--scale full` for the required 5,000 employees, 500 skills, 1,000 courses, and 10,000 enrollments. It writes only to the chosen output directory.

## Business rules and acceptance
- Skill levels are 0–5; role/course targets are 1–5; absent employee assessments count as level 0.
- Gap = `max(0, role target - current level)`.
- A prerequisite is satisfied when current level meets the prerequisite's `minimum_level` (baseline defaults to 1).
- Recommendations exclude inactive/unavailable courses, courses exceeding budget, full courses, existing active enrollments and missing prerequisites. Optional diagnostics show rejection reasons.
- Course attendance/completion does not itself increase proficiency. A separate assessment endpoint records a history event and updates the current proficiency snapshot.
- Cancellation refunds the original course cost to the department budget; reactivation charges the course cost again. Completed enrollments cannot be cancelled. The rule is explicit and audit logged.
- Baseline synthetic data remains valid. Five negative scenarios are represented as separately labelled fixtures/ground truth to avoid silently corrupting normal data. Ground truth must never be used as input features.
- Evaluation endpoint: `/api/evaluation/metrics`; it reports enrollment/completion and budget metrics plus sampled open skill gaps. Completion is not conflated with proficiency improvement.

## API
`GET /health`; `/api/dashboard/summary`; `/api/employees`; `/api/roles`; `/api/skills`; `/api/courses`; `/api/employees/{id}/gaps`; `/api/employees/{id}/recommendations?diagnostics=true`; `/api/employees/{id}/career-paths`; `POST /api/enrollments`; `POST /api/enrollments/{id}/cancel`; `POST /api/enrollments/{id}/complete`; `POST /api/employees/{id}/skills/{skill_id}/assessments`; `GET /api/employees/{id}/assessments`; `/api/budgets`; `/api/audit-events`; `/api/evaluation/metrics`.

## Entity relationships
- Role 1:N Employee; Role M:N Skill via RoleSkillTarget.
- Employee M:N Skill via EmployeeSkill (current snapshot) and SkillAssessment (append-only assessment history).
- Course M:N Skill via CourseSkill; Skill prerequisites are a directed relationship between Skill records.
- Employee 1:N Enrollment; Course 1:N Enrollment; Enrollment 0:1 Completion.
- Department/year 1:1 Budget; Employee 1:N LearningPath; LearningPath M:N Course via LearningPathCourse.
- AuditEvent is append-only polymorphic traceability (entity business ID rather than a hard FK because it spans entity types).

## ID convention
Internal integer PKs are used for efficient FK relationships. Unique immutable business IDs follow `EMP-000001`, `SKL-000001`, `CRS-000001`, `ENR-EMP-000001-CRS-000001`, `CMP-2026-000001`, and `BUD-Engineering-2026`. IDs are never derived from mutable names except the requested budget nomenclature.

## Data privacy and limitations
All sample names/emails are synthetic `example.test` values. No external dataset or private data is used. This is a demo MVP, not a production HR system: add authentication/authorization, database migrations, rate limiting, structured logging, and privacy review before production deployment.


## Automated API tests

From the `backend` folder, install the requirements and run:

```powershell
py -m pytest -q test_api_workflows.py
```

These tests use an isolated SQLite database and do not require a running MySQL server. They cover health/dashboard responses, skill-gap/recommendation endpoints, duplicate enrollment/completion protection, reassessment history, learning paths/audit access, and not-found handling. Run the full-scale dataset validator separately as described above.

## Original project audit

See `docs/original_project_audit.md` for the review of the ZIP you provided, identified gaps, changes included in this revised package, verification status, and the `.env` security warning.
## Demo Admin Credentials

Use this account to access the SkillPath Admin dashboard.

- **Email:** `yottaflex123@gmail.com`
- **Password:** Provided privately to the evaluator.
- **Role:** Admin
- **Registration:** Public registration is disabled.

### Login Instructions

1. Start the FastAPI backend.
2. Start the React frontend.
3. Open the frontend URL in your browser.
4. Sign in using the demo Admin credentials.

The dashboard includes Overview, Employee Insights, Learning & Enrollment, Budgets, and Traceability.

**Security:** This account is intended for demo evaluation using synthetic data. Never commit passwords, API keys, or database secrets to the public repository.
