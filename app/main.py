from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.database import connect_to_mongo, close_mongo_connection
from app.routes import router
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()

app = FastAPI(
    title=settings.APP_NAME,
    description="Comprehensive therapy management system for autistic children",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Templates
templates_path = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_path)

# Include API routes
app.include_router(router, prefix="/api")

# ==================== HTML ROUTES ====================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/doctor/dashboard", response_class=HTMLResponse)
async def doctor_dashboard(request: Request):
    return templates.TemplateResponse("doctor_dashboard.html", {"request": request})

@app.get("/doctor/add-child", response_class=HTMLResponse)
async def add_child_page(request: Request):
    return templates.TemplateResponse("add_child.html", {"request": request})

@app.get("/doctor/my-children", response_class=HTMLResponse)
async def my_children_page(request: Request):
    return templates.TemplateResponse("my_children.html", {"request": request})

@app.get("/doctor/sessions", response_class=HTMLResponse)
async def sessions_page(request: Request):
    return templates.TemplateResponse("sessions.html", {"request": request})

@app.get("/doctor/reports", response_class=HTMLResponse)
async def reports_page(request: Request):
    return templates.TemplateResponse("reports.html", {"request": request})

@app.get("/doctor/add-session/{child_id}", response_class=HTMLResponse)
async def add_session_page(request: Request, child_id: str):
    return templates.TemplateResponse("add_session.html", {"request": request, "child_id": child_id})

@app.get("/doctor/view-child/{child_id}", response_class=HTMLResponse)
async def view_child_page(request: Request, child_id: str):
    return templates.TemplateResponse("view_child.html", {"request": request, "child_id": child_id})

@app.get("/parent/dashboard", response_class=HTMLResponse)
async def parent_dashboard(request: Request):
    return templates.TemplateResponse("parent_dashboard.html", {"request": request})

@app.get("/parent/view-child/{child_id}", response_class=HTMLResponse)
async def parent_view_child_page(request: Request, child_id: str):
    return templates.TemplateResponse("parent_view_child.html", {"request": request, "child_id": child_id})

@app.get("/reports/weekly/{child_id}", response_class=HTMLResponse)
async def weekly_report_page(request: Request, child_id: str):
    return templates.TemplateResponse("weekly_report.html", {"request": request, "child_id": child_id})

@app.get("/reports/monthly/{child_id}", response_class=HTMLResponse)
async def monthly_report_page(request: Request, child_id: str):
    return templates.TemplateResponse("monthly_report.html", {"request": request, "child_id": child_id})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
