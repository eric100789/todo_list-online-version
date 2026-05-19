你現在是一位頂尖的資深軟體工程師與架構師（Senior Software Engineer & Architect）。
我需要你幫我將一套現有的 Python PyQt6 桌面應用程式，徹底改造為「前後端分離」的現代化網頁與容器化架構。

請根據以下提供的系統背景與 5 大核心需求，直接為我生成可實作的專案架構、後端程式碼、資料庫遷移指令以及部署設定檔：

### 📌 系統背景與技術選型
1. 舊系統：完全基於 Python 撰寫，GUI 介面使用 PyQt6。
2. 新後端：指定使用 Python FastAPI 框架。
3. 資料庫：原本使用 SQLite3，現在需要遷移並升級至 PostgreSQL
4. 前端：請基於原本的 PyQt6 GUI 功能邏輯，建立一套現代網頁前端架構，並說明原本的桌面端如何改為透過 API Call 與新後端溝通。

---

### 🛠️ 改造核心需求（請逐一完成並給出程式碼/設定檔）

#### 1. API 化與特殊登入機制 (FastAPI Auth & Session Management)
- 將原本 PyQt6 中的所有核心商業邏輯與資料操作，全部改造成 FastAPI 的 RESTful API 路由。
- 實作一個「永久有效，但具備排他性（Single Device Session）」的登入系統。
- 規則細節：
  - 使用者可以註冊一組帳戶（需要email, username, password），註冊功能可以隨時關閉（更改config或是env來開關功能）
  - 使用者登入後，Token/Session 絕對不會因為時間到期而失效（No Expiration）。
  - 使用者可以踢除（Revoke/Kick out）該帳號在其他地方的舊登入狀態。
  - 請在 PostgreSQL 中設計對應的 `users` 與 `sessions` 資料表（或利用 Token Version 機制），並給出 FastAPI 的 Auth Middleware/Dependency 實作程式碼。

#### 2. 前端網頁化與用戶端 API 呼叫策略
- 說明你如何將原本的 PyQt6 介面邏輯轉換為 Web 前端（請給出一個核心功能的前端 Fetch API 呼叫範例）。
- 若要保留桌面端外殼，請說明如何改造原本的 PyQt6，使其不直接連線資料庫，而是改為透過 `httpx` 或 `requests` 呼叫 FastAPI 進行操作。

#### 3. 環境變數管理 (.env)
- 系統的所有敏感資訊（資料庫連線字串、JWT Secret Key、Port 等）必須完全從程式碼中抽離，統一由 `.env` 管理。
- 請提供一份完整的 `.env.example` 檔案內容，並在 FastAPI 中使用 `pydantic-settings` 進行讀取。

#### 4. Git 安全策略 (.gitignore)
- 確保所有敏感資訊、虛擬環境、暫存檔不會流出。
- 請提供一份針對此 Python FastAPI + PostgreSQL + 前端專案的 `.gitignore` 檔案內容。

#### 5. 容器化部署 (Docker & Docker Compose)
- 請編寫生產環境等級的 `Dockerfile`（採用多階段構建 Multi-stage build 以優化映像檔大小）。
- 請提供一個 `docker-compose.yml` 檔案，需包含：
  - FastAPI 後端服務
  - PostgreSQL 資料庫服務（含環境變數與 Volume 持久化設定）
  - 前端靜態服務（如使用 Nginx 代理）
  - 確保執行 `docker-compose up --build` 就能一鍵啟動整個開發/部署環境。

---