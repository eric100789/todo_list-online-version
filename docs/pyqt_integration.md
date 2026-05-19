PyQt6 integration notes

To adapt the original PyQt6 desktop UI to call the new FastAPI backend, replace direct SQLite access with HTTP calls using `httpx` or `requests`.

Example (using `httpx`):

```python
import httpx

API_BASE = "http://localhost:8000"

def login(email_or_username: str, password: str):
    payload = {"email": email_or_username, "username": email_or_username, "password": password}
    r = httpx.post(f"{API_BASE}/auth/login", json=payload)
    r.raise_for_status()
    return r.json()["token"]

def list_tasks(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    r = httpx.get(f"{API_BASE}/tasks", headers=headers)
    r.raise_for_status()
    return r.json()

# Use these functions inside your PyQt6 handlers instead of DB queries.
```

Notes:
- Store the returned token in memory or secure store. The backend issues permanent non-expiring tokens.
- To perform actions on behalf of the logged-in user, include the `Authorization: Bearer <token>` header.
