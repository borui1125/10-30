"""
主應用程式 (main.py)
負責活動報名系統之所有後端路由與資料庫操作
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, List, Optional
from urllib.parse import quote

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# 匯入組員 A 定義之資料模型
from models import Base, Event, Registration

# 載入環境變數
load_dotenv()

# 資料庫連線字串設定 (優先讀取 DATABASE_URL，若無則依獨立變數組裝)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "postgres")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "event_db")
    DATABASE_URL = f"postgresql+psycopg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# 若前綴為 postgresql://，自動轉換為 postgresql+psycopg:// 以相容 psycopg 3
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

# 建立 SQLAlchemy Engine 與 SessionLocal
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 依賴注入取得資料庫 Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 應用程式生命週期管理：啟動時自動檢查並建立資料表
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ [DB] 資料表連線與結構確認成功")
    except Exception as e:
        print(f"⚠️ [DB Warning] 資料表初始化未完成（請確認 PostgreSQL 服務與環境變數設定）：{e}")
    yield


app = FastAPI(title="活動報名系統", lifespan=lifespan)

# 確保 templates 目錄存在（不建立任何模板檔案）
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def render_page(
    request: Request,
    page: str,
    events: Optional[List[Event]] = None,
    event: Optional[Event] = None,
    registrations: Optional[List[Registration]] = None,
    message: Optional[str] = None,
    error: Optional[str] = None,
    status_code: int = status.HTTP_200_OK,
):
    """
    統一渲染 templates/index.html 的輔助函式
    確保六個通用模板變數皆傳入 Jinja2 模板
    """
    context = {
        "request": request,
        "page": page,
        "events": events,
        "event": event,
        "registrations": registrations,
        "message": message,
        "error": error,
    }
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context,
        status_code=status_code,
    )


# ==========================================================
# 路由定義 (嚴格遵守規格)
# ==========================================================


@app.get("/", response_class=HTMLResponse)
def list_events(
    request: Request,
    message: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    1. GET /：顯示活動列表
    """
    try:
        events = db.query(Event).order_by(Event.id.desc()).all()
    except Exception as e:
        events = []
        error = f"讀取活動清單失敗：{str(e)}"

    return render_page(
        request=request,
        page="event_list",
        events=events,
        message=message,
        error=error,
    )


@app.get("/events/new", response_class=HTMLResponse)
def new_event_form(
    request: Request,
    message: Optional[str] = None,
    error: Optional[str] = None,
):
    """
    2. GET /events/new：顯示新增活動表單
    """
    return render_page(
        request=request,
        page="event_new",
        message=message,
        error=error,
    )


@app.post("/events")
def create_event(
    request: Request,
    name: str = Form(""),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    3. POST /events：建立活動
    驗證必要欄位並防範重新整理重複提交 (PRG Pattern)
    """
    name_clean = name.strip()
    desc_clean = description.strip() if description else None

    # 後端驗證：活動名稱為必填
    if not name_clean:
        return render_page(
            request=request,
            page="event_new",
            error="活動名稱為必填欄位",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        new_event = Event(name=name_clean, description=desc_clean)
        db.add(new_event)
        db.commit()
        db.refresh(new_event)
    except Exception as e:
        db.rollback()
        return render_page(
            request=request,
            page="event_new",
            error=f"建立活動時發生錯誤：{str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # 建立成功，使用 HTTP 303 重新導向至首頁並帶上成功訊息
    redirect_url = f"/?message={quote('活動建立成功！')}"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@app.get("/events/{event_id}/register", response_class=HTMLResponse)
def show_register_form(
    event_id: int,
    request: Request,
    message: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    4. GET /events/{event_id}/register：顯示指定活動的報名表
    """
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
    except Exception as e:
        return render_page(
            request=request,
            page="error",
            error=f"資料庫查詢失敗：{str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # 活動不存在時顯示錯誤
    if not event:
        return render_page(
            request=request,
            page="error",
            error="指定的活動不存在",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    return render_page(
        request=request,
        page="event_register",
        event=event,
        message=message,
        error=error,
    )


@app.post("/events/{event_id}/register")
def submit_registration(
    event_id: int,
    request: Request,
    name: str = Form(""),
    phone: str = Form(""),
    db: Session = Depends(get_db),
):
    """
    5. POST /events/{event_id}/register：提交報名資料
    接收姓名與聯絡電話，驗證並存入資料庫，成功後 Redirect 至報名清單頁
    """
    # 檢查活動是否存在
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
    except Exception as e:
        return render_page(
            request=request,
            page="error",
            error=f"資料庫查詢失敗：{str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if not event:
        return render_page(
            request=request,
            page="error",
            error="指定的活動不存在，無法進行報名",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    name_clean = name.strip()
    phone_clean = phone.strip()

    # 後端驗證：姓名與電話為必填
    if not name_clean or not phone_clean:
        return render_page(
            request=request,
            page="event_register",
            event=event,
            error="姓名與聯絡電話皆為必填欄位",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        registration = Registration(
            event_id=event_id,
            name=name_clean,
            phone=phone_clean,
        )
        db.add(registration)
        db.commit()
        db.refresh(registration)
    except Exception as e:
        db.rollback()
        return render_page(
            request=request,
            page="event_register",
            event=event,
            error=f"儲存報名資料時發生錯誤：{str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # 報名成功，使用 HTTP 303 重新導向至該活動的報名清單頁
    redirect_url = f"/events/{event_id}/registrations?message={quote('報名成功！')}"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@app.get("/events/{event_id}/registrations", response_class=HTMLResponse)
def show_registrations(
    event_id: int,
    request: Request,
    message: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    6. GET /events/{event_id}/registrations：顯示指定活動的報名清單
    """
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
    except Exception as e:
        return render_page(
            request=request,
            page="error",
            error=f"資料庫查詢失敗：{str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # 活動不存在時顯示錯誤
    if not event:
        return render_page(
            request=request,
            page="error",
            error="指定的活動不存在",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    try:
        registrations = (
            db.query(Registration)
            .filter(Registration.event_id == event_id)
            .order_by(Registration.id.asc())
            .all()
        )
    except Exception as e:
        registrations = []
        error = f"讀取報名清單失敗：{str(e)}"

    return render_page(
        request=request,
        page="event_registrations",
        event=event,
        registrations=registrations,
        message=message,
        error=error,
    )
