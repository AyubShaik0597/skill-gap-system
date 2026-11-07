# Manual acceptance test plan

1. Start backend and frontend; `/health` returns `{"status":"healthy"}` and dashboard loads.
2. Run `python -m app.seed_demo` once in `backend`; it creates a demo employee and catalog only if employees table is empty.
3. Open Employee insights; select Alex Morgan (database employee ID 1); verify gaps are role targets minus assessed levels, missing assessments default to zero.
4. Verify recommendations include relevant courses and diagnostics explain why candidates were excluded (prerequisite, availability, capacity, budget, duplicate enrollment). Use Build learning path on an alternative role and verify a persisted ordered path.
5. Enroll in an eligible recommendation; verify unique ENR business ID and remaining budget decreases by cost.
6. Try enrolling in the same active course again; expect HTTP 409.
7. Try a course with missing prerequisite; expect HTTP 400 and explanatory detail.
8. Cancel a non-completed enrollment; verify budget refund and audit event. Reactivate it; verify budget charged again.
9. Record completion once; verify CMP ID and enrollment status COMPLETED. Attempt second completion; expect HTTP 409.
10. Record a separate skill assessment; verify history retains the event and current snapshot changes. Completion alone must not change proficiency.
11. Check `/api/evaluation/metrics` and `/api/audit-events`.
12. Generate starter data and run validator; run reproducibility checker. Then generate full-scale data in a separate output folder and validate it.
13. Confirm ground-truth files are separate from core table exports and never used by recommendation feature inputs.
