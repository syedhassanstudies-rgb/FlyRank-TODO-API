from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from supabase import create_client, Client
import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id    SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            done  BOOLEAN DEFAULT FALSE
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()["count"]
    if count == 0:
        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES (%s, %s)",
            [
                ("Create a calculator", False),
                ("Make a Game", False),
                ("Read Documents", True)
            ]
        )
    conn.commit()
    cursor.close()
    conn.close()

init_db()

# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Auth scheme
bearer_scheme = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    try:
        response = supabase.auth.get_user(token)
        if response.user is None:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return response.user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

app = FastAPI()

# ── Info routes ──────────────────────────────────────────
@app.get("/", summary="Shows API info: Name, Version, Endpoints")
def api_info():
    return {
        "name": "TODO_API",
        "version": "1.0.0",
        "endpoints": ["/tasks", "/auth", "/protected", "/public"]
    }

@app.get("/health", summary="Shows Health of the API")
def return_health():
    return {"health": "API Healthy"}

# ── Public route ─────────────────────────────────────────
@app.get("/public/info", summary="Public endpoint — no auth needed")
def public_info():
    return {"message": "Welcome stranger! This info is public."}

# ── Auth routes ──────────────────────────────────────────
class AuthCredentials(BaseModel):
    email: str
    password: str

@app.post("/auth/signup", status_code=201, summary="Register a new user")
def signup(credentials: AuthCredentials):
    if not credentials.email or not credentials.password:
        raise HTTPException(status_code=400, detail="Email and password required")
    try:
        response = supabase.auth.sign_up({
            "email": credentials.email,
            "password": credentials.password
        })
        return {"user": response.user}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/login", summary="Login and get JWT")
def login(credentials: AuthCredentials):
    if not credentials.email or not credentials.password:
        raise HTTPException(status_code=400, detail="Email and password required")
    try:
        response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid login credentials")

@app.post("/auth/logout", status_code=204, summary="Logout current user")
def logout(user=Depends(get_current_user)):
    try:
        supabase.auth.sign_out()
        return
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ── Protected routes ─────────────────────────────────────
@app.get("/protected/profile", summary="Get current user profile")
def profile(user=Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at
    }

@app.get("/protected/dashboard", summary="Protected dashboard")
def dashboard(user=Depends(get_current_user)):
    return {"message": f"Welcome to your dashboard, {user.email}"}

# ── Task routes ──────────────────────────────────────────
class TaskCreate(BaseModel):
    title: str

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

@app.get("/tasks", summary="Shows all the Tasks Created")
def get_all_tasks():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(task) for task in tasks]

@app.get("/tasks/{id}", summary="Shows Task by ID")
def get_tasks_by_id(id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (id,))
    task = cursor.fetchone()
    cursor.close()
    conn.close()
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {id} not found")
    return dict(task)

@app.post("/tasks", status_code=201, summary="Creates Task")
def create_task(task: TaskCreate):
    if not task.title.strip():
        raise HTTPException(status_code=400, detail="Task title cannot be empty")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING *",
        (task.title.strip(), False)
    )
    new_task = dict(cursor.fetchone())
    conn.commit()
    cursor.close()
    conn.close()
    return new_task

@app.put("/tasks/{id}", summary="Update an Existing Task")
def update_task(id: int, update: TaskUpdate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (id,))
    task = cursor.fetchone()
    if task is None:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {id} not found")
    if update.title is not None and not update.title.strip():
        cursor.close()
        conn.close()
        raise HTTPException(status_code=400, detail="Task title cannot be empty")
    new_title = update.title.strip() if update.title is not None else task["title"]
    new_done = update.done if update.done is not None else task["done"]
    cursor.execute(
        "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING *",
        (new_title, new_done, id)
    )
    updated_task = dict(cursor.fetchone())
    conn.commit()
    cursor.close()
    conn.close()
    return updated_task

@app.delete("/tasks/{id}", status_code=204, summary="Delete an Existing Task")
def delete_task(id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (id,))
    task = cursor.fetchone()
    if task is None:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {id} not found")
    cursor.execute("DELETE FROM tasks WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()