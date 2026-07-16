from fastapi import FastAPI

app = FastAPI()

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

