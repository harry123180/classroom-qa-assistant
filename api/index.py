"""Vercel 的 Python 進入點。實際程式在 backend/ 裡，這個檔案不用改。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app import app  # noqa: E402,F401
