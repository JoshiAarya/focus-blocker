import sqlite3
import os
from datetime import datetime, timedelta

DB_FILE = "focus_data.db"

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

    conn.commit()
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
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    print("--- Initializing DB and State ---")
    init_db()
    current_s, longest_s = get_streak_info()
    print(f"Initial Streak: Current={current_s}, Longest={longest_s}")
    sessions, total_duration = get_session_history()
    print(f"Initial Sessions: {len(sessions)}, Total Duration: {total_duration:.1f} mins")

    print("\n--- Simulating sessions for a streak: Day 1, Day 2, Day 3 (today) ---")
    # Simulate dates: two days ago, yesterday, and today
    two_days_ago = datetime.now() - timedelta(days=2)
    yesterday = datetime.now() - timedelta(days=1)
    today = datetime.now()

    # Record sessions for a continuous streak
    record_session(two_days_ago - timedelta(minutes=25), two_days_ago)
    print(f"Recorded session on {two_days_ago.date()}")

    record_session(yesterday - timedelta(minutes=25), yesterday)
    print(f"Recorded session on {yesterday.date()}")

    record_session(today - timedelta(minutes=25), today)
    print(f"Recorded session on {today.date()}")

    # Update and check streak after recording all sessions
    current_s, longest_s = update_streak()
    print(f"Current Streak after 3 consecutive sessions: Current={current_s}, Longest={longest_s}")

    print("\n--- Simulating a broken streak (no session for a day, then a new session) ---")
    # Simulate a day passing without a session
    # Then record a session two days from now
    day_after_tomorrow = datetime.now() + timedelta(days=2) # This will be after the gap
    record_session(day_after_tomorrow - timedelta(minutes=25), day_after_tomorrow)
    print(f"Recorded session on {day_after_tomorrow.date()} (after a gap)")

    # Update streak after the gap and new session
    current_s, longest_s = update_streak()
    print(f"Current Streak after intentional gap: Current={current_s}, Longest={longest_s}")

    print("\n--- Testing Edge Case: No session today ---")
    # Clean up data to ensure streak is tested from scratch
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    init_db() # Re-initialize DB
    
    # Record a session yesterday, but not today
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