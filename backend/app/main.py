from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import sqlite3, time, uuid, os

app = FastAPI()
DB = "pastes.db"

# ---------- DB ----------
def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pastes (
        id TEXT PRIMARY KEY,
        content TEXT NOT NULL,
        expires_at INTEGER,
        max_views INTEGER,
        views INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------- MODELS ----------
class PasteIn(BaseModel):
    content: str
    ttl_seconds: int | None = None
    max_views: int | None = None

# ---------- TIME ----------
def now_ms(req: Request):
    if os.getenv("TEST_MODE") == "1":
        h = req.headers.get("x-test-now-ms")
        if h:
            return int(h)
    return int(time.time() * 1000)

# ---------- HEALTH ----------
@app.get("/api/healthz")
def healthz():
    return {"ok": True}

# ---------- CREATE ----------
@app.post("/api/pastes")
def create_paste(p: PasteIn):
    if not p.content.strip():
        raise HTTPException(400, detail="content required")

    expires = None
    if p.ttl_seconds:
        expires = int(time.time() * 1000) + p.ttl_seconds * 1000

    pid = uuid.uuid4().hex[:8]

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO pastes VALUES (?,?,?,?,0)",
        (pid, p.content, expires, p.max_views)
    )
    conn.commit()
    conn.close()

    return {"id": pid, "url": f"/p/{pid}"}

# ---------- FETCH ----------
def fetch_paste(pid, now):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        "SELECT content, expires_at, max_views, views FROM pastes WHERE id=?",
        (pid,)
    )
    row = cur.fetchone()

    if not row:
        conn.close()
        return None

    content, expires, maxv, views = row

    if expires and now > expires:
        conn.close()
        return None

    if maxv and views >= maxv:
        conn.close()
        return None

    cur.execute("UPDATE pastes SET views = views + 1 WHERE id=?", (pid,))
    conn.commit()
    conn.close()

    return content

# ---------- API FETCH ----------
@app.get("/api/pastes/{pid}")
def get_paste(pid: str, req: Request):
    content = fetch_paste(pid, now_ms(req))
    if not content:
        raise HTTPException(404)
    return {"content": content}

# ---------- HTML VIEW ----------
@app.get("/p/{pid}", response_class=HTMLResponse)
def view_paste(pid: str, req: Request):
    content = fetch_paste(pid, now_ms(req))
    if not content:
        raise HTTPException(404)

    safe = content.replace("<","&lt;").replace(">","&gt;")
    return f"<pre>{safe}</pre>"
