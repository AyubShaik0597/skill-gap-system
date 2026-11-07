# Data dictionary overview

The full machine-generated dictionary is emitted as `data_dictionary.md` in every generated dataset folder. The following rules apply across entities:

- Internal `id`: integer primary key, positive, unique within table.
- `business_id`: immutable unique external identifier following entity-specific conventions.
- Foreign keys: required unless explicitly optional; every referenced parent must exist.
- Skill proficiency: integer 0–5. Role targets and course target levels: integer 1–5.
- Currency: decimal INR, never binary float for persisted calculations; cost and allocated amounts must be nonnegative, and `0 <= spent <= allocated`.
- Duration: decimal hours, strictly positive. Capacity: optional integer >=0.
- Course dates: availability end must be on or after availability start. Enrollment must be inside the course availability window.
- Enrollment states: `ENROLLED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`.
- Completion outcomes: `ATTENDED`, `PASSED`, `FAILED`; outcome is not inferred as a proficiency gain.
- Completion score: optional decimal 0–100; one completion record per enrollment.
- Assessment source: `MANUAL` by default; each assessment records previous and new level, timestamp, assessor, and optional notes.
- Budget: unique `(department, fiscal_year)`; `spent_amount` reconciles to non-cancelled enrollment costs under the stated cancellation refund policy.

Entity field-by-field details are in generated `data_dictionary.md`.
