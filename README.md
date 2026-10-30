# 活動報名系統

## 執行需求

- Python 3.12 或更新版本
- PostgreSQL，並先建立應用程式使用的資料庫

## 安裝與啟動

Windows 使用者可雙擊 [start_backend.bat](./start_backend.bat) 啟動後端。首次執行會建立虛擬環境並安裝依賴，然後建立並開啟 `.env` 範本；請將 `your_password` 換成 PostgreSQL 的實際密碼並儲存，再雙擊一次啟動。`.env` 是本機設定檔，不會提交至 Git。

在專案根目錄執行：

```powershell
py -m venv .venv-runtime
.\.venv-runtime\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

編輯 `.env`，將 `DATABASE_URL` 設為有效的 PostgreSQL 連線字串，並使用自己的資料庫帳號與密碼。

確認 PostgreSQL 正在執行，且 `event_db` 資料庫已建立，再啟動伺服器：

```powershell
.\.venv-runtime\Scripts\python.exe -m uvicorn main:app --reload
```

瀏覽 <http://127.0.0.1:8000/> 開啟活動列表。
請從伺服器網址開啟頁面，不要直接雙擊 `index.html`；頁面需透過 `/api/events` 與資料庫同步活動及報名資料。
