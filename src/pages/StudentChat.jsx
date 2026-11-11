import { useEffect, useRef, useState } from "react";
import { api, storage } from "../api.js";
import Markdown from "../components/Markdown.jsx";

const PROFILE_KEY = "qa.profile";

export default function StudentChat({ config }) {
  const [profile, setProfile] = useState(() => storage.get(PROFILE_KEY));
  const needsJoin = !profile && (config.requireStudentName || config.requireClassCode);

  const logout = () => {
    storage.remove(PROFILE_KEY);
    setProfile(null);
  };

  return (
    <div className="page chat-page">
      <header className="topbar">
        <div>
          <div className="topbar-title">{config.assistantName}</div>
          <div className="topbar-sub">{config.courseName}</div>
        </div>
        {profile?.name && (
          <button className="link-button" onClick={logout}>
            {profile.name}・登出
          </button>
        )}
      </header>
      {needsJoin ? (
        <JoinForm
          config={config}
          onJoin={(p) => {
            storage.set(PROFILE_KEY, p);
            setProfile(p);
          }}
        />
      ) : (
        <Chat config={config} profile={profile || {}} />
      )}
    </div>
  );
}

function JoinForm({ config, onJoin }) {
  const [name, setName] = useState("");
  const [classCode, setClassCode] = useState("");

  const submit = (e) => {
    e.preventDefault();
    if (config.requireStudentName && !name.trim()) return;
    onJoin({ name: name.trim(), classCode: classCode.trim() });
  };

  return (
    <form className="card join-form" onSubmit={submit}>
      <h2>開始提問</h2>
      {config.requireStudentName && (
        <label>
          姓名（或學號）
          <input value={name} onChange={(e) => setName(e.target.value)} maxLength={50} autoFocus />
        </label>
      )}
      {config.requireClassCode && (
        <label>
          班級代碼
          <input value={classCode} onChange={(e) => setClassCode(e.target.value)} />
        </label>
      )}
      <button className="primary" type="submit">
        進入
      </button>
    </form>
  );
}

function Chat({ config, profile }) {
  const [messages, setMessages] = useState([]); // [{role: "user"|"assistant", content}]
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = async (text) => {
    const question = text.trim();
    if (!question || loading) return;
    setError("");
    setInput("");
    const history = messages;
    setMessages([...history, { role: "user", content: question }]);
    setLoading(true);
    try {
      const { answer } = await api.ask({ ...profile, question, history });
      setMessages((m) => [...m, { role: "assistant", content: answer }]);
    } catch (e) {
      setError(e.message);
      setMessages(history); // 失敗就把問題放回輸入框，方便重送
      setInput(question);
    } finally {
      setLoading(false);
    }
  };

  const onKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      send(input);
    }
  };

  return (
    <>
      <main className="messages">
        <div className="bubble assistant">
          <Markdown>{config.welcomeMessage}</Markdown>
        </div>
        {messages.length === 0 && config.suggestedQuestions.length > 0 && (
          <div className="suggestions">
            {config.suggestedQuestions.map((q) => (
              <button key={q} className="chip" onClick={() => send(q)}>
                {q}
              </button>
            ))}
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`bubble ${m.role}`}>
            {m.role === "assistant" ? <Markdown>{m.content}</Markdown> : m.content}
          </div>
        ))}
        {loading && <div className="bubble assistant thinking">思考中…</div>}
        <div ref={bottomRef} />
      </main>

      <footer className="composer">
        {error && <div className="error">{error}</div>}
        <div className="composer-row">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="輸入問題，Enter 送出，Shift+Enter 換行"
            maxLength={config.maxQuestionLength}
            rows={2}
          />
          <button className="primary" onClick={() => send(input)} disabled={loading || !input.trim()}>
            送出
          </button>
        </div>
        {messages.length > 0 && (
          <button className="link-button" onClick={() => setMessages([])} disabled={loading}>
            開新對話
          </button>
        )}
      </footer>
    </>
  );
}
