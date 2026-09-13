from fastapi import FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from llm.schema import TriageRequest, TriageResponse, Category, Urgency
from pydantic import BaseModel, Field
from typing import Optional
import sqlite3
import os
from dotenv import load_dotenv
load_dotenv()


app = FastAPI(
    title="Task API",
    version="1.0",
    description="Simple CRUD API for managing tasks."
)


# Convert FastAPI validation errors from 422 to 400.
# This is required for the A17 /triage endpoint.
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    fields = sorted({
        str(error["loc"][-1])
        for error in exc.errors()
        if len(error.get("loc", [])) > 1
    })

    return JSONResponse(
        status_code=400,
        content={
            "error": "Invalid request",
            "fields": fields
        }
    )


class Task(BaseModel):
    id: int
    title: str
    done: bool


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1)


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None


DATABASE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "tasks.db"
)

print("DATABASE BEING USED:", DATABASE)


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT 0
        )
    """)

    cursor = conn.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]

    if count == 0:
        conn.executemany(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            [
                ("Learn FastAPI", 0),
                ("Complete CRUD Assignment", 0),
                ("Push to GitHub", 1)
            ]
        )

    conn.commit()
    conn.close()


init_db()


@app.get("/", summary="API Information")
def root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks", "/triage"]
    }


@app.get("/health", summary="Health Check")
def health():
    return {"status": "ok"}


@app.get("/tasks", summary="Get All Tasks")
def get_tasks():
    conn = get_db()

    rows = conn.execute(
        "SELECT id, title, done FROM tasks"
    ).fetchall()

    conn.close()

    return [
        Task(
            id=row["id"],
            title=row["title"],
            done=bool(row["done"])
        )
        for row in rows
    ]


@app.get("/tasks/{task_id}", summary="Get Task By ID")
def get_task(task_id: int):
    conn = get_db()

    row = conn.execute(
        "SELECT id, title, done FROM tasks WHERE id = ?",
        (task_id,)
    ).fetchone()

    conn.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )

    return Task(
        id=row["id"],
        title=row["title"],
        done=bool(row["done"])
    )


@app.post(
    "/tasks",
    status_code=status.HTTP_201_CREATED,
    summary="Create Task"
)
def create_task(task: TaskCreate):
    title = task.title.strip()

    if not title:
        raise HTTPException(
            status_code=400,
            detail="Title is required"
        )

    conn = get_db()

    cursor = conn.execute(
        "INSERT INTO tasks (title, done) VALUES (?, ?)",
        (title, 0)
    )

    task_id = cursor.lastrowid

    conn.commit()

    row = conn.execute(
        "SELECT id, title, done FROM tasks WHERE id = ?",
        (task_id,)
    ).fetchone()

    conn.close()

    return Task(
        id=row["id"],
        title=row["title"],
        done=bool(row["done"])
    )


@app.put("/tasks/{task_id}", summary="Update Task")
def update_task(task_id: int, updated: TaskUpdate):

    if updated.title is None and updated.done is None:
        raise HTTPException(
            status_code=400,
            detail="Request body cannot be empty"
        )

    conn = get_db()

    row = conn.execute(
        "SELECT id, title, done FROM tasks WHERE id = ?",
        (task_id,)
    ).fetchone()

    if row is None:
        conn.close()

        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )

    new_title = row["title"]
    new_done = bool(row["done"])

    if updated.title is not None:

        if not updated.title.strip():
            conn.close()

            raise HTTPException(
                status_code=400,
                detail="Title cannot be empty"
            )

        new_title = updated.title.strip()

    if updated.done is not None:
        new_done = updated.done

    conn.execute(
        """
        UPDATE tasks
        SET title = ?, done = ?
        WHERE id = ?
        """,
        (new_title, int(new_done), task_id)
    )

    conn.commit()

    row = conn.execute(
        "SELECT id, title, done FROM tasks WHERE id = ?",
        (task_id,)
    ).fetchone()

    conn.close()

    return Task(
        id=row["id"],
        title=row["title"],
        done=bool(row["done"])
    )


@app.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Task"
)
def delete_task(task_id: int):

    conn = get_db()

    row = conn.execute(
        "SELECT id FROM tasks WHERE id = ?",
        (task_id,)
    ).fetchone()

    if row is None:
        conn.close()

        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )

    conn.execute(
        "DELETE FROM tasks WHERE id = ?",
        (task_id,)
    )

    conn.commit()
    conn.close()

    return


# A17 Stage 1 endpoint.
# No real LLM call is made yet.
@app.post("/triage", response_model=TriageResponse)
def triage(request: TriageRequest):

    if os.getenv("LLM_STUB", "0") == "1":
        return TriageResponse(
            category=Category.other,
            urgency=Urgency.normal,
            confidence=0.0,
            reason="Stub response; LLM is disabled."
        )

    raise HTTPException(
        status_code=503,
        detail="LLM integration is not enabled yet."
    )