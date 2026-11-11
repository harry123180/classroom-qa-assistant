"""Flask API。所有路由都在 /api 底下。

學生端：
  GET  /api/config            前端要顯示的課程設定
  POST /api/ask               提問 {name, classCode, question, history}
老師端（header 要帶 X-Teacher-Password）：
  POST /api/teacher/login     驗證密碼
  GET  /api/teacher/stats     統計
  GET  /api/teacher/questions 問答紀錄 ?limit=200&student=王小明
  GET  /api/teacher/export.csv
其他：
  GET  /api/health            檢查設定是否正確
"""
import csv
import hmac
import io
import logging
from datetime import datetime
from functools import wraps
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request

load_dotenv()  # 本機開發讀 .env；Vercel 上用後台的環境變數

from . import db, llm  # noqa: E402
from .config import build_system_prompt, env, load_config, public_config  # noqa: E402

app = Flask(__name__)
log = logging.getLogger(__name__)


def error(message: str, status: int = 400):
    return jsonify({"error": message}), status


def start_of_today_iso() -> str:
    tz = ZoneInfo(load_config()["timezone"])
    now = datetime.now(tz)
    return db.to_iso(now.replace(hour=0, minute=0, second=0, microsecond=0))


# ---------- 公開 ----------

@app.get("/api/health")
def health():
    return jsonify(
        {
            "ok": True,
            "llmConfigured": llm.is_configured(),
            "model": llm.model_name(),
            "teacherEnabled": bool(env("TEACHER_PASSWORD")),
            **db.backend_info(),
        }
    )


@app.get("/api/config")
def get_config():
    return jsonify(public_config())


@app.post("/api/ask")
def ask():
    cfg = load_config()
    data = request.get_json(silent=True) or {}
    name = str(data.get("name") or "").strip()[:50] or "匿名"
    question = str(data.get("question") or "").strip()

    if cfg["requireStudentName"] and name == "匿名":
        return error("請先輸入姓名")
    class_code = env("CLASS_CODE")
    if class_code and not hmac.compare_digest(str(data.get("classCode") or "").strip(), class_code):
        return error("班級代碼錯誤", 403)
    if not question:
        return error("問題不能是空的")
    if len(question) > cfg["maxQuestionLength"]:
        return error(f"問題太長了（上限 {cfg['maxQuestionLength']} 字）")
    if not llm.is_configured():
        return error("系統尚未設定 AI 模型（LLM_API_KEY），請通知老師", 503)

    limit = cfg["dailyQuestionLimit"]
    if limit and db.count_since(name, start_of_today_iso()) >= limit:
        return error(f"今天的提問次數已達上限（{limit} 次），明天再來吧！", 429)

    messages = [{"role": "system", "content": build_system_prompt()}]
    messages += clean_history(data.get("history"), cfg["maxHistoryMessages"])
    messages.append({"role": "user", "content": question})

    try:
        answer = llm.chat(messages)
    except Exception as e:  # noqa: BLE001
        log.exception("LLM call failed")
        db.add_question(name, question, None, f"{type(e).__name__}: {e}"[:500], llm.model_name())
        return error("AI 助教暫時無法回答，請稍後再試", 502)

    db.add_question(name, question, answer, None, llm.model_name())
    return jsonify({"answer": answer})


def clean_history(history, max_messages: int) -> list[dict]:
    """只保留前端傳來的最近幾則對話，並過濾掉不合法的內容（例如假冒 system）。"""
    if not isinstance(history, list) or max_messages <= 0:
        return []
    cleaned = [
        {"role": m["role"], "content": m["content"][:4000]}
        for m in history
        if isinstance(m, dict) and m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str)
    ]
    return cleaned[-max_messages:]


# ---------- 老師 ----------

def teacher_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        password = env("TEACHER_PASSWORD")
        if not password:
            return error("尚未設定 TEACHER_PASSWORD，老師後台已停用", 403)
        given = request.headers.get("X-Teacher-Password", "")
        if not hmac.compare_digest(given, password):
            return error("密碼錯誤", 401)
        return fn(*args, **kwargs)

    return wrapper


@app.post("/api/teacher/login")
@teacher_required
def teacher_login():
    return jsonify({"ok": True})


@app.get("/api/teacher/stats")
@teacher_required
def teacher_stats():
    return jsonify({**db.stats(start_of_today_iso()), **db.backend_info()})


@app.get("/api/teacher/questions")
@teacher_required
def teacher_questions():
    limit = min(max(request.args.get("limit", 200, type=int), 1), 2000)
    student = (request.args.get("student") or "").strip() or None
    return jsonify({"questions": db.list_questions(limit, student)})


@app.get("/api/teacher/export.csv")
@teacher_required
def teacher_export():
    rows = db.list_questions(100000)
    buf = io.StringIO()
    buf.write("﻿")  # 讓 Excel 正確顯示中文
    writer = csv.writer(buf)
    writer.writerow(["id", "時間(UTC)", "學生", "問題", "回答", "錯誤", "模型"])
    for r in rows:
        writer.writerow([r["id"], r["created_at"], r["student_name"], r["question"], r["answer"], r["error"], r["model"]])
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=questions.csv"},
    )
