# AGENTS.md — 給 AI coding agent（Claude Code、Codex、Cursor…）的說明

這是一個「課堂 AI 助教問答系統」範本。使用者通常是**老師**，不一定會寫程式，
會用 vibe coding 的方式請你客製化。請用老師聽得懂的話溝通，改動盡量小而清楚。

## 技術架構

- 前端：React 19 + Vite（純 JavaScript，沒有 TypeScript），在 `src/`
- 後端：Python Flask，在 `backend/`；`api/index.py` 是 Vercel 的進入點，不用改
- 資料庫：沒設 `DATABASE_URL` → SQLite（`data/qa.db`）；有設 → Postgres
- AI 模型：任何 OpenAI 相容 API（`backend/llm.py`），由環境變數設定
- 部署：Vercel（`vercel.json`）。前端是靜態檔，`/api/*` 全部轉給 Flask

## 檔案地圖：想改什麼 → 改哪裡

| 想改的東西 | 檔案 |
|---|---|
| 課程名稱、助教人設、歡迎詞、建議問題、每日提問上限 | `assistant.config.json` |
| 助教要參考的課程資料 | `knowledge/*.md`、`knowledge/*.txt` |
| 學生聊天畫面 | `src/pages/StudentChat.jsx` |
| 老師後台 | `src/pages/TeacherDashboard.jsx` |
| 配色、字體、版面 | `src/styles.css`（顏色都在最上面的 CSS 變數） |
| 前端呼叫 API 的函式 | `src/api.js` |
| API 路由、驗證、提問規則 | `backend/app.py` |
| 資料表、SQL | `backend/db.py` |
| 呼叫 AI 的方式 | `backend/llm.py` |
| 讀設定與課程資料 | `backend/config.py` |

`assistant.config.json` 欄位：
- `courseName` / `assistantName`：顯示名稱，也可以在 `systemPrompt` 裡用 `{courseName}`、`{assistantName}` 帶入
- `systemPrompt`：助教的人設與規則，可寫字串或字串陣列（每個元素一行）
- `welcomeMessage`：學生看到的第一句話（支援 Markdown）
- `suggestedQuestions`：建議問題按鈕
- `requireStudentName`：是否要求輸入姓名
- `dailyQuestionLimit`：每位學生每天最多提問數，`0` = 不限制
- `maxQuestionLength`：單題字數上限
- `maxHistoryMessages`：每次提問附帶幾則先前對話（讓 AI 能接續上下文）
- `knowledgeMaxChars`：課程資料最多放幾個字進提示詞
- `temperature`：`null` = 不送（有些推理模型不接受此參數）
- `timezone`：計算「今天」用的時區

## 環境變數（見 `.env.example`）

`LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL`、`TEACHER_PASSWORD`、`CLASS_CODE`（選填）、`DATABASE_URL`（選填）

## 本機開發

```bash
pip install -r requirements.txt
npm install
cp .env.example .env      # 填入金鑰
npm run dev:api           # 終端機 1：Flask（port 5000）
npm run dev               # 終端機 2：前端（http://localhost:5173）
```

老師後台在 `http://localhost:5173/#/teacher`。

## 部署到 Vercel（老師說「幫我部署 / 上線」時照這個做）

老師通常**沒有 GitHub 帳號**，請用 Vercel CLI 直接從本機部署，不要要求老師建 GitHub repo。

1. 確認老師已有 Vercel 帳號（沒有的話請他到 https://vercel.com/signup 用 Email 註冊）
2. `npx vercel login` → 會開瀏覽器，**請老師自己完成登入**，不要代填
3. `npx vercel --yes` → 第一次部署，會自動建立 Vercel 專案（之後就有 `.vercel/` 資料夾）
4. 設定環境變數（值向老師詢問；**不要把金鑰寫進任何檔案或 commit**）：
   ```bash
   printf '%s' "<值>" | npx vercel env add LLM_API_KEY production
   printf '%s' "<值>" | npx vercel env add LLM_MODEL production
   printf '%s' "<值>" | npx vercel env add TEACHER_PASSWORD production
   # 選填：LLM_BASE_URL（用 OpenAI 官方就不用設）、CLASS_CODE
   ```
5. 資料庫：請老師到 Vercel 網站 → 這個專案 → **Storage** → **Create Database** → **Neon** → 連到此專案。
   完成後 `DATABASE_URL` 會自動設定。**沒做這步，問答紀錄會消失。**
6. `npx vercel --prod` → 正式部署，輸出的網址就是學生要用的網址
7. 打開 `<網址>/api/health` 確認 `llmConfigured: true` 且 `database: "postgres"`
8. 告訴老師：學生網址是 `<網址>/`，老師後台是 `<網址>/#/teacher`

之後修改內容，只要再跑一次 `npx vercel --prod`。
環境變數改了之後也要再跑一次 `npx vercel --prod` 才會生效。

## 必須遵守的規則

1. **金鑰只能在後端**。不要把 `LLM_API_KEY`、`TEACHER_PASSWORD` 放進 `src/` 或任何前端程式碼，也不要用 `VITE_` 開頭的環境變數存機密（會被打包進前端）。
2. **所有後端路由都以 `/api/` 開頭**，否則 Vercel 不會轉給 Flask。
3. **老師專用的 API 一定要加 `@teacher_required`**。
4. **SQL 用 `?` 佔位符、透過 `db.execute()` 執行**，不要用字串拼接。要能同時在 SQLite 和 Postgres 跑：
   - 新增資料表時，在 `SCHEMA_SQLITE` 裡加 `CREATE TABLE IF NOT EXISTS ...`（Postgres 版會自動轉換 `INTEGER PRIMARY KEY AUTOINCREMENT`）
   - 時間用 `db.now_iso()`（UTC ISO 字串），不要用資料庫專屬的時間函式
   - 修改既有資料表的欄位時，`CREATE TABLE IF NOT EXISTS` 不會生效，需要另外寫 `ALTER TABLE`，並提醒老師
5. **Vercel 不能用本機檔案存資料**：除了 `/tmp`（隨時會被清掉）之外都是唯讀。要存東西請用資料庫。
6. 新增 Python 套件要加到 `requirements.txt`；新增前端套件用 `npm install`。
7. 後端新增的檔案資料夾如果要在 Vercel 上讀取，記得加進 `vercel.json` 的 `includeFiles`。
8. Vercel Function 有執行時間上限（`vercel.json` 的 `maxDuration`），不要做長時間的工作。
9. 改完請跑 `npm run build` 確認前端能編譯；後端改動請實際打一次 API 測試。

## 常見客製化範例（老師可能會這樣問）

- 「助教不要直接給答案」→ 改 `systemPrompt`
- 「加入第 5 週的講義」→ 把內容存成 `knowledge/week5.md`
- 「學生要用學號登入」→ 改 `StudentChat.jsx` 的 `JoinForm` 文字；若要驗證學號名單，在後端加名單檢查
- 「老師後台要看每週統計」→ 在 `db.py` 加查詢、`app.py` 加 `@teacher_required` 路由、`TeacherDashboard.jsx` 加顯示
- 「讓學生對回答按讚／倒讚」→ 新增 `feedback` 資料表與 `/api/feedback` 路由
