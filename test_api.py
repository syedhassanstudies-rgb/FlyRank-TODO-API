import requests
import random

BASE_URL = "http://localhost:8000"
EMAIL = f"testuser{random.randint(1000,9999)}@gmail.com"
PASSWORD = "password123"

def log(label, response, expected_status=None):
    status = response.status_code
    try:
        body = response.json()
    except:
        body = response.text
    if expected_status:
        icon = "✅" if status == expected_status else "❌"
    else:
        icon = "✅" if response.ok else "❌"
    print(f"{icon} [{status}] {label}")
    print(f"   {body}\n")

print("=" * 50)
print("FLYRANK API TEST SUITE")
print("=" * 50)

# Info routes
r = requests.get(f"{BASE_URL}/")
log("GET /", r, 200)

r = requests.get(f"{BASE_URL}/health")
log("GET /health", r, 200)

# Public route
r = requests.get(f"{BASE_URL}/public/info")
log("GET /public/info", r, 200)

# Protected without token
r = requests.get(f"{BASE_URL}/protected/profile")
log("GET /protected/profile (no token) → expect 401", r, 401)

# Signup
r = requests.post(f"{BASE_URL}/auth/signup", json={"email": EMAIL, "password": PASSWORD})
log(f"POST /auth/signup ({EMAIL})", r, 201)

# Login
r = requests.post(f"{BASE_URL}/auth/login", json={"email": EMAIL, "password": PASSWORD})
log("POST /auth/login", r, 200)
token = r.json().get("access_token") if r.ok else None

# Wrong password
r = requests.post(f"{BASE_URL}/auth/login", json={"email": EMAIL, "password": "wrongpassword"})
log("POST /auth/login (wrong password) → expect 401", r, 401)

# Empty fields
r = requests.post(f"{BASE_URL}/auth/signup", json={"email": "", "password": ""})
log("POST /auth/signup (empty fields) → expect 400", r, 400)

# Protected with valid token
headers = {"Authorization": f"Bearer {token}"} if token else {}

r = requests.get(f"{BASE_URL}/protected/profile", headers=headers)
log("GET /protected/profile (valid token) → expect 200", r, 200)

r = requests.get(f"{BASE_URL}/protected/dashboard", headers=headers)
log("GET /protected/dashboard (valid token) → expect 200", r, 200)

# Fake token
r = requests.get(f"{BASE_URL}/protected/profile", headers={"Authorization": "Bearer faketoken123"})
log("GET /protected/profile (fake token) → expect 401", r, 401)

# Task routes
r = requests.get(f"{BASE_URL}/tasks")
log("GET /tasks", r, 200)

r = requests.post(f"{BASE_URL}/tasks", json={"title": "Test task from script"})
log("POST /tasks", r, 201)
task_id = r.json().get("id") if r.ok else None

r = requests.get(f"{BASE_URL}/tasks/{task_id}")
log(f"GET /tasks/{task_id}", r, 200)

r = requests.put(f"{BASE_URL}/tasks/{task_id}", json={"title": "Updated task", "done": True})
log(f"PUT /tasks/{task_id}", r, 200)

r = requests.post(f"{BASE_URL}/tasks", json={"title": ""})
log("POST /tasks (empty title) → expect 400", r, 400)

r = requests.get(f"{BASE_URL}/tasks/99999")
log("GET /tasks/99999 → expect 404", r, 404)

r = requests.delete(f"{BASE_URL}/tasks/{task_id}")
log(f"DELETE /tasks/{task_id} → expect 204", r, 204)

# Logout
r = requests.post(f"{BASE_URL}/auth/logout", headers=headers)
log("POST /auth/logout → expect 204", r, 204)

print("=" * 50)
print("TEST SUITE COMPLETE")
print("=" * 50)