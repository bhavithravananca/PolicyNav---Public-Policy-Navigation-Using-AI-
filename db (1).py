import os
import sqlite3
import json

DB_NAME = os.path.join(os.environ.get('APP_DIR', '.'), "policynav_users.db")

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        password_hash TEXT,
        security_question TEXT,
        security_answer_hash TEXT,
        failed_attempts INTEGER DEFAULT 0,
        lock_until TEXT,
        password_history TEXT,
        avatar_path TEXT,
        is_admin INTEGER DEFAULT 0,
        is_online INTEGER DEFAULT 0,
        last_seen TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deleted_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        deleted_at TEXT DEFAULT CURRENT_TIMESTAMP,
        deleted_by TEXT DEFAULT 'admin'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pending_registrations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT UNIQUE,
        password_hash TEXT,
        security_question TEXT,
        security_answer_hash TEXT,
        requested_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        app_section TEXT,
        user_input TEXT,
        ai_output TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        section TEXT,
        rating INTEGER,
        comments TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("PRAGMA table_info(users)")
    cols = [col[1] for col in cursor.fetchall()]
    for col, defval in [("avatar_path","TEXT"), ("is_admin","INTEGER DEFAULT 0"),
                        ("is_online","INTEGER DEFAULT 0"), ("last_seen","TEXT")]:
        if col not in cols:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {defval}")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deadlines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        doc_name TEXT,
        deadline_text TEXT,
        deadline_date TEXT,
        context TEXT,
        is_done INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_points (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email      TEXT UNIQUE,
        total_points    INTEGER DEFAULT 0,
        login_streak    INTEGER DEFAULT 0,
        last_login_date TEXT,
        badges          TEXT DEFAULT '[]'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS points_log (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        action     TEXT,
        points     INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("PRAGMA table_info(user_points)")
    up_cols = [c[1] for c in cursor.fetchall()]
    for col, defval in [("login_streak","INTEGER DEFAULT 0"),
                        ("last_login_date","TEXT"),
                        ("badges","TEXT DEFAULT '[]'")]:
        if col not in up_cols:
            cursor.execute(f"ALTER TABLE user_points ADD COLUMN {col} {defval}")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS broadcasts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Add the tracker column to users if it doesn't exist
    cursor.execute("PRAGMA table_info(users)")
    cols = [col[1] for col in cursor.fetchall()]
    if "last_seen_broadcast_id" not in cols:
        cursor.execute("ALTER TABLE users ADD COLUMN last_seen_broadcast_id INTEGER DEFAULT 0")


    conn.commit()
    conn.close()

def create_user(username, email, password_hash, question, answer_hash):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        history = json.dumps([password_hash])
        cursor.execute("""
        INSERT INTO users (username, email, password_hash, security_question,
            security_answer_hash, password_history, avatar_path, is_admin)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (username, email, password_hash, question, answer_hash, history, None, 0))
        conn.commit()
        return True, "User created"
    except:
        return False, "User exists"
    finally:
        conn.close()

def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_login_attempts(email, attempts, lock_until=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET failed_attempts=?, lock_until=? WHERE email=?",
                   (attempts, lock_until, email))
    conn.commit()
    conn.close()

def update_password(email, new_hash):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password_hash=? WHERE email=?", (new_hash, email))
    conn.commit()
    conn.close()

def update_password_history(email, history_json):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password_history=? WHERE email=?", (history_json, email))
    conn.commit()
    conn.close()

def update_avatar(email, avatar_path):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET avatar_path=? WHERE email=?", (avatar_path, email))
    conn.commit()
    conn.close()

def set_user_online(email, is_online: bool):
    from datetime import datetime
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_online=?, last_seen=? WHERE email=?",
                   (1 if is_online else 0, datetime.utcnow().isoformat(), email))
    conn.commit()
    conn.close()

def promote_user_to_admin(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_admin=1 WHERE email=?", (email,))
    conn.commit()
    conn.close()

def remove_admin_status(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_admin=0 WHERE email=?", (email,))
    conn.commit()
    conn.close()

def delete_user(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO deleted_accounts (email) VALUES (?)", (email,))
    cursor.execute("DELETE FROM users WHERE email=?", (email,))
    conn.commit()
    conn.close()

def is_deleted_account(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM deleted_accounts WHERE email=?", (email,))
    result = cursor.fetchone() is not None
    conn.close()
    return result

def add_pending_registration(username, email, password_hash, question, answer_hash):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT OR REPLACE INTO pending_registrations
            (username, email, password_hash, security_question, security_answer_hash)
        VALUES (?, ?, ?, ?, ?)
        """, (username, email, password_hash, question, answer_hash))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def get_pending_registrations():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pending_registrations ORDER BY requested_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def approve_pending_registration(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pending_registrations WHERE email=?", (email,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False, "Not found"
    _, username, email, pw_hash, sq, sa, _ = row
    history = json.dumps([pw_hash])
    try:
        cursor.execute("""
        INSERT INTO users (username, email, password_hash, security_question,
            security_answer_hash, password_history, avatar_path, is_admin)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (username, email, pw_hash, sq, sa, history, None, 0))
        cursor.execute("DELETE FROM pending_registrations WHERE email=?", (email,))
        cursor.execute("DELETE FROM deleted_accounts WHERE email=?", (email,))
        conn.commit()
        return True, "Approved"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def reject_pending_registration(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pending_registrations WHERE email=?", (email,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT username, email, failed_attempts, lock_until, avatar_path, is_admin,
               is_online, last_seen
        FROM users
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def submit_feedback(user_email, section, rating, comments):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO feedback (user_email, section, rating, comments) VALUES (?, ?, ?, ?)",
                   (user_email, section, rating, comments))
    conn.commit()
    conn.close()

def log_activity(user_email, section, user_input, ai_output):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO activity_log (user_email, app_section, user_input, ai_output) VALUES (?, ?, ?, ?)",
                   (user_email, section, user_input, ai_output))
    conn.commit()
    conn.close()

def get_user_activity(user_email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT app_section, user_input, ai_output, created_at
        FROM activity_log WHERE user_email=?
        ORDER BY created_at DESC
    """, (user_email,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_feedback():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_email, section, rating, comments, created_at FROM feedback ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_email(old_email, new_email):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET email=? WHERE email=?", (new_email, old_email))
        cursor.execute("UPDATE activity_log SET user_email=? WHERE user_email=?", (new_email, old_email))
        cursor.execute("UPDATE feedback SET user_email=? WHERE user_email=?", (new_email, old_email))
        conn.commit()
        return True, "Email updated"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def email_exists(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM users WHERE email=?", (email,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def get_all_activity_logs():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.user_email, a.app_section, a.user_input, a.ai_output, a.created_at,
               CASE WHEN d.email IS NOT NULL THEN 1 ELSE 0 END as is_deleted
        FROM activity_log a
        LEFT JOIN deleted_accounts d ON a.user_email = d.email
        ORDER BY a.created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def send_admin_action_email(to_email, message):
    pass

def save_deadline(user_email, doc_name, deadline_text, deadline_date, context):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO deadlines (user_email, doc_name, deadline_text, deadline_date, context)
        VALUES (?, ?, ?, ?, ?)
    """, (user_email, doc_name, deadline_text, deadline_date, context))
    conn.commit()
    conn.close()

def get_user_deadlines(user_email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, doc_name, deadline_text, deadline_date, context, is_done, created_at
        FROM deadlines WHERE user_email=?
        ORDER BY deadline_date ASC
    """, (user_email,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def toggle_deadline_done(deadline_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE deadlines SET is_done = CASE WHEN is_done=1 THEN 0 ELSE 1 END
        WHERE id=?
    """, (deadline_id,))
    conn.commit()
    conn.close()

def delete_deadline(deadline_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM deadlines WHERE id=?", (deadline_id,))
    conn.commit()
    conn.close()

POINTS_MAP = {
    "upload_doc":      10,
    "rag_question":    5,
    "summarize":       8,
    "readability":     4,
    "feedback":        3,
    "login_streak_7":  20,
    "login_streak_30": 50,
}

BADGES = [
    {"id":"first_reader",    "name":"First Reader",    "icon":"📖","desc":"Upload your first document",      "condition":("upload_doc",1)},
    {"id":"policy_detective","name":"Policy Detective","icon":"🔍","desc":"Ask 10 RAG questions",            "condition":("rag_question",10)},
    {"id":"summarizer",      "name":"Summarizer Pro",  "icon":"📝","desc":"Generate 5 summaries",            "condition":("summarize",5)},
    {"id":"streak_7",        "name":"7-Day Streak",    "icon":"🔥","desc":"Login 7 days in a row",           "condition":("streak",7)},
    {"id":"streak_30",       "name":"30-Day Streak",   "icon":"⚡","desc":"Login 30 days in a row",          "condition":("streak",30)},
    {"id":"power_user",      "name":"Power User",      "icon":"🌟","desc":"Earn 500 points",                 "condition":("points",500)},
    {"id":"civic_champion",  "name":"Civic Champion",  "icon":"🏛️","desc":"Earn 1000 points",                "condition":("points",1000)},
    {"id":"policy_scholar",  "name":"Policy Scholar",  "icon":"🎓","desc":"Earn 2000 points",                "condition":("points",2000)},
    {"id":"feedback_star",   "name":"Feedback Star",   "icon":"💬","desc":"Give feedback 5 times",           "condition":("feedback",5)},
    {"id":"readability_guru","name":"Readability Guru","icon":"📊","desc":"Run 10 readability analyses",     "condition":("readability",10)},
]

def _ensure_points_row(cursor, email):
    cursor.execute(
        "INSERT OR IGNORE INTO user_points (user_email, total_points) VALUES (?, 0)",
        (email,)
    )

def award_points(email, action):
    pts = POINTS_MAP.get(action, 0)
    if pts == 0:
        return 0
    conn = get_connection()
    cursor = conn.cursor()
    _ensure_points_row(cursor, email)
    cursor.execute(
        "UPDATE user_points SET total_points=total_points+? WHERE user_email=?",
        (pts, email)
    )
    cursor.execute(
        "INSERT INTO points_log (user_email,action,points) VALUES (?,?,?)",
        (email, action, pts)
    )
    conn.commit()
    conn.close()
    _check_and_award_badges(email)
    return pts

def update_login_streak(email):
    from datetime import datetime as _dt, timedelta as _td
    conn = get_connection()
    cursor = conn.cursor()
    _ensure_points_row(cursor, email)
    cursor.execute(
        "SELECT login_streak, last_login_date FROM user_points WHERE user_email=?",
        (email,)
    )
    row = cursor.fetchone()
    streak, last_date = (row[0] or 0), row[1]
    today     = _dt.utcnow().date().isoformat()
    yesterday = (_dt.utcnow().date() - _td(days=1)).isoformat()
    if last_date == today:
        conn.close()
        return streak
    new_streak = streak + 1 if last_date == yesterday else 1
    cursor.execute(
        "UPDATE user_points SET login_streak=?, last_login_date=? WHERE user_email=?",
        (new_streak, today, email)
    )
    if new_streak == 7:
        cursor.execute(
            "UPDATE user_points SET total_points=total_points+20 WHERE user_email=?",
            (email,)
        )
        cursor.execute(
            "INSERT INTO points_log (user_email,action,points) VALUES (?,?,?)",
            (email, "login_streak_7", 20)
        )
    elif new_streak == 30:
        cursor.execute(
            "UPDATE user_points SET total_points=total_points+50 WHERE user_email=?",
            (email,)
        )
        cursor.execute(
            "INSERT INTO points_log (user_email,action,points) VALUES (?,?,?)",
            (email, "login_streak_30", 50)
        )
    conn.commit()
    conn.close()
    _check_and_award_badges(email)
    return new_streak

def _check_and_award_badges(email):
    import json as _j
    conn = get_connection()
    cursor = conn.cursor()
    _ensure_points_row(cursor, email)
    cursor.execute(
        "SELECT total_points, login_streak, badges FROM user_points WHERE user_email=?",
        (email,)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return
    total_pts, streak, badges_json = row
    earned = set(_j.loads(badges_json or "[]"))
    cursor.execute(
        "SELECT action, COUNT(*) FROM points_log WHERE user_email=? GROUP BY action",
        (email,)
    )
    action_counts = dict(cursor.fetchall())
    new_badges = list(earned)
    for badge in BADGES:
        if badge["id"] in earned:
            continue
        ctype, cval = badge["condition"]
        if   ctype == "points"  and total_pts >= cval:                 new_badges.append(badge["id"])
        elif ctype == "streak"  and streak >= cval:                    new_badges.append(badge["id"])
        elif ctype in action_counts and action_counts[ctype] >= cval:  new_badges.append(badge["id"])
    if len(new_badges) != len(earned):
        cursor.execute(
            "UPDATE user_points SET badges=? WHERE user_email=?",
            (_j.dumps(new_badges), email)
        )
        conn.commit()
    conn.close()

def get_user_points_data(email):
    import json as _j
    conn = get_connection()
    cursor = conn.cursor()
    _ensure_points_row(cursor, email)
    cursor.execute(
        "SELECT total_points, login_streak, last_login_date, badges FROM user_points WHERE user_email=?",
        (email,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {"points": 0, "streak": 0, "badges": []}
    return {
        "points":     row[0] or 0,
        "streak":     row[1] or 0,
        "last_login": row[2],
        "badges":     _j.loads(row[3] or "[]")
    }

def get_leaderboard(limit=20):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.username, u.email, p.total_points, p.login_streak, p.badges
        FROM user_points p
        JOIN users u ON u.email = p.user_email
        WHERE p.total_points > 0
        ORDER BY p.total_points DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_points_history(email, limit=20):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT action, points, created_at FROM points_log WHERE user_email=? ORDER BY created_at DESC LIMIT ?",
        (email, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

def create_broadcast(title, description):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO broadcasts (title, description) VALUES (?, ?)", (title, description))
    conn.commit()
    conn.close()

def get_all_broadcasts():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, description, created_at FROM broadcasts ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_latest_broadcast():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, description, created_at FROM broadcasts ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row

def get_last_seen_broadcast(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT last_seen_broadcast_id FROM users WHERE email=?", (email,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row and row[0] else 0

def update_last_seen_broadcast(email, broadcast_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET last_seen_broadcast_id=? WHERE email=?", (broadcast_id, email))
    conn.commit()
    conn.close()