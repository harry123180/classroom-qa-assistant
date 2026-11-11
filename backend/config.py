"""讀取課程設定（assistant.config.json）與課程資料（knowledge/ 資料夾）。"""
import json
import os
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "assistant.config.json"
KNOWLEDGE_DIR = ROOT / "knowledge"
KNOWLEDGE_EXTS = {".md", ".txt"}

DEFAULTS = {
    "courseName": "我的課程",
    "assistantName": "AI 助教",
    "welcomeMessage": "有任何課程問題都可以問我。",
    "systemPrompt": "你是課堂助教，請用繁體中文簡潔回答。",
    "suggestedQuestions": [],
    "requireStudentName": True,
    "dailyQuestionLimit": 30,
    "maxQuestionLength": 2000,
    "maxHistoryMessages": 6,
    "knowledgeMaxChars": 30000,
    "temperature": None,
    "timezone": "Asia/Taipei",
}


@lru_cache(maxsize=1)
def load_config() -> dict:
    cfg = dict(DEFAULTS)
    if CONFIG_PATH.exists():
        cfg.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
    # systemPrompt 可以寫成字串，或寫成多行的陣列
    if isinstance(cfg["systemPrompt"], list):
        cfg["systemPrompt"] = "\n".join(cfg["systemPrompt"])
    return cfg


def public_config() -> dict:
    """給前端看的設定（不含 systemPrompt 與任何機密）。"""
    cfg = load_config()
    return {
        "courseName": cfg["courseName"],
        "assistantName": cfg["assistantName"],
        "welcomeMessage": cfg["welcomeMessage"],
        "suggestedQuestions": cfg["suggestedQuestions"],
        "requireStudentName": cfg["requireStudentName"],
        "requireClassCode": bool(env("CLASS_CODE")),
        "maxQuestionLength": cfg["maxQuestionLength"],
    }


@lru_cache(maxsize=1)
def load_knowledge() -> str:
    """把 knowledge/ 裡的 .md / .txt 串起來。檔名以 _ 開頭的會被略過（拿來寫說明）。"""
    if not KNOWLEDGE_DIR.exists():
        return ""
    parts = []
    for path in sorted(KNOWLEDGE_DIR.rglob("*")):
        if path.suffix.lower() in KNOWLEDGE_EXTS and not path.name.startswith("_"):
            rel = path.relative_to(KNOWLEDGE_DIR).as_posix()
            parts.append(f"### 檔案：{rel}\n{path.read_text(encoding='utf-8').strip()}")
    text = "\n\n".join(parts)
    limit = load_config()["knowledgeMaxChars"]
    if limit and len(text) > limit:
        text = text[:limit] + "\n\n（課程資料過長，以下已截斷）"
    return text


def build_system_prompt() -> str:
    cfg = load_config()
    prompt = cfg["systemPrompt"].replace("{courseName}", cfg["courseName"]).replace(
        "{assistantName}", cfg["assistantName"]
    )
    knowledge = load_knowledge()
    if knowledge:
        prompt += f"\n\n===== 課程資料 =====\n{knowledge}\n===== 課程資料結束 ====="
    return prompt


def env(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()
