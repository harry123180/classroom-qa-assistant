# 課堂 AI 助教問答系統

學生問問題、AI 助教回答、老師在後台看所有問答紀錄。
可以免費部署到 Vercel，不需要自己管伺服器。

- 學生頁：`https://你的網址/`
- 老師後台：`https://你的網址/#/teacher`

---

## 一、把它變成你的課（只要改兩個地方）

1. **`assistant.config.json`**：課程名稱、助教人設、歡迎詞、建議問題、每天提問上限
2. **`knowledge/` 資料夾**：放入課程大綱、講義重點、作業說明（`.md` 或 `.txt`），助教回答時會參考

想要更多客製化？直接用 Claude Code、Codex 或 Cursor 開啟這個資料夾，用中文告訴它你要什麼，
例如「幫我把配色改成綠色」、「讓學生可以對回答按讚」。`AGENTS.md` 已經寫好給 AI 看的說明。

## 二、部署到 Vercel

### 方法 A：請 AI 幫你部署（不需要 GitHub，推薦）

1. 到 [vercel.com/signup](https://vercel.com/signup) 用 Email 註冊 Vercel 帳號
2. 下載這個專案：在 GitHub 頁面點 **Code → Download ZIP** 解壓縮，或執行
   `git clone https://github.com/harry123180/classroom-qa-assistant.git`
3. 用 Codex / Claude Code 開啟這個資料夾，跟它說：**「幫我部署到 Vercel」**
4. 它會開瀏覽器讓你登入 Vercel，並問你 API Key、老師密碼等設定，照著回答即可
5. 中間它會請你到 Vercel 網站點幾下加資料庫（Neon），大約一分鐘

### 方法 B：透過 GitHub 自動部署

1. 把這個資料夾推到你的 GitHub（私有 repo 也可以）
2. 到 [vercel.com](https://vercel.com) → **Add New → Project** → 選擇這個 repo → **Deploy**
3. 到專案的 **Settings → Environment Variables**，加入：

   | 名稱 | 說明 | 範例 |
   |---|---|---|
   | `LLM_API_KEY` | AI 模型的 API Key（必填） | `sk-...` |
   | `LLM_MODEL` | 模型名稱（必填） | `gpt-4o-mini` |
   | `LLM_BASE_URL` | 用 OpenAI 官方就留空；用 LiteLLM 等相容服務才填 | `https://ai.example.com/v1` |
   | `TEACHER_PASSWORD` | 老師後台密碼（必填） | 自己設一個 |
   | `CLASS_CODE` | 班級代碼，設定後學生要輸入才能提問（選填） | `py2026` |

4. **加資料庫（重要，不然紀錄會消失）**：專案頁 → **Storage** → **Create Database** → 選 **Neon（Postgres）** → 連到這個專案。
   Vercel 會自動設好 `DATABASE_URL`，不用改程式。
5. 到 **Deployments** → 最新一筆 → **Redeploy**，讓環境變數生效
6. 打開 `https://你的專案.vercel.app/api/health` 檢查：
   - `llmConfigured: true` → AI 設定正確
   - `database: "postgres"` → 資料庫設定正確

之後每次 `git push`，Vercel 都會自動重新部署。

### 想用自己的網域？
Vercel 專案 → **Settings → Domains** 加入網域（例如 `qa.yourschool.edu.tw`），
再到你的 DNS 加一筆 CNAME 指向 `cname.vercel-dns.com`。

## 三、在自己電腦上測試（選擇性）

需要先安裝 [Node.js](https://nodejs.org)（20 以上）與 [Python](https://www.python.org)（3.10 以上）。

```bash
pip install -r requirements.txt
npm install
cp .env.example .env    # 用記事本打開 .env 填入金鑰
```

開兩個終端機：

```bash
npm run dev:api   # 後端
npm run dev       # 前端 → 打開 http://localhost:5173
```

本機會用 SQLite（存在 `data/qa.db`），不需要另外裝資料庫。

## 常見問題

**Q：一定要用 OpenAI 嗎？**
不用。任何「OpenAI 相容」的 API 都可以（LiteLLM、Ollama、vLLM、Groq、OpenRouter…），設定 `LLM_BASE_URL` 即可。

**Q：學生會看到我的 API Key 嗎？**
不會。金鑰只存在 Vercel 後端的環境變數，前端拿不到。

**Q：要花多少錢？**
Vercel 與 Neon 免費方案就夠一般班級使用。AI 費用依模型與提問量而定，小型模型通常一個學期一班只要幾美元；
可用 `dailyQuestionLimit` 限制每人每天的提問數。

**Q：學生的身分怎麼驗證？**
目前只要求輸入姓名（加上選填的班級代碼），沒有帳號密碼，適合課堂使用。需要更嚴格的驗證可以請 AI 幫你加。

## 專案結構

```
assistant.config.json   課程設定 ← 最常改
knowledge/              課程資料 ← 最常改
src/                    前端（React）
backend/                後端（Flask）
api/index.py            Vercel 進入點（不用改）
vercel.json             Vercel 設定
AGENTS.md               給 AI coding agent 的說明
```
