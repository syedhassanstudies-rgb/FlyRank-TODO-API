from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv

load_dotenv()

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

class TaskCreate(BaseModel):
    title: str

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

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

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