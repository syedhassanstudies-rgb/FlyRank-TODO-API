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


@app.get("/", summary="Shows API info: Name,Version,Endpoints")
def api_info():
    return {
        "name": "TODO_API",
        "version": "1.0.0",
        "endpoints": ["2"]
    }

@app.get("/health", summary="Shows Health of the API")
def return_health():
    return {"health": "API Healthy"}

@app.get("/tasks", summary="Shows all the Tasks Created")
def get_all_tasks():
    return tasks

@app.get("/tasks/{id}", summary="Shows Task by ID")
def get_tasks_by_id(id : int):
    for task in tasks:
        if task["id"] == id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {id} not found")
        
class TaskCreate(BaseModel):
    title: str

@app.post("/tasks",status_code=201, summary="Creates Task")
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


@app.put("/tasks/{id}", summary="Update an Existing Task")
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

@app.delete("/tasks/{id}", status_code=204, summary="Delete an Existing task")
def delete_task(id: int):
    for index, task in enumerate(tasks):
        if task["id"] == id:
            tasks.pop(index)
            return
    raise HTTPException(status_code=404, detail=f"Task {id} not found")
        
