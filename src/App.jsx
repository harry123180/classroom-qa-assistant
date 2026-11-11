import { useEffect, useState } from "react";
import { api } from "./api.js";
import StudentChat from "./pages/StudentChat.jsx";
import TeacherDashboard from "./pages/TeacherDashboard.jsx";

// 簡單的 hash 路由：#/ 學生頁、#/teacher 老師後台
function useHashRoute() {
  const [hash, setHash] = useState(window.location.hash);
  useEffect(() => {
    const onChange = () => setHash(window.location.hash);
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return hash.replace(/^#/, "") || "/";
}

export default function App() {
  const route = useHashRoute();
  const [config, setConfig] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .getConfig()
      .then((cfg) => {
        setConfig(cfg);
        document.title = `${cfg.assistantName}｜${cfg.courseName}`;
      })
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="center-message error">無法連線到伺服器：{error}</div>;
  if (!config) return <div className="center-message">載入中…</div>;

  return route.startsWith("/teacher") ? <TeacherDashboard config={config} /> : <StudentChat config={config} />;
}
