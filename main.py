from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
app = FastAPI()

#Tasks Data
tasks = [
    {"id": 1, "title": "Create a calculator", "done": False},
    {"id": 2, "title": "Make a Game", "done": True},
    {"id": 3, "title": "Read Documents", "done": True},
]


@app.get("/")
def api_info():
    return {
        "name": "TODO_API",
        "version": "1.0.0",
        "endpoints": ["2"]
    }

@app.get("/health")
def return_health():
    return {"health": "API Healthy"}

@app.get("/tasks")
def get_all_tasks():
    return tasks

@app.get("/tasks/{id}")
def get_tasks_by_id(id : int):
    for task in tasks:
        if task["id"] == id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {id} not found")
        
class TaskCreate(BaseModel):
    title: str

@app.post("/tasks",status_code=201)
def create_task(task: TaskCreate):
    if not task.title.strip():
        raise HTTPException(status_code=400, detail="Task Title Cannot be Empty")
    new_task = {
        "id": tasks[-1]["id"] + 1,
        "title": task.title,
        "done": False,
    }

    tasks.append(new_task)
    return new_task


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None


@app.put("/tasks/{id}")
def update_task(id :int, update: TaskUpdate):
    for task in tasks:
        if task["id"] == id:
            if update.title is not None:
                if not update.title.strip():
                    raise  HTTPException(status_code=400, detail="Task cannot be empty")
                task["title"] = update.title
            if update.done is not None:
                task["done"] = update.done
            return task
    raise HTTPException(status_code=404, detail=f"Task {id} not found")

@app.delete("/tasks/{id}", status_code=204)
def delete_task(id: int):
    for index, task in enumerate(tasks):
        if task["id"] == id:
            tasks.pop(index)
            return
    raise HTTPException(status_code=404, detail=f"Task {id} not found")
        
