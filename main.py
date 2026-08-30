from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import sqlite3

def get_db():
    conn = sqlite3.connect("tasks.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done  INTEGER DEFAULT 0
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.executemany(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            [
                ("Create a calculator", 0),
                ("Make a Game", 0),
                ("Read Documents", 1)
            ]
        )
    conn.commit()
    conn.close()

init_db()

app = FastAPI()

@app.get("/", summary="Shows API info: Name,Version,Endpoints")
def api_info():
    return {
        "name": "TODO_API",
        "version": "1.0.0",
        "endpoints": ["/tasks"]
    }

@app.get("/health", summary="Shows Health of the API")
def return_health():
    return {"health": "API Healthy"}

@app.get("/tasks", summary="Shows all the Tasks Created")
def get_all_tasks():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()
    conn.close()
    return [dict(task) for task in tasks]

@app.get("/tasks/{id}", summary="Shows Task by ID")
def get_tasks_by_id(id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (id,))
    task = cursor.fetchone()
    conn.close()
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {id} not found")
    return dict(task)

class TaskCreate(BaseModel):
    title: str

@app.post("/tasks", status_code=201, summary="Creates Task")
def create_task(task: TaskCreate):
    if not task.title.strip():
        raise HTTPException(status_code=400, detail="Task Title Cannot be Empty")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (title, done) VALUES (?, ?)",
        (task.title.strip(), 0)
    )
    conn.commit()
    new_id = cursor.lastrowid
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (new_id,))
    new_task = dict(cursor.fetchone())
    conn.close()
    return new_task

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

@app.put("/tasks/{id}", summary="Update an Existing Task")
def update_task(id: int, update: TaskUpdate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (id,))
    task = cursor.fetchone()
    if task is None:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {id} not found")
    if update.title is not None and not update.title.strip():
        conn.close()
        raise HTTPException(status_code=400, detail="Task title cannot be empty")
    new_title = update.title.strip() if update.title is not None else task["title"]
    new_done = int(update.done) if update.done is not None else task["done"]
    cursor.execute(
        "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
        (new_title, new_done, id)
    )
    conn.commit()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (id,))
    updated_task = dict(cursor.fetchone())
    conn.close()
    return updated_task

@app.delete("/tasks/{id}", status_code=204, summary="Delete an Existing task")
def delete_task(id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (id,))
    task = cursor.fetchone()
    if task is None:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Task {id} not found")
    cursor.execute("DELETE FROM tasks WHERE id = ?", (id,))
    conn.commit()
    conn.close()