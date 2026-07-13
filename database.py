import sqlite3
from datetime import datetime, timedelta, timezone

DB_PATH = "meeting.db"


def init_db():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS meeting_series(
        id INTEGER PRIMARY KEY,
        series_key TEXT UNIQUE,
        title TEXT,
        description TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS meeting_briefs(
        id INTEGER PRIMARY KEY,
        series_id INTEGER NOT NULL,
        meeting_start TEXT,
        summary TEXT,
        generated_at TEXT,
        FOREIGN KEY(series_id) REFERENCES meeting_series(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS action_items(
        id INTEGER PRIMARY KEY,
        series_id INTEGER,
        owner TEXT,
        task TEXT,
        due_date TEXT,
        status TEXT,
        source_note TEXT,
        created_at TEXT,
        FOREIGN KEY(series_id) REFERENCES meeting_series(id)
    )
    """)

    # Migrate legacy meeting_briefs with old schema
    cursor.execute("PRAGMA table_info(meeting_briefs)")
    brief_columns = [row[1] for row in cursor.fetchall()]
    if brief_columns and (
        'series_id' not in brief_columns
        or 'meeting_start' not in brief_columns
        or 'generated_at' not in brief_columns
    ):
        cursor.execute("ALTER TABLE meeting_briefs RENAME TO meeting_briefs_old")
        cursor.execute("""
        CREATE TABLE meeting_briefs(
            id INTEGER PRIMARY KEY,
            series_id INTEGER NOT NULL,
            meeting_start TEXT,
            summary TEXT,
            generated_at TEXT,
            FOREIGN KEY(series_id) REFERENCES meeting_series(id)
        )
        """)

        cursor.execute("SELECT id, title, summary FROM meeting_briefs_old")
        rows = cursor.fetchall()
        for row in rows:
            title = row[1]
            summary = row[2]
            cursor.execute(
                "INSERT OR IGNORE INTO meeting_series(series_key, title, description) VALUES (?, ?, ?)",
                (title, title, None)
            )
            cursor.execute(
                "SELECT id FROM meeting_series WHERE series_key = ?",
                (title,)
            )
            series_id = cursor.fetchone()[0]
            cursor.execute(
                "INSERT INTO meeting_briefs(series_id, meeting_start, summary, generated_at) VALUES (?, ?, ?, ?)",
                (series_id, None, summary, datetime.now(timezone.utc).isoformat())
            )
        cursor.execute("DROP TABLE meeting_briefs_old")

    # Migrate legacy action_items with old schema
    cursor.execute("PRAGMA table_info(action_items)")
    action_columns = [row[1] for row in cursor.fetchall()]
    if action_columns and (
        'series_id' not in action_columns
        or 'source_note' not in action_columns
        or 'created_at' not in action_columns
    ):
        cursor.execute("ALTER TABLE action_items RENAME TO action_items_old")
        cursor.execute("""
        CREATE TABLE action_items(
            id INTEGER PRIMARY KEY,
            series_id INTEGER,
            owner TEXT,
            task TEXT,
            due_date TEXT,
            status TEXT,
            source_note TEXT,
            created_at TEXT,
            FOREIGN KEY(series_id) REFERENCES meeting_series(id)
        )
        """)

        cursor.execute("SELECT id, owner, task, due_date, status FROM action_items_old")
        rows = cursor.fetchall()
        for row in rows:
            owner = row[1]
            task = row[2]
            due_date = row[3]
            status = row[4]
            cursor.execute(
                "INSERT INTO action_items(series_id, owner, task, due_date, status, source_note, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (None, owner, task, due_date, status, None, datetime.now(timezone.utc).isoformat())
            )
        cursor.execute("DROP TABLE action_items_old")

    conn.commit()
    conn.close()


def get_connection():

    return sqlite3.connect(DB_PATH)


def get_or_create_series(series_key, title, description=None):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM meeting_series WHERE series_key = ?",
        (series_key,)
    )

    row = cursor.fetchone()

    if row:
        series_id = row[0]
    else:
        cursor.execute(
            "INSERT INTO meeting_series(series_key, title, description) VALUES (?, ?, ?)",
            (series_key, title, description)
        )
        series_id = cursor.lastrowid
        conn.commit()

    conn.close()
    return series_id


def brief_exists(series_id, meeting_start):

    conn = get_connection()
    row = conn.execute(
        "SELECT 1 FROM meeting_briefs WHERE series_id = ? AND meeting_start = ?",
        (series_id, meeting_start)
    ).fetchone()
    conn.close()
    return bool(row)


def save_brief(series_id, meeting_start, summary):

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO meeting_briefs(
            series_id,
            meeting_start,
            summary,
            generated_at
        ) VALUES (?, ?, ?, ?)
        """,
        (
            series_id,
            meeting_start,
            summary,
            datetime.now(timezone.utc).isoformat()
        )
    )

    conn.commit()
    conn.close()


def save_action(owner, task, due_date, series_id=None, source_note=None):

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO action_items(
            series_id,
            owner,
            task,
            due_date,
            status,
            source_note,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            series_id,
            owner,
            task,
            due_date or "Unspecified",
            "Open",
            source_note,
            datetime.now(timezone.utc).isoformat()
        )
    )

    conn.commit()
    conn.close()


def note_processed(source_note):

    if not source_note:
        return False

    conn = get_connection()
    row = conn.execute(
        "SELECT 1 FROM action_items WHERE source_note = ? LIMIT 1",
        (source_note,)
    ).fetchone()
    conn.close()
    return bool(row)


def get_past_briefs(series_id, limit=4):

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT meeting_start, summary
        FROM meeting_briefs
        WHERE series_id = ?
        ORDER BY meeting_start DESC
        LIMIT ?
        """,
        (series_id, limit)
    ).fetchall()

    conn.close()

    return [
        {"meeting_start": row[0], "summary": row[1]}
        for row in rows
    ]


def get_open_actions():

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT ai.id,
               ai.owner,
               ai.task,
               ai.due_date,
               ai.status,
               ms.title AS meeting_series
        FROM action_items ai
        LEFT JOIN meeting_series ms
          ON ai.series_id = ms.id
        WHERE ai.status = 'Open'
        ORDER BY ai.due_date
        """
    ).fetchall()

    conn.close()

    return [
        {
            "id": row[0],
            "owner": row[1],
            "task": row[2],
            "due_date": row[3],
            "status": row[4],
            "meeting_series": row[5],
        }
        for row in rows
    ]


def get_upcoming_briefs(hours=24):

    now = datetime.now(timezone.utc)
    future = now + timedelta(hours=hours)
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT mb.id,
               ms.title,
               mb.meeting_start,
               mb.summary,
               mb.generated_at
        FROM meeting_briefs mb
        JOIN meeting_series ms
          ON mb.series_id = ms.id
        WHERE mb.meeting_start >= ?
          AND mb.meeting_start <= ?
        ORDER BY mb.meeting_start
        """,
        (now.isoformat(), future.isoformat())
    ).fetchall()

    conn.close()

    return [
        {
            "id": row[0],
            "series_title": row[1],
            "meeting_start": row[2],
            "summary": row[3],
            "generated_at": row[4],
        }
        for row in rows
    ]
