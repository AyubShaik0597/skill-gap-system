import { useState } from "react";

const API =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export default function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await fetch(`${API}/api/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: email.trim(),
          password,
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          data.detail || "Login failed. Check your credentials."
        );
      }

      if (!data.access_token || !data.user) {
        throw new Error("The server returned an invalid login response.");
      }

      onLogin(data);
    } catch (err) {
      setError(
        err.message === "Failed to fetch"
          ? "Cannot connect to the backend. Check that FastAPI is running."
          : err.message
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={styles.page}>
      <form onSubmit={handleSubmit} style={styles.card}>
        <div style={styles.logo}>✦</div>

        <h1 style={styles.title}>Welcome to SkillPath</h1>
        <p style={styles.subtitle}>
          Sign in to your employee learning workspace.
        </p>

        {error && (
          <div role="alert" style={styles.error}>
            {error}
          </div>
        )}

        <label htmlFor="email" style={styles.label}>
          Email address
        </label>
        <input
          id="email"
          type="email"
          autoComplete="username"
          placeholder="you@company.com"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          required
          style={styles.input}
        />

        <label htmlFor="password" style={styles.label}>
          Password
        </label>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          placeholder="Enter your password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
          style={styles.input}
        />

        <button
          type="submit"
          disabled={loading}
          style={styles.button}
        >
          {loading ? "Signing in..." : "Sign in"}
        </button>

        <p style={styles.footer}>
          Authorized accounts only. Contact your administrator for access.
        </p>
      </form>
    </main>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    display: "grid",
    placeItems: "center",
    padding: "24px",
    background: "#0b1525",
    color: "#f4f7fb",
    fontFamily: "Arial, sans-serif",
  },
  card: {
    width: "100%",
    maxWidth: "420px",
    boxSizing: "border-box",
    padding: "36px",
    border: "1px solid #2b3d52",
    borderRadius: "18px",
    background: "#132236",
  },
  logo: {
    width: "48px",
    height: "48px",
    display: "grid",
    placeItems: "center",
    borderRadius: "14px",
    background: "#20b996",
    color: "#071b24",
    fontSize: "28px",
    fontWeight: "bold",
  },
  title: {
    margin: "24px 0 8px",
    fontSize: "28px",
  },
  subtitle: {
    marginBottom: "28px",
    color: "#a8bbd0",
    lineHeight: 1.6,
  },
  label: {
    display: "block",
    margin: "16px 0 8px",
    fontSize: "14px",
    fontWeight: "bold",
  },
  input: {
    width: "100%",
    boxSizing: "border-box",
    padding: "13px",
    border: "1px solid #40536b",
    borderRadius: "9px",
    background: "#0b1525",
    color: "#ffffff",
    fontSize: "15px",
  },
  button: {
    width: "100%",
    marginTop: "24px",
    padding: "14px",
    border: "none",
    borderRadius: "9px",
    background: "#20b996",
    color: "#06231d",
    fontWeight: "bold",
    fontSize: "16px",
    cursor: "pointer",
  },
  error: {
    padding: "12px",
    borderRadius: "8px",
    background: "#48252d",
    color: "#ffb6bd",
    lineHeight: 1.5,
  },
  footer: {
    marginTop: "22px",
    color: "#9db0c5",
    fontSize: "12px",
    textAlign: "center",
    lineHeight: 1.6,
  },
};