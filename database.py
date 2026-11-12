import sqlite3
from pathlib import Path
from datetime import datetime, timezone
import json

DB_PATH = Path(__file__).parent / "trustpay.db"

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            client_name TEXT NOT NULL,
            freelancer_name TEXT NOT NULL,
            total_amount REAL NOT NULL,
            currency TEXT NOT NULL DEFAULT 'USD',
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS milestones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            requirements TEXT NOT NULL,
            amount REAL NOT NULL,
            due_date TEXT,
            status TEXT NOT NULL DEFAULT 'PENDING',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            milestone_id INTEGER NOT NULL REFERENCES milestones(id) ON DELETE CASCADE,
            evidence_text TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS ai_verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id INTEGER NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
            completed_requirements TEXT NOT NULL,
            missing_requirements TEXT NOT NULL,
            confidence REAL NOT NULL,
            recommendation TEXT NOT NULL,
            explanation TEXT NOT NULL,
            mode TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            milestone_id INTEGER NOT NULL REFERENCES milestones(id),
            paypal_order_id TEXT UNIQUE,
            paypal_capture_id TEXT,
            amount REAL NOT NULL,
            currency TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ORDER_CREATED',
            approval_url TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """)
        conn.commit()

def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def create_project(title, description, client_name, freelancer_name, total_amount, currency):
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO projects
            (title, description, client_name, freelancer_name, total_amount, currency, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (title, description, client_name, freelancer_name, total_amount, currency, now())
        )
        return cur.lastrowid

def list_projects():
    with connect() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM projects ORDER BY id DESC").fetchall()]

def get_project(project_id):
    with connect() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        return dict(row) if row else None

def add_milestone(project_id, title, requirements, amount, due_date):
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO milestones
            (project_id, title, requirements, amount, due_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (project_id, title, requirements, amount, due_date, now())
        )
        return cur.lastrowid

def list_milestones(project_id):
    with connect() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM milestones WHERE project_id=? ORDER BY id", (project_id,)
        ).fetchall()]

def get_milestone(milestone_id):
    with connect() as conn:
        row = conn.execute("SELECT * FROM milestones WHERE id=?", (milestone_id,)).fetchone()
        return dict(row) if row else None

def add_submission(milestone_id, evidence_text):
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO submissions (milestone_id, evidence_text, created_at) VALUES (?, ?, ?)",
            (milestone_id, evidence_text, now())
        )
        return cur.lastrowid

def list_submissions(milestone_id):
    with connect() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM submissions WHERE milestone_id=? ORDER BY id DESC", (milestone_id,)
        ).fetchall()]

def save_verification(submission_id, result):
    with connect() as conn:
        conn.execute(
            """INSERT INTO ai_verifications
            (submission_id, completed_requirements, missing_requirements, confidence,
             recommendation, explanation, mode, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                submission_id,
                json.dumps(result.get("completed_requirements", [])),
                json.dumps(result.get("missing_requirements", [])),
                float(result.get("confidence", 0)),
                result.get("recommendation", "REQUEST_MORE_EVIDENCE"),
                result.get("explanation", ""),
                result.get("mode", "LLM"),
                now()
            )
        )
        conn.commit()

def get_latest_verification(submission_id):
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM ai_verifications WHERE submission_id=? ORDER BY id DESC LIMIT 1",
            (submission_id,)
        ).fetchone()
        if not row:
            return None
        result = dict(row)
        result["completed_requirements"] = json.loads(result["completed_requirements"])
        result["missing_requirements"] = json.loads(result["missing_requirements"])
        return result

def update_milestone_status(milestone_id, status):
    with connect() as conn:
        conn.execute("UPDATE milestones SET status=? WHERE id=?", (status, milestone_id))
        conn.commit()

def create_payment_record(milestone_id, order_id, amount, currency):
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO payments
            (milestone_id, paypal_order_id, amount, currency, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'ORDER_CREATED', ?, ?)""",
            (milestone_id, order_id, amount, currency, now(), now())
        )
        return cur.lastrowid

def update_payment_order(payment_id, order_id, status, approval_url=None):
    with connect() as conn:
        conn.execute(
            """UPDATE payments SET paypal_order_id=?, status=?, approval_url=?, updated_at=?
            WHERE id=?""",
            (order_id, status, approval_url, now(), payment_id)
        )
        conn.commit()

def update_payment_capture(payment_id, capture_id, status):
    with connect() as conn:
        conn.execute(
            """UPDATE payments SET paypal_capture_id=?, status=?, updated_at=? WHERE id=?""",
            (capture_id, status, now(), payment_id)
        )
        conn.commit()

def list_payments():
    with connect() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM payments ORDER BY id DESC").fetchall()]

def get_payment_by_id(payment_id):
    with connect() as conn:
        row = conn.execute("SELECT * FROM payments WHERE id=?", (payment_id,)).fetchone()
        return dict(row) if row else None

def add_activity(project_id, message):
    with connect() as conn:
        conn.execute(
            "INSERT INTO activity (project_id, message, created_at) VALUES (?, ?, ?)",
            (project_id, message, now())
        )
        conn.commit()

def get_activity(limit=10):
    with connect() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM activity ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()]
