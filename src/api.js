// 前端呼叫後端的所有函式都集中在這裡

async function request(path, { method = "GET", body, headers = {} } = {}) {
  const res = await fetch(path, {
    method,
    headers: { ...(body ? { "Content-Type": "application/json" } : {}), ...headers },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `伺服器錯誤（${res.status}）`);
  return data;
}

const teacherHeaders = (password) => ({ "X-Teacher-Password": password });

export const api = {
  getConfig: () => request("/api/config"),
  ask: (payload) => request("/api/ask", { method: "POST", body: payload }),

  teacherLogin: (password) =>
    request("/api/teacher/login", { method: "POST", headers: teacherHeaders(password) }),
  teacherStats: (password) => request("/api/teacher/stats", { headers: teacherHeaders(password) }),
  teacherQuestions: (password, { limit = 200, student = "" } = {}) =>
    request(`/api/teacher/questions?limit=${limit}&student=${encodeURIComponent(student)}`, {
      headers: teacherHeaders(password),
    }),
  async teacherExportCsv(password) {
    const res = await fetch("/api/teacher/export.csv", { headers: teacherHeaders(password) });
    if (!res.ok) throw new Error("匯出失敗");
    const url = URL.createObjectURL(await res.blob());
    const a = Object.assign(document.createElement("a"), { href: url, download: "questions.csv" });
    a.click();
    URL.revokeObjectURL(url);
  },
};

// localStorage 在無痕模式等情況可能無法使用，所以都包 try/catch
export const storage = {
  get(key, fallback = null) {
    try {
      const v = localStorage.getItem(key);
      return v === null ? fallback : JSON.parse(v);
    } catch {
      return fallback;
    }
  },
  set(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {
      /* 忽略 */
    }
  },
  remove(key) {
    try {
      localStorage.removeItem(key);
    } catch {
      /* 忽略 */
    }
  },
};
