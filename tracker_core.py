import json
import os
from datetime import datetime, timedelta

TRACKING_FILE = "focus_sessions.json"

def load_tracking_data():
    """Loads focus session data from the JSON file."""
    if not os.path.exists(TRACKING_FILE):
        return {"sessions": [], "last_session_date": None, "current_streak": 0, "longest_streak": 0, "session_dates": set()}
    try:
        with open(TRACKING_FILE, "r") as f:
            data = json.load(f)
            # Ensure all keys exist, for backward compatibility
            data.setdefault("sessions", [])
            data.setdefault("last_session_date", None)
            data.setdefault("current_streak", 0)
            data.setdefault("longest_streak", 0)
            data.setdefault("session_dates", set())  # Add session_dates
            return data
    except json.JSONDecodeError:
        # Handle corrupted or empty JSON file
        return {"sessions": [], "last_session_date": None, "current_streak": 0, "longest_streak": 0, "session_dates": set()}

def save_tracking_data(data):
    """Saves focus session data to the JSON file."""
    with open(TRACKING_FILE, "w") as f:
        json.dump(data, f, indent=4)

def record_session(start_time, end_time):
    """Records a completed focus session."""
    data = load_tracking_data()
    duration_seconds = int((end_time - start_time).total_seconds())

    session_info = {
        "start": start_time.isoformat(),
        "end": end_time.isoformat(),
        "duration_minutes": round(duration_seconds / 60, 2)
    }
    data["sessions"].append(session_info)
    session_date = start_time.date().isoformat()
    data["session_dates"].add(session_date)  # Add session date
    save_tracking_data(data)

def update_streak():
    """Calculates and updates the current and longest streaks."""
    data = load_tracking_data()
    today = datetime.now().date()
    session_dates = {datetime.fromisoformat(d).date() for d in data["session_dates"]}

    # Calculate current streak
    current_streak = 0
    check_date = today
    while check_date in session_dates:
        current_streak += 1
        check_date -= timedelta(days=1)
    data["current_streak"] = current_streak

    # Update longest streak
    data["longest_streak"] = max(data["longest_streak"], current_streak)
    save_tracking_data(data)
    return data["current_streak"], data["longest_streak"]

def get_session_history():
    """Returns a list of past session durations and total duration."""
    data = load_tracking_data()
    total_duration_minutes = sum(s["duration_minutes"] for s in data["sessions"])
    return data["sessions"], total_duration_minutes

def get_streak_info():
    """Returns the current and longest streaks."""
    data = load_tracking_data()
    return data.get("current_streak", 0), data.get("longest_streak", 0)

# Example usage (for testing)
if __name__ == "__main__":
    print("--- Initial State ---")
    data = load_tracking_data()
    print(data)

    print("\n--- Simulating sessions on 2025-05-19, 2025-05-20, and today (2025-05-21) ---")
    dates = [datetime(2025, 5, 19), datetime(2025, 5, 20), datetime.now()]
    for d in dates:
        start = d - timedelta(minutes=25)
        end = d
        record_session(start, end)
        print(f"Recorded session on {d.date()}")

    current_s, longest_s = update_streak()
    print(f"Current Streak: {current_s}, Longest Streak: {longest_s}")

    print("\n--- Simulating a gap and a new session today ---")
    # Simulate a gap
    data = load_tracking_data()
    data["session_dates"].clear()
    save_tracking_data(data)

    start = datetime.now() - timedelta(minutes=25)
    end = datetime.now()
    record_session(start, end)
    current_s, longest_s = update_streak()
    print(f"Current Streak after gap: {current_s}, Longest Streak: {longest_s}")

    print("\n--- Current Streak Info ---")
    current_s, longest_s = get_streak_info()
    print(f"Final Current Streak: {current_s}, Longest Streak: {longest_s}")

    print("\n--- Session History ---")
    sessions, total_duration = get_session_history()
    for s in sessions:
        print(f" Start: {s['start']}, End: {s['end']}, Duration: {s['duration_minutes']} mins")
    print(f"Total focus time: {total_duration} minutes")