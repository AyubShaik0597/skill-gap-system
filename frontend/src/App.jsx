import { useEffect, useState } from "react";
import Login from "./Login.jsx";

const API =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

let authToken = localStorage.getItem("skillpath_access_token") || "";

async function api(path, options = {}) {
  const r = await fetch(API + path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(authToken
        ? { Authorization: `Bearer ${authToken}` }
        : {}),
      ...(options.headers || {}),
    },
  });

  const d = await r
    .json()
    .catch(() => ({ detail: "Invalid server response" }));

  if (!r.ok) {
    throw Error(d.detail || `HTTP ${r.status}`);
  }

  return d;
}

const cash = (n) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(Number(n || 0));

export default function App() {
  const [authenticated, setAuthenticated] = useState(
    Boolean(localStorage.getItem("skillpath_access_token"))
  );

  const [tab, setTab] = useState("Overview");
  const [summary, setSummary] = useState({});
  const [employees, setEmployees] = useState([]);
  const [budgets, setBudgets] = useState([]);
  const [id, setId] = useState("1");
  const [gaps, setGaps] = useState(null);
  const [recs, setRecs] = useState(null);
  const [career, setCareer] = useState([]);
  const [history, setHistory] = useState([]);
  const [search, setSearch] = useState("");
  const [course, setCourse] = useState("");
  const [enrollment, setEnrollment] = useState("");
  const [skill, setSkill] = useState("1");
  const [level, setLevel] = useState("3");
  const [score, setScore] = useState("85");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function refresh() {
    try {
      setError("");

      const [s, e, b] = await Promise.all([
        api("/api/dashboard/summary"),
        api("/api/employees?limit=500"),
        api("/api/budgets"),
      ]);

      setSummary(s);
      setEmployees(e);
      setBudgets(b);
    } catch (e) {
      setError(
        e.message + " — start FastAPI and seed a demo dataset."
      );
    }
  }

  async function loadEmployee(emp = id) {
    if (!emp) return;

    try {
      const [g, r, c, h] = await Promise.all([
        api(`/api/employees/${emp}/gaps`),
        api(
          `/api/employees/${emp}/recommendations?diagnostics=true`
        ),
        api(`/api/employees/${emp}/career-paths`),
        api(`/api/employees/${emp}/assessments`),
      ]);

      setGaps(g);
      setRecs(r);
      setCareer(c);
      setHistory(h);
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => {
    if (authenticated) {
      refresh();
    }
  }, [authenticated]);

  useEffect(() => {
    if (authenticated) {
      loadEmployee(id);
    }
  }, [id, authenticated]);

  function handleLogin(data) {
    if (!data?.access_token) {
      setError("Login response did not contain an access token.");
      return;
    }

    authToken = data.access_token;

    localStorage.setItem(
      "skillpath_access_token",
      data.access_token
    );

    if (data.user) {
      localStorage.setItem(
        "skillpath_user",
        JSON.stringify(data.user)
      );
    }

    setError("");
    setAuthenticated(true);
  }

  function handleLogout() {
    authToken = "";

    localStorage.removeItem("skillpath_access_token");
    localStorage.removeItem("skillpath_user");

    setAuthenticated(false);
    setSummary({});
    setEmployees([]);
    setBudgets([]);
    setGaps(null);
    setRecs(null);
    setCareer([]);
    setHistory([]);
    setError("");
    setNotice("");
    setSearch("");
    setTab("Overview");
  }

  async function action(fn) {
    try {
      setError("");

      const message = await fn();
      setNotice(message);

      await refresh();
      await loadEmployee();
    } catch (e) {
      setError(e.message);
    }
  }

  const emp = employees.find(
    (e) => e.id === Number(id)
  );

  const filtered = employees.filter((e) =>
    `${e.full_name} ${e.business_id} ${e.department}`
      .toLowerCase()
      .includes(search.toLowerCase())
  );

  if (!authenticated) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="layout">
      <aside>
        <div className="logo">
          <span>✦</span>

          <div>
            <b>skillpath</b>
            <small>LEARNING INTELLIGENCE</small>
          </div>
        </div>

        <p className="muted">WORKSPACE</p>

        {[
          "Overview",
          "Employee insights",
          "Learning & enrollment",
          "Budgets",
          "Traceability",
        ].map((t) => (
          <button
            className={tab === t ? "nav active" : "nav"}
            onClick={() => setTab(t)}
            key={t}
          >
            {
              {
                Overview: "▦",
                "Employee insights": "◉",
                "Learning & enrollment": "▣",
                Budgets: "◈",
                Traceability: "⌁",
              }[t]
            }
            　{t}
          </button>
        ))}

        <div className="sidefoot">
          ● API workspace{" "}
          <button onClick={refresh}>↻</button>
        </div>
      </aside>

      <main>
        <header>
          <div>
            <small className="eyebrow">
              PEOPLE DEVELOPMENT / SKILL ANALYTICS
            </small>

            <h1>{tab}</h1>
          </div>

          <div
            style={{
              display: "flex",
              gap: "10px",
              alignItems: "center",
            }}
          >
            <button
              className="outline"
              onClick={refresh}
            >
              ↻ Refresh
            </button>

            <button
              className="outline"
              onClick={handleLogout}
            >
              Sign out
            </button>
          </div>
        </header>

        {error && (
          <div className="alert bad">
            ⚠ {error}

            <button onClick={() => setError("")}>
              ×
            </button>
          </div>
        )}

        {notice && (
          <div className="alert good">
            ✓ {notice}

            <button onClick={() => setNotice("")}>
              ×
            </button>
          </div>
        )}

        {tab === "Overview" && (
          <>
            <section className="hero">
              <div>
                <small>WORKFORCE READINESS</small>

                <h2>
                  Turn skill gaps into
                  <br />
                  <em>measurable growth.</em>
                </h2>

                <p>
                  Connect role expectations, employee proficiency,
                  feasible learning options and budget decisions in
                  one traceable workflow.
                </p>

                <button
                  className="primary"
                  onClick={() =>
                    setTab("Employee insights")
                  }
                >
                  Explore employee insights →
                </button>
              </div>

              <div className="orb">
                <span>↗</span>
                <b>Skill gap</b>
                <small>→ feasible path → outcome</small>
              </div>
            </section>

            <h2 className="sectiontitle">
              Operational snapshot
            </h2>

            <section className="stats">
              {[
                [
                  "Active employees",
                  summary.active_employees,
                  "Workforce in scope",
                ],
                [
                  "Skills catalog",
                  summary.skills,
                  "Competency library",
                ],
                [
                  "Active courses",
                  summary.active_courses,
                  "Learning catalogue",
                ],
                [
                  "Enrollments",
                  summary.enrollments,
                  `${summary.completions || 0} completions recorded`,
                ],
              ].map((x) => (
                <article className="stat" key={x[0]}>
                  <small>{x[0]}</small>
                  <strong>{x[1] ?? "—"}</strong>
                  <span>{x[2]}</span>
                </article>
              ))}
            </section>

            <section className="columns">
              <article className="panel">
                <h3>Employee skill analysis</h3>

                <p>
                  Search and select an employee to inspect gaps.
                </p>

                <input
                  placeholder="Search name, employee ID or department"
                  value={search}
                  onChange={(e) =>
                    setSearch(e.target.value)
                  }
                />

                {filtered.slice(0, 6).map((e) => (
                  <button
                    className="employee"
                    key={e.id}
                    onClick={() => {
                      setId(String(e.id));
                      setTab("Employee insights");
                    }}
                  >
                    <span className="person">
                      {e.full_name
                        .split(" ")
                        .map((x) => x[0])
                        .slice(0, 2)
                        .join("")}
                    </span>

                    <span>
                      <b>{e.full_name}</b>

                      <small>
                        {e.business_id} · {e.department}
                      </small>
                    </span>

                    <i>{e.role}</i> ↗
                  </button>
                ))}
              </article>

              <article className="panel">
                <h3>Department budget health</h3>

                <p>
                  Allocated versus committed learning spend.
                </p>

                {budgets.slice(0, 8).map((b) => (
                  <div
                    className="budget"
                    key={b.business_id}
                  >
                    <div>
                      <b>{b.department}</b>

                      <span>
                        {cash(b.spent)} / {cash(b.allocated)}
                      </span>
                    </div>

                    <progress
                      value={b.spent}
                      max={b.allocated || 1}
                    />

                    <small>
                      {cash(b.remaining)} remaining
                    </small>
                  </div>
                ))}

                {!budgets.length && (
                  <p>
                    No budgets loaded. Seed the database first.
                  </p>
                )}
              </article>
            </section>
          </>
        )}

        {tab === "Employee insights" && (
          <>
            <section className="panel profile">
              <div>
                <small className="eyebrow">
                  EMPLOYEE PROFILE
                </small>

                <h2>
                  {emp?.full_name || "Choose employee"}
                </h2>

                <p>
                  {emp?.business_id} · {emp?.department} ·{" "}
                  {emp?.role}
                </p>
              </div>

              <select
                value={id}
                onChange={(e) => setId(e.target.value)}
              >
                {employees.map((e) => (
                  <option key={e.id} value={e.id}>
                    {e.business_id} — {e.full_name}
                  </option>
                ))}
              </select>
            </section>

            <section className="columns">
              <article className="panel">
                <h3>Priority skill gaps</h3>

                <p>
                  Target proficiency minus current assessment.
                  Missing assessment defaults to 0.
                </p>

                {gaps?.gaps?.map((g) => (
                  <div className="gap" key={g.skill_id}>
                    <div>
                      <b>{g.skill}</b>

                      <small>
                        Current {g.current_level} / Target{" "}
                        {g.target_level}
                      </small>
                    </div>

                    <progress
                      value={g.current_level}
                      max={g.target_level}
                    />

                    <strong>+{g.gap}</strong>
                  </div>
                ))}

                {gaps?.gap_count === 0 && (
                  <p>
                    No open skill gaps for this role.
                  </p>
                )}
              </article>

              <article className="panel">
                <h3>Feasible course matches</h3>

                <p>
                  Filtered by gaps, prerequisites, availability,
                  capacity and budget.
                </p>

                {recs?.recommendations?.map((r) => (
                  <div
                    className="course"
                    key={r.course_id}
                  >
                    <div>
                      <b>{r.title}</b>

                      <small>
                        {r.matched_skills.join(", ")} ·{" "}
                        {r.duration_hours} hours
                      </small>

                      <small>{r.provider}</small>
                    </div>

                    <strong>{cash(r.cost)}</strong>

                    <button
                      className="outline"
                      onClick={() => {
                        setCourse(String(r.course_id));
                        setTab("Learning & enrollment");
                      }}
                    >
                      Select
                    </button>
                  </div>
                ))}

                {recs?.recommendations?.length === 0 && (
                  <p>
                    No feasible recommendations. Review
                    diagnostics in Learning & enrollment.
                  </p>
                )}
              </article>
            </section>

            <article className="panel">
              <h3>Career pathways</h3>

              <p>
                Alternative roles ranked by remaining skill
                development effort.
              </p>

              <div className="pathcards">
                {career.map((c) => (
                  <div key={c.role_id}>
                    <b>{c.role}</b>

                    <strong>{c.skills_to_develop}</strong>

                    <small>
                      proficiency levels to develop
                    </small>

                    <button
                      className="outline"
                      onClick={() =>
                        action(async () => {
                          const r = await api(
                            `/api/employees/${Number(id)}/learning-paths?target_role_id=${c.role_id}`,
                            { method: "POST" }
                          );

                          return `Learning path ${r.business_id} proposed: ${r.courses.length} courses, estimated cost ${cash(r.estimated_cost)}.`;
                        })
                      }
                    >
                      Build learning path
                    </button>
                  </div>
                ))}
              </div>
            </article>
          </>
        )}

        {tab === "Learning & enrollment" && (
          <>
            <section className="columns">
              <article className="panel">
                <h3>Enroll employee</h3>

                <p>
                  API checks prerequisites, capacity, availability,
                  duplicate enrollment and budget.
                </p>

                <label>
                  Employee

                  <select
                    value={id}
                    onChange={(e) => setId(e.target.value)}
                  >
                    {employees.map((e) => (
                      <option value={e.id} key={e.id}>
                        {e.business_id} — {e.full_name}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  Course database ID

                  <input
                    type="number"
                    value={course}
                    onChange={(e) =>
                      setCourse(e.target.value)
                    }
                    placeholder="Numeric course ID"
                  />
                </label>

                <button
                  className="primary"
                  onClick={() =>
                    action(async () => {
                      const r = await api("/api/enrollments", {
                        method: "POST",
                        body: JSON.stringify({
                          employee_id: Number(id),
                          course_id: Number(course),
                          actor: "frontend-user",
                        }),
                      });

                      return `Enrolled ${r.business_id}; remaining budget ${cash(r.remaining_budget)}.`;
                    })
                  }
                  disabled={!course}
                >
                  Validate and enroll →
                </button>
              </article>

              <article className="panel">
                <h3>Record completion</h3>

                <p>
                  Course completion is not the same as proficiency
                  improvement.
                </p>

                <label>
                  Enrollment database ID

                  <input
                    type="number"
                    value={enrollment}
                    onChange={(e) =>
                      setEnrollment(e.target.value)
                    }
                    placeholder="Numeric enrollment ID"
                  />
                </label>

                <label>
                  Score (0–100)

                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={score}
                    onChange={(e) =>
                      setScore(e.target.value)
                    }
                  />
                </label>

                <button
                  className="primary"
                  onClick={() =>
                    action(async () => {
                      const r = await api(
                        `/api/enrollments/${Number(enrollment)}/complete`,
                        {
                          method: "POST",
                          body: JSON.stringify({
                            score: Number(score),
                            outcome:
                              Number(score) >= 70
                                ? "PASSED"
                                : "FAILED",
                            actor: "frontend-user",
                          }),
                        }
                      );

                      return `Completion ${r.business_id} recorded. Record reassessment separately.`;
                    })
                  }
                  disabled={!enrollment}
                >
                  Record course outcome ✓
                </button>
              </article>
            </section>

            <article className="panel">
              <h3>Rejected course diagnostics</h3>

              <p>
                Transparent reasons for infeasible recommendations.
              </p>

              {recs?.rejected_courses
                ?.slice(0, 30)
                .map((c) => (
                  <div
                    className="diagnostic"
                    key={c.course_id}
                  >
                    <b>{c.title}</b>
                    <span>{c.reasons.join(" · ")}</span>
                  </div>
                ))}

              {!recs?.rejected_courses?.length && (
                <p>
                  No rejected candidates returned for this employee.
                </p>
              )}
            </article>
          </>
        )}

        {tab === "Budgets" && (
          <article className="panel">
            <h3>Department learning budgets</h3>

            <p>
              Cancellation refunds are explicitly logged;
              reactivation charges again.
            </p>

            <div className="tablewrap">
              <table>
                <thead>
                  <tr>
                    <th>Department</th>
                    <th>Year</th>
                    <th>Allocated</th>
                    <th>Spent</th>
                    <th>Remaining</th>
                  </tr>
                </thead>

                <tbody>
                  {budgets.map((b) => (
                    <tr key={b.business_id}>
                      <td>{b.department}</td>
                      <td>{b.fiscal_year}</td>
                      <td>{cash(b.allocated)}</td>
                      <td>{cash(b.spent)}</td>
                      <td>{cash(b.remaining)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </article>
        )}

        {tab === "Traceability" && (
          <>
            <article className="panel">
              <h3>Record skill reassessment</h3>

              <p>
                Each assessment is a history event and updates the
                current proficiency snapshot.
              </p>

              <div className="formrow">
                <label>
                  Skill database ID

                  <input
                    type="number"
                    value={skill}
                    onChange={(e) =>
                      setSkill(e.target.value)
                    }
                  />
                </label>

                <label>
                  New level

                  <select
                    value={level}
                    onChange={(e) =>
                      setLevel(e.target.value)
                    }
                  >
                    {[0, 1, 2, 3, 4, 5].map((x) => (
                      <option key={x}>{x}</option>
                    ))}
                  </select>
                </label>

                <button
                  className="primary"
                  onClick={() =>
                    action(async () => {
                      const r = await api(
                        `/api/employees/${Number(id)}/skills/${Number(skill)}/assessments`,
                        {
                          method: "POST",
                          body: JSON.stringify({
                            level: Number(level),
                            assessor: "frontend-user",
                            source: "MANUAL",
                            notes: "UI reassessment",
                          }),
                        }
                      );

                      await loadEmployee();

                      return `Assessment recorded: ${r.previous_level ?? "unassessed"} → ${r.assessed_level}.`;
                    })
                  }
                >
                  Save assessment
                </button>
              </div>
            </article>

            <article className="panel">
              <h3>
                Assessment history · {emp?.full_name || "Employee"}
              </h3>

              {history.map((h) => (
                <div
                  className="history"
                  key={h.business_id}
                >
                  <span>
                    <b>{h.skill}</b>

                    <small>
                      {h.business_id} ·{" "}
                      {new Date(h.assessed_at).toLocaleString()}
                    </small>
                  </span>

                  <strong>
                    {h.previous_level ?? "—"} → {h.assessed_level}
                  </strong>

                  <small>
                    {h.assessor} / {h.source}
                  </small>
                </div>
              ))}

              {!history.length && (
                <p>No assessment history yet.</p>
              )}

              <button
                className="outline"
                onClick={() =>
                  window.open(API + "/docs", "_blank")
                }
              >
                Open API documentation ↗
              </button>
            </article>

            <article className="panel">
              <h3>Evaluation metrics</h3>

              <p>
                Live API endpoint:{" "}
                <code>/api/evaluation/metrics</code>
              </p>

              <button
                className="outline"
                onClick={async () => {
                  try {
                    const m = await api(
                      "/api/evaluation/metrics"
                    );

                    setNotice(JSON.stringify(m));
                  } catch (e) {
                    setError(e.message);
                  }
                }}
              >
                Load evaluation metrics
              </button>
            </article>
          </>
        )}

        <footer>
          SKILLPATH · WORKFORCE LEARNING INTELLIGENCE{" "}
          <span>
            Deterministic rules · Traceable decisions · Measurable
            outcomes
          </span>
        </footer>
      </main>
    </div>
  );
}