# Todo Online Version — Migration to FastAPI + PostgreSQL + Docker

This repository contains a minimal migration of the original PyQt6 desktop Todo app into a backend API (FastAPI), PostgreSQL database, a small static frontend and Docker Compose deployment.

Quick start (development):

1. Copy `.env.example` to `.env` and edit values.

2. Start services:

```bash
docker-compose up --build
```

3. Create DB schema (run inside the `db` container or from host with psql):

```bash
# the repository is mounted into containers at /workspace — run the SQL migration file inside the db container
docker-compose exec db psql -U postgres -d todo_db -f /workspace/migrations/initial.sql
```

Notes:
- Backend API runs at `http://localhost:8000`.
- Frontend static site served at `http://localhost:3000` (proxied to backend for `/api`).

Auth and session notes:
- Login issues a permanent session token (no expiration) stored in `sessions` table.
- Single-device policy: login removes other sessions for the same user.
- Use header `Authorization: Bearer <token>` for authenticated requests.

PyQt6 desktop integration:

- Replace direct DB access in the PyQt6 app with HTTP calls. See [docs/pyqt_integration.md](docs/pyqt_integration.md) for an example using `httpx`.


Files added:
- `backend/` — FastAPI app and Dockerfile
- `frontend/` — simple static UI example (index.html + app.js)
- `nginx/` — nginx conf used by the frontend image to proxy `/api` to backend
- `docker-compose.yml` — orchestrates `db`, `backend`, `frontend`
- `.env.example` — environment variables template
- `migrations/initial.sql` — initial SQL to create tables in PostgreSQL

Migration / production notes:
- For production you should run Alembic migrations. The SQL in `migrations/initial.sql` is a starting point.
- Replace `SECRET_KEY` with a secure random value.
- Consider running the backend behind a production-grade process manager and TLS terminator.
# Todo List 待辦清單應用程式

使用 Python + PyQt6 + SQLite3 開發的桌面待辦工具，支援任務清單、Kanban 看板、歷史紀錄、記事與迷你模式。

## 功能總覽

### 任務清單
1. 新增、編輯、刪除、完成任務
2. 星號標記重要任務
3. 任務顏色可選預設色或自訂色
4. 截止日期支援 MM/DD 與 YYYY/MM/DD
5. 截止日期月曆視窗會展開顯示完整日期格

### Kanban 看板
1. 任務與清單完全同步
2. 未分類欄位會接住一般新增任務
3. 可新增、編輯、刪除分類
4. 每個分類可設定顏色（預設色或自訂色）
5. 在分類標題的拖曳把手可拖曳分類，並儲存排序
6. 任務可拖曳到任一分類欄位
7. 每個分類欄位可直接按 + 新增任務到該欄
8. 可在看板直接完成或刪除任務

### Kanban 版面策略
1. 看板固定提供橫向捲軸，可在小視窗下查看全部分類
2. 可在設定頁調整「欄位最小寬度」
3. 欄位最小寬度變更時，欄內任務卡片寬度會同步更新
4. 設定頁可一鍵恢復預設欄寬

### 迷你模式
1. 可切換清單 / 看板顯示
2. 可調整透明度與是否置頂
3. 會記住迷你模式顯示型態

### 其他
1. 歷史（列表/月曆）與記事功能
2. 深色/淺色主題
3. 中英文切換
4. 偏好設定自動儲存於 prefs.json

## 快速開始

### 環境需求
1. Python 3.10+
2. PyQt6

### 安裝

```bash
pip install PyQt6
```

### 執行

```bash
python main.py
```

## 主要操作

### 看板分類拖曳排序
1. 開啟看板頁
2. 在分類標題的「↕」把手按住拖曳到目標分類上
3. 放開後會立即更新排序並寫入資料庫

### 看板欄寬與捲軸
1. 進入設定頁的「看板設定」
2. 調整「欄位最小寬度」
3. 使用「恢復預設」可快速還原看板寬度
4. 在看板底部使用水平捲軸切換到其他欄位

### 截止日期月曆
1. 在新增/編輯任務視窗點擊日期按鈕
2. 視窗會展開，顯示完整月曆日期
3. 選取日期後會自動收合回一般高度

## 打包 EXE

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name "TodoList" main.py
```

或直接執行 build_exe.bat。

## 重置資料庫

```bash
python reset_db.py
```

此操作會永久刪除資料，請先備份。

## 專案結構

```text
todo/
|- main.py
|- main_window.py
|- kanban_view.py
|- task_card.py
|- dialogs.py
|- settings_panel.py
|- mini_mode.py
|- history_view.py
|- notes_view.py
|- database.py
|- i18n.py
|- styles.py
|- date_utils.py
|- build_exe.bat
|- reset_db.py
`- README.md
```
