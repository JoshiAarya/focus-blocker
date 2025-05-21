import sqlite3
import os
from datetime import datetime, timedelta
from platformdirs import user_data_dir # Import the necessary function

# Define your application name and author (important for platformdirs)
APP_NAME = "FocusModeApp" # Replace with your actual app name
APP_AUTHOR = "JoshiAarya" # Replace with your name or company

# Dynamically determine the database file path
DATA_DIR = user_data_dir(appname=APP_NAME, appauthor=APP_AUTHOR)
# Ensure the directory exists
os.makedirs(DATA_DIR, exist_ok=True)
DB_FILE = os.path.join(DATA_DIR, "focus_data.db")

# --- Rest of your time_controller.py code (remains largely the same) ---

def init_db():
    """Initializes the SQLite database and creates tables if they don't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            duration_minutes REAL NOT NULL
        )
    ''')

    # Create streaks table (stores global streak info)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS streaks (
            id INTEGER PRIMARY KEY,
            current_streak INTEGER NOT NULL,
            longest_streak INTEGER NOT NULL,
            last_checked_date TEXT UNIQUE -- To manage daily updates
        )
    ''')

    # Create daily_sessions table (to track which dates had focus sessions for streak calculation)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_sessions (
            session_date TEXT UNIQUE NOT NULL -- Store dates like 'YYYY-MM-DD'
        )
    ''')

    # Initialize streak data if it doesn't exist
    cursor.execute("INSERT OR IGNORE INTO streaks (id, current_streak, longest_streak) VALUES (1, 0, 0)")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scheduled_focus_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scheduled_datetime TEXT NOT NULL,    -- ISO format: YYYY-MM-DDTHH:MM:SS
            duration_minutes INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending', -- e.g., 'pending', 'active', 'completed', 'missed', 'cancelled'
            notification_sent INTEGER DEFAULT 0, -- 0 for false, 1 for true
            notes TEXT,                          -- Optional user notes
            created_at TEXT NOT NULL             -- Timestamp when the schedule was created
        )
    ''')


    conn.commit()
    conn.close()

def add_scheduled_session(scheduled_datetime, duration_minutes, notes=""):
    """Adds a new scheduled focus session to the database."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    created_at_ts = datetime.now().isoformat()
    try:
        cursor.execute('''
            INSERT INTO scheduled_focus_sessions 
            (scheduled_datetime, duration_minutes, notes, created_at, status, notification_sent)
            VALUES (?, ?, ?, ?, 'pending', 0)
        ''', (scheduled_datetime.isoformat(), duration_minutes, notes, created_at_ts))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Database error adding scheduled session: {e}")
        return None
    finally:
        conn.close()

def get_scheduled_sessions(start_date=None, end_date=None, status_filter=None):
    """
    Retrieves scheduled sessions, optionally filtered by date range and status.
    Dates should be datetime.date objects.
    """
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    query = "SELECT id, scheduled_datetime, duration_minutes, status, notification_sent, notes FROM scheduled_focus_sessions"
    conditions = []
    params = []

    if start_date:
        conditions.append("scheduled_datetime >= ?")
        # Ensure we query from the beginning of the start_date
        params.append(datetime.combine(start_date, datetime.min.time()).isoformat())
    if end_date:
        conditions.append("scheduled_datetime <= ?")
        # Ensure we query up to the end of the end_date
        params.append(datetime.combine(end_date, datetime.max.time()).isoformat())
    if status_filter:
        conditions.append("status = ?")
        params.append(status_filter)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY scheduled_datetime ASC"
        
    cursor.execute(query, tuple(params))
    
    schedules = []
    for row in cursor.fetchall():
        schedules.append({
            "id": row[0],
            "scheduled_datetime": datetime.fromisoformat(row[1]),
            "duration_minutes": row[2],
            "status": row[3],
            "notification_sent": bool(row[4]),
            "notes": row[5]
        })
    conn.close()
    return schedules

def get_upcoming_pending_schedules():
    """Retrieves all 'pending' scheduled sessions from now onwards."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    now_iso = datetime.now().isoformat()
    cursor.execute('''
        SELECT id, scheduled_datetime, duration_minutes, status, notification_sent, notes 
        FROM scheduled_focus_sessions
        WHERE status = 'pending' AND scheduled_datetime >= ?
        ORDER BY scheduled_datetime ASC
    ''', (now_iso,))
    schedules = []
    for row in cursor.fetchall():
        schedules.append({
            "id": row[0],
            "scheduled_datetime": datetime.fromisoformat(row[1]),
            "duration_minutes": row[2],
            "status": row[3],
            "notification_sent": bool(row[4]),
            "notes": row[5]
        })
    conn.close()
    return schedules


def update_scheduled_session_status(session_id, new_status):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE scheduled_focus_sessions SET status = ? WHERE id = ?", (new_status, session_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error updating scheduled session status: {e}")
        return False
    finally:
        conn.close()

def update_scheduled_session_notification_sent(session_id, sent_status_bool):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    sent_status_int = 1 if sent_status_bool else 0
    try:
        cursor.execute("UPDATE scheduled_focus_sessions SET notification_sent = ? WHERE id = ?", (sent_status_int, session_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error updating notification status: {e}")
        return False
    finally:
        conn.close()


def delete_scheduled_session(session_id):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM scheduled_focus_sessions WHERE id = ?", (session_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error deleting scheduled session: {e}")
        return False
    finally:
        conn.close()


def record_session(start_time, end_time):
    """Records a completed focus session in the database."""
    init_db() # Ensure DB is initialized before any operation
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    duration_seconds = int((end_time - start_time).total_seconds())
    duration_minutes = round(duration_seconds / 60, 2)

    # Insert into sessions table
    cursor.execute('''
        INSERT INTO sessions (start_time, end_time, duration_minutes)
        VALUES (?, ?, ?)
    ''', (start_time.isoformat(), end_time.isoformat(), duration_minutes))

    # Insert or ignore into daily_sessions table for streak tracking
    session_date_str = start_time.date().isoformat()
    cursor.execute('''
        INSERT OR IGNORE INTO daily_sessions (session_date)
        VALUES (?)
    ''', (session_date_str,))

    conn.commit()
    conn.close()

def update_streak():
    """Calculates and updates the current and longest streaks in the database."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    today = datetime.now().date()
    today_str = today.isoformat()

    # Get all unique session dates from the daily_sessions table
    cursor.execute("SELECT session_date FROM daily_sessions ORDER BY session_date")
    session_dates_str = [row[0] for row in cursor.fetchall()]
    session_dates_dt = {datetime.fromisoformat(d).date() for d in session_dates_str}

    current_streak = 0
    # Check if a session occurred today
    if today in session_dates_dt:
        current_streak = 1 # Start streak with today
        check_date = today - timedelta(days=1)
        while check_date in session_dates_dt:
            current_streak += 1
            check_date -= timedelta(days=1)
    # else: current_streak remains 0 if no session today

    # Get the existing longest streak
    cursor.execute("SELECT longest_streak FROM streaks WHERE id = 1")
    longest_streak_row = cursor.fetchone()
    longest_streak = longest_streak_row[0] if longest_streak_row else 0

    # Update longest streak if current is greater
    longest_streak = max(longest_streak, current_streak)

    # Update the streaks table
    cursor.execute('''
        UPDATE streaks
        SET current_streak = ?, longest_streak = ?, last_checked_date = ?
        WHERE id = 1
    ''', (current_streak, longest_streak, today_str))

    conn.commit()
    conn.close()

    return current_streak, longest_streak

def get_session_history():
    """Returns a list of past session durations and total duration from the database."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT start_time, end_time, duration_minutes FROM sessions ORDER BY start_time DESC")
    rows = cursor.fetchall()

    sessions_list = []
    total_duration_minutes = 0.0

    for row in rows:
        start_time_str, end_time_str, duration_minutes = row
        sessions_list.append({
            "start": start_time_str,
            "end": end_time_str,
            "duration_minutes": duration_minutes
        })
        total_duration_minutes += duration_minutes

    conn.close()
    return sessions_list, total_duration_minutes

def get_streak_info():
    """Returns the current and longest streaks from the database."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT current_streak, longest_streak FROM streaks WHERE id = 1")
    streak_info = cursor.fetchone()
    conn.close()

    if streak_info:
        return streak_info[0], streak_info[1]
    return 0, 0 # Default if no streak info is found

# Example usage (for testing)
if __name__ == "__main__":
    # Clean up previous data for consistent testing
    # Note: This will delete data from the platform-specific data directory
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    if not os.path.exists(os.path.dirname(DB_FILE)):
        os.makedirs(os.path.dirname(DB_FILE))

    print(f"Database will be stored at: {DB_FILE}")

    print("--- Initializing DB and State ---")
    init_db()
    current_s, longest_s = get_streak_info()
    print(f"Initial Streak: Current={current_s}, Longest={longest_s}")
    sessions, total_duration = get_session_history()
    print(f"Initial Sessions: {len(sessions)}, Total Duration: {total_duration:.1f} mins")

    print("\n--- Simulating sessions for a streak: Day 1, Day 2, Day 3 (today) ---")
    two_days_ago = datetime.now() - timedelta(days=2)
    yesterday = datetime.now() - timedelta(days=1)
    today = datetime.now()

    record_session(two_days_ago - timedelta(minutes=25), two_days_ago)
    print(f"Recorded session on {two_days_ago.date()}")

    record_session(yesterday - timedelta(minutes=25), yesterday)
    print(f"Recorded session on {yesterday.date()}")

    record_session(today - timedelta(minutes=25), today)
    print(f"Recorded session on {today.date()}")

    current_s, longest_s = update_streak()
    print(f"Current Streak after 3 consecutive sessions: Current={current_s}, Longest={longest_s}")

    print("\n--- Simulating a broken streak (no session for a day, then a new session) ---")
    day_after_tomorrow = datetime.now() + timedelta(days=2)
    record_session(day_after_tomorrow - timedelta(minutes=25), day_after_tomorrow)
    print(f"Recorded session on {day_after_tomorrow.date()} (after a gap)")

    current_s, longest_s = update_streak()
    print(f"Current Streak after intentional gap: Current={current_s}, Longest={longest_s}")

    print("\n--- Testing Edge Case: No session today ---")
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    init_db()
    
    yesterday_test = datetime.now() - timedelta(days=1)
    record_session(yesterday_test - timedelta(minutes=25), yesterday_test)
    print(f"Recorded session on {yesterday_test.date()} (but not today)")
    
    current_s, longest_s = update_streak()
    print(f"Current Streak (no session today): Current={current_s}, Longest={longest_s}")

    print("\n--- Final Streak Info ---")
    current_s, longest_s = get_streak_info()
    print(f"Final Current Streak: Current={current_s}, Longest={longest_s}")

    print("\n--- Final Session History ---")
    sessions, total_duration = get_session_history()
    for s in sessions:
        print(f" Start: {s['start']}, End: {s['end']}, Duration: {s['duration_minutes']} mins")
    print(f"Total focus time: {total_duration:.1f} minutes")