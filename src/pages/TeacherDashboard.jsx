import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api.js";
import Markdown from "../components/Markdown.jsx";

const PASSWORD_KEY = "qa.teacherPassword";

function getSaved() {
  try {
    return sessionStorage.getItem(PASSWORD_KEY) || "";
  } catch {
    return "";
  }
}

function save(pw) {
  try {
    if (pw) sessionStorage.setItem(PASSWORD_KEY, pw);
    else sessionStorage.removeItem(PASSWORD_KEY);
  } catch {
    /* 忽略 */
  }
}

export default function TeacherDashboard({ config }) {
  const [password, setPassword] = useState(getSaved);

  const logout = useCallback(() => {
    save("");
    setPassword("");
  }, []);

  return (
    <div className="page teacher-page">
      <header className="topbar">
        <div>
          <div className="topbar-title">老師後台</div>
          <div className="topbar-sub">{config.courseName}</div>
        </div>
        <div className="topbar-actions">
          <a className="link-button" href="#/">
            學生頁
          </a>
          {password && (
            <button className="link-button" onClick={logout}>
              登出
            </button>
          )}
        </div>
      </header>
      {password ? (
        <Dashboard password={password} onUnauthorized={logout} />
      ) : (
        <Login
          onLogin={(pw) => {
            save(pw);
            setPassword(pw);
          }}
        />
      )}
    </div>
  );
}

function Login({ onLogin }) {
  const [pw, setPw] = useState("");
  const [error, setError] = useState("");
  const submit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await api.teacherLogin(pw);
      onLogin(pw);
    } catch (err) {
      setError(err.message);
    }
  };
  return (
    <form className="card join-form" onSubmit={submit}>
      <h2>老師登入</h2>
      <label>
        密碼
        <input type="password" value={pw} onChange={(e) => setPw(e.target.value)} autoFocus />
      </label>
      {error && <div className="error">{error}</div>}
      <button className="primary" type="submit">
        登入
      </button>
    </form>
  );
}

function Dashboard({ password, onUnauthorized }) {
  const [stats, setStats] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [student, setStudent] = useState("");
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [s, q] = await Promise.all([
        api.teacherStats(password),
        api.teacherQuestions(password, { student }),
      ]);
      setStats(s);
      setQuestions(q.questions);
    } catch (e) {
      if (e.message === "密碼錯誤") onUnauthorized();
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [password, student, onUnauthorized]);

  useEffect(() => {
    load();
  }, [load]);

  const filtered = useMemo(() => {
    const k = search.trim().toLowerCase();
    if (!k) return questions;
    return questions.filter((q) =>
      [q.student_name, q.question, q.answer].some((v) => (v || "").toLowerCase().includes(k))
    );
  }, [questions, search]);

  return (
    <main className="dashboard">
      {stats?.ephemeral && (
        <div className="warning">
          ⚠️ 目前在 Vercel 上使用 SQLite，資料會不定期消失。請在 Vercel 加一個 Postgres（Neon）並設定 DATABASE_URL。
        </div>
      )}
      {error && <div className="error">{error}</div>}

      {stats && (
        <section className="stats">
          <Stat label="總提問數" value={stats.total} />
          <Stat label="今日提問" value={stats.today} />
          <Stat label="提問學生數" value={stats.students} />
        </section>
      )}

      {stats?.topStudents?.length > 0 && (
        <section className="card">
          <h3>提問最多的學生</h3>
          <div className="suggestions">
            {stats.topStudents.map((s) => (
              <button key={s.student_name} className="chip" onClick={() => setStudent(s.student_name)}>
                {s.student_name}（{s.n}）
              </button>
            ))}
          </div>
        </section>
      )}

      <section className="toolbar">
        <input placeholder="搜尋問題、回答、學生…" value={search} onChange={(e) => setSearch(e.target.value)} />
        {student && (
          <button className="chip" onClick={() => setStudent("")}>
            只看：{student} ✕
          </button>
        )}
        <button onClick={load} disabled={loading}>
          {loading ? "載入中…" : "重新整理"}
        </button>
        <button onClick={() => api.teacherExportCsv(password).catch((e) => setError(e.message))}>
          匯出 CSV
        </button>
      </section>

      <section className="question-list">
        {filtered.length === 0 && <div className="muted">目前沒有紀錄</div>}
        {filtered.map((q) => (
          <details key={q.id} className="card question-item">
            <summary>
              <span className="muted">{new Date(q.created_at).toLocaleString()}</span>
              <button
                className="link-button"
                onClick={(e) => {
                  e.preventDefault();
                  setStudent(q.student_name);
                }}
              >
                {q.student_name}
              </button>
              {q.error && <span className="badge">失敗</span>}
              <div className="question-text">{q.question}</div>
            </summary>
            {q.answer ? <Markdown>{q.answer}</Markdown> : <div className="error">{q.error}</div>}
          </details>
        ))}
      </section>
    </main>
  );
}

function Stat({ label, value }) {
  return (
    <div className="card stat">
      <div className="stat-value">{value}</div>
      <div className="muted">{label}</div>
    </div>
  );
}
