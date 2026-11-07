# Original ZIP audit and change log

## What I found in `skill-gap-system.zip`

This review was performed against the source files included in the uploaded archive. The archive contains an `.env` file and a full `.venv`/frontend dependency tree. The `.env` contained database connection settings. It is intentionally not copied into the revised package.

### Functional gaps in the original source

1. **Business IDs were missing from the SQLAlchemy core entities.** `app/models.py` used auto-increment integer IDs only for roles, employees, skills, courses, enrollments and completions. This makes stable, human-readable identifiers and traceability harder to guarantee.
2. **Learning paths were not persisted as first-class records.** The original UI included a `LearningPathPage`, but the backend had no `LearningPath` / `LearningPathCourse` models or create/list learning-path endpoints.
3. **Assessment history was not stored separately.** The original `EmployeeSkill` table only kept the latest proficiency snapshot. Updating it overwrote the prior level, so a history of reassessments could not be reconstructed.
4. **The audit log was write-only from the API.** An audit service existed, but the API did not expose a query endpoint for reviewing event history.
5. **The API surface was incomplete.** There were no general list endpoints for employees, roles, skills and courses, no career-path comparison endpoint, and no evaluation/metrics endpoint.
6. **The original tests did not validate the business workflow.** `tests/test_enrollment_rules.py` tested arithmetic with `Decimal`, but did not call the API or exercise prerequisites, course availability, capacity, duplicate enrollment/completion, cancellation/refund, or reassessment.
7. **Data generation was tied to a live application database.** The original scripts seeded tables and exported the live database. The archive did not contain the separated, deterministic synthetic-data generator and standalone validation/reproducibility workflow needed to recreate the required dataset without mutating the application database.
8. **Scenario ground truth was not separated from baseline data.** The archive contained ordinary CSV/JSON exports and a database report, but no independent ground-truth and negative-scenario fixture files.
9. **No SQL seed export or source/provenance manifest was included in the exported dataset.**
10. **Frontend API configuration was hard-coded.** `frontend/src/App.jsx` directly set `API = "http://127.0.0.1:8000"` and called Axios directly, making environment-specific configuration harder.

### Changes in this revised package

- Added stable business IDs alongside internal database primary keys.
- Added `SkillAssessment`, `LearningPath`, and `LearningPathCourse` models.
- Added persistent learning-path create/list endpoints and career-path comparison.
- Added assessment-history endpoints and explicit reassessment updates. Completing a course does **not** automatically change skill proficiency.
- Added cancellation/refund, duplicate protection, completion, audit-event query and evaluation metrics endpoints.
- Added general list endpoints for employees, roles, skills and courses.
- Added prerequisite, availability, budget, capacity and existing-enrollment checks in recommendation/enrollment workflows.
- Added deterministic synthetic dataset generation with seed `20261022`, the required scale, CSV/JSON exports, SQL seed, data dictionary, manifest, source manifest, validation summary, separate ground truth and scenario fixtures.
- Added a dataset validator and reproducibility checker.
- Added an automated API test suite and a test plan.
- Added environment examples and ignored local secrets/dependencies from the deliverable.

## Verification status

The full generated dataset validator was run against the revised package and passed. The reproducibility checker compared 31 output files and reported identical hashes. The automated backend API workflow suite passed: 5 tests. The result reported 5,000 employees, 500 skills, 1,000 courses, 10,000 enrollments, no prerequisite eligibility violations, valid capacity/budget reconciliation, and five separate ground-truth cases.

The React production build could not be verified because `npm install` timed out in this environment. A real MySQL deployment also still needs to be tested on the target machine. Do not treat those as verified until you run the steps in the README. Use your own local `.env` and never commit it.

## Security note

The uploaded original ZIP included a `.env` file. If its database password was real or has been shared anywhere else, rotate it now. The revised ZIP excludes `.env`, `.venv`, `node_modules`, Python caches and test caches.
