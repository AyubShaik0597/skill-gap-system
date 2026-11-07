# Architecture and relationship notes

## Layers
- **React/Vite**: overview, employee profile, gaps, feasible recommendations, budget view, completion and reassessment forms.
- **FastAPI**: REST endpoints, business-rule checks, HTTP exceptions, traceable API actions.
- **SQLAlchemy/MySQL**: normalized entity storage, FK/unique/check constraints, transaction boundaries.
- **data_tools**: deterministic standard-library generator and file-based validation/reproducibility tools. These scripts never connect to the live database.

## Cardinality and lifecycle
| Relationship | Cardinality | Optionality / lifecycle |
|---|---|---|
| Role → Employee | 1:N | Employee requires one role in this MVP. |
| Role ↔ Skill | N:M via RoleSkillTarget | Effective-dated target; target level 1–5. |
| Employee ↔ Skill | N:M via EmployeeSkill | Current snapshot, one row per employee/skill pair. |
| Employee → SkillAssessment | 1:N | Append-only assessment events; previous level can be null for first assessment. |
| Course ↔ Skill | N:M via CourseSkill | Course may map to multiple skills; target level 1–5. |
| Skill → prerequisite Skill | N:M directed graph | No self edge; generator creates acyclic baseline edges. |
| Employee → Enrollment | 1:N | ENROLLED → IN_PROGRESS → COMPLETED, or CANCELLED. Reactivation is explicit and audited. |
| Course → Enrollment | 1:N | Capacity applies to non-cancelled enrollments. |
| Enrollment → Completion | 1:0..1 | One completion per enrollment; duplicate attempts return conflict. |
| Department/year → Budget | 1:1 | Unique department + fiscal year; allocated/spent reconciled. |
| Employee → LearningPath | 1:N | Proposed/approved/in-progress/completed/cancelled lifecycle. |
| LearningPath ↔ Course | N:M via LearningPathCourse | Sequence number records planned order. |
| Any business entity → AuditEvent | 1:N conceptual | Polymorphic entity business ID, append-only, no generic FK. |

## Deliberate anomaly cases
The baseline remains valid. `ground_truth.csv/json` and `scenario_fixtures.csv/json` describe expected failure decisions without injecting invalid rows into normal input tables. These fixtures cover prerequisite violation, budget exceeded, duplicate completion, missing reassessment, and course unavailable during planning. A submission evaluator can use them to verify API rejection/decision rules.
