import os
import sys
import ctypes
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from datetime import datetime, timedelta
from tkcalendar import Calendar, DateEntry # Import DateEntry as well if you ever need a date picker

import blocker_core as bc
from timer_logic import FocusTimer
import tracker_core as tc

def is_admin():
    if os.name == 'nt':
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    else:
        return os.geteuid() == 0

class BlockerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Focus Mode Website Blocker")
        self.root.geometry("450x650")
        self.root.resizable(False, False)
        self.root.configure(bg="#F0F0F0")

        self.style = ttk.Style()
        self.style.theme_use('clam')

        # --- Top Status and Title Frame ---
        top_frame = tk.Frame(self.root, bg="#E0E0E0", bd=2, relief=tk.RAISED)
        top_frame.pack(pady=(20, 10), padx=20, fill=tk.X)

        tk.Label(top_frame, text="✨ Focus Mode App ✨", font=("Arial", 20, "bold"), bg="#E0E0E0", fg="#333333").pack(pady=10)
        self.status_label = tk.Label(top_frame, text="Status: Inactive", fg="red", font=("Arial", 14, "bold"), bg="#E0E0E0")
        self.status_label.pack(pady=(0, 10))

        # --- Timer Input Frame ---
        timer_input_frame = tk.Frame(self.root, bg="#F8F8F8", bd=1, relief=tk.GROOVE)
        timer_input_frame.pack(pady=10, padx=20, fill=tk.X)

        tk.Label(timer_input_frame, text="Set Focus Duration (minutes):", font=("Arial", 12), bg="#F8F8F8").pack(pady=(10, 5))

        self.timer_entry = tk.Entry(timer_input_frame, width=8, font=("Arial", 16), justify='center', bd=2, relief=tk.SUNKEN)
        self.timer_entry.insert(0, "25")
        self.timer_entry.pack(pady=(0, 10))

        self.countdown_label = tk.Label(self.root, text="Ready to focus!", font=("Arial", 18, "bold"), fg="#4CAF50", bg="#F0F0F0")
        self.countdown_label.pack(pady=15)

        self.focus_timer = None
        self.timer_running = False
        self.session_start_time = None

        # --- Control Buttons Frame ---
        button_frame = tk.Frame(self.root, bg="#F0F0F0")
        button_frame.pack(pady=10, padx=20, fill=tk.X)

        self.style.configure('TButton', font=('Arial', 12), padding=10)
        self.style.map('TButton', background=[('active', '#D0D0D0')])

        ttk.Button(button_frame, text="🚀 Start Focus Mode", command=self.start_focus_with_timer, style='Green.TButton').pack(pady=7, fill=tk.X)
        self.style.configure('Green.TButton', background='green', foreground='white')
        self.style.map('Green.TButton', background=[('active', '#009900')])

        ttk.Button(button_frame, text="🛑 Stop Focus Mode", command=self.stop_focus, style='Red.TButton').pack(pady=7, fill=tk.X)
        self.style.configure('Red.TButton', background='gray', foreground='white')
        self.style.map('Red.TButton', background=[('active', '#A0A0A0')])

        ttk.Button(button_frame, text="📝 Edit Whitelist", command=self.edit_whitelist).pack(pady=7, fill=tk.X)
        ttk.Button(button_frame, text="📅 View Activity Calendar", command=self.view_activity_calendar).pack(pady=7, fill=tk.X)
        ttk.Button(button_frame, text="🚪 Exit App", command=self.root.quit).pack(pady=7, fill=tk.X)

        # --- Streak and Total Time Display ---
        self.streak_label = tk.Label(self.root, text="", font=("Arial", 12), bg="#F0F0F0", fg="#333333")
        self.streak_label.pack(pady=(10, 0))
        self.total_time_label = tk.Label(self.root, text="", font=("Arial", 12), bg="#F0F0F0", fg="#333333")
        self.total_time_label.pack(pady=(0, 10))
        
        self._update_activity_display()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        if messagebox.askokcancel("Exit Application", "Are you sure you want to exit? Ensure Focus Mode is stopped."):
            self.stop_focus()
            self.root.destroy()

    def _update_activity_display(self):
        current_streak, longest_streak = tc.get_streak_info()
        sessions, total_duration = tc.get_session_history()
        
        self.streak_label.config(text=f"🔥 Current Streak: {current_streak} days (Longest: {longest_streak} days)")
        self.total_time_label.config(text=f"⏱️ Total Focus Time: {total_duration:.1f} minutes")


    def start_focus(self):
        bc.block_all_except_whitelist()
        bc.start_focus_server()
        self.status_label.config(text="Status: Focus Mode ON", fg="green")
        self.session_start_time = datetime.now()

    def stop_focus(self):
        if self.focus_timer and self.focus_timer.running:
            self.focus_timer.stop_timer()
            self.timer_running = False
        
        bc.unblock_all()
        bc.stop_focus_server()
        self.status_label.config(text="Status: Inactive", fg="red")
        self.countdown_label.config(text="Ready to focus!")

        if self.session_start_time:
            session_end_time = datetime.now()
            if (session_end_time - self.session_start_time).total_seconds() >= 60:
                tc.record_session(self.session_start_time, session_end_time)
                tc.update_streak()
            self.session_start_time = None

        self._update_activity_display()
        messagebox.showinfo("Focus Mode", "Focus Mode ended. All sites are unblocked.")


    def edit_whitelist(self):
        editor = tk.Toplevel(self.root)
        editor.title("Edit Whitelist")
        editor.geometry("400x350")
        editor.transient(self.root)
        editor.grab_set()
        editor.focus_set()

        editor.configure(bg="#F0F0F0")

        tk.Label(editor, text="Edit Whitelisted Sites (one per line):", font=("Arial", 12, "bold"), bg="#F0F0F0").pack(pady=10)

        whitelist = bc.load_whitelist()
        text_area = scrolledtext.ScrolledText(editor, wrap=tk.WORD, width=40, height=10, font=("Arial", 10), bd=2, relief=tk.SUNKEN)
        text_area.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        text_area.insert(tk.END, "\n".join(whitelist))

        def save():
            sites = {line.strip() for line in text_area.get("1.0", tk.END).splitlines() if line.strip()}
            bc.save_whitelist(sites)
            editor.destroy()
            messagebox.showinfo("Saved", "Whitelist updated successfully!")

        ttk.Button(editor, text="Save Whitelist", command=save, style='TButton').pack(pady=10)
    
    def start_focus_with_timer(self):
        if self.timer_running:
            messagebox.showwarning("Timer Running", "A focus session is already active. Please stop the current session first.")
            return

        try:
            minutes = int(self.timer_entry.get())
            if minutes <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number of minutes (greater than 0).")
            return

        self.start_focus()

        self.focus_timer = FocusTimer(minutes, self._update_countdown_display, self._on_timer_complete)
        self.focus_timer.start_timer()
        self.timer_running = True
        self.countdown_label.config(fg="#0000FF")


    def _update_countdown_display(self, mins, secs):
        self.root.after(0, lambda: self.countdown_label.config(text=f"⏳ Time Left: {mins:02}:{secs:02}"))

    def _on_timer_complete(self):
        self.root.after(0, lambda: self.countdown_label.config(text="✅ Time's up!", fg="#4CAF50"))
        self.root.after(1000, self.stop_focus)

    def view_activity_calendar(self):
        calendar_viewer = tk.Toplevel(self.root)
        calendar_viewer.title("Focus Activity Calendar")
        calendar_viewer.geometry("600x550")
        calendar_viewer.transient(self.root)
        calendar_viewer.grab_set()
        calendar_viewer.focus_set()
        calendar_viewer.configure(bg="#F0F0F0")

        tk.Label(calendar_viewer, text="Your Focus History", font=("Arial", 16, "bold"), bg="#F0F0F0").pack(pady=10)

        sessions, _ = tc.get_session_history()
        
        # Dictionary to store total duration for each day
        daily_durations = {}
        # List to store datetime.date objects for highlighting
        dates_to_highlight = [] 

        for s in sessions:
            # Parse the ISO format string back to a datetime object
            session_start_dt = datetime.fromisoformat(s['start'])
            session_date = session_start_dt.date() # Get just the date part
            
            daily_durations[session_date] = daily_durations.get(session_date, 0) + s['duration_minutes']
            dates_to_highlight.append(session_date) # Add to list for highlighting

        # Calendar widget
        # Pass the list of dates to highlight during initialization
        self.cal = Calendar(calendar_viewer, selectmode='day',
                           font="Arial 10",
                           background="white", foreground="black",
                           normalbackground="white", normalforeground="black",
                           headersbackground="#4CAF50", headersforeground="white",
                           selectbackground="#FFC107", selectforeground="black",
                           weekendbackground="#F5F5DC", weekendforeground="black",
                           othermonthbackground="#E0E0E0", othermonthforeground="gray",
                           bordercolor="#B0B0B0",
                           locale='en_US',
                           cursor="hand1",
                           # Explicitly pass dates to be highlighted
                           # The tags parameter expects a dictionary: {'tag_name': [list_of_dates]}
                           # We create a single tag 'focus_day' for all our dates
                           tags={'focus_day': dates_to_highlight}) 
        self.cal.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Configure the appearance of the 'focus_day' tag
        self.cal.tag_config('focus_day', background='lightblue', foreground='blue') 

        # Label to display daily summary
        self.daily_summary_label = tk.Label(calendar_viewer, text="Click on a date to see daily summary.",
                                             font=("Arial", 12), bg="#F0F0F0")
        self.daily_summary_label.pack(pady=10)

        # Function to update daily summary when a date is selected
        def on_date_select(event):
            selected_date_str = self.cal.get_date()
            # Convert selected_date_str (e.g., 'MM/DD/YY') to a datetime.date object
            selected_date = datetime.strptime(selected_date_str, '%m/%d/%y').date()

            total_for_day = daily_durations.get(selected_date, 0)
            
            if total_for_day > 0:
                self.daily_summary_label.config(text=f"Focus Time on {selected_date.strftime('%Y-%m-%d')}: {total_for_day:.1f} minutes")
            else:
                self.daily_summary_label.config(text=f"No focus sessions on {selected_date.strftime('%Y-%m-%d')}.")
        
        self.cal.bind("<<CalendarSelected>>", on_date_select)

        # Display current streak and total time at the bottom of the calendar window too
        current_streak, longest_streak = tc.get_streak_info()
        _, total_duration_all = tc.get_session_history()
        
        tk.Label(calendar_viewer, text=f"Current Streak: {current_streak} days | Longest Streak: {longest_streak} days",
                 font=("Arial", 10, "bold"), bg="#F0F0F0").pack(pady=(0, 5))
        tk.Label(calendar_viewer, text=f"Overall Focus Time: {total_duration_all:.1f} minutes",
                 font=("Arial", 10, "bold"), bg="#F0F0F0").pack(pady=(0, 10))

        ttk.Button(calendar_viewer, text="Close", command=calendar_viewer.destroy, style='TButton').pack(pady=5)


if __name__ == "__main__":
    if not is_admin():
        print("❌ Please run this script as administrator.")
        messagebox.showerror("Permission Error", "Run this script as Administrator.")
        sys.exit(1)

    root = tk.Tk()
    app = BlockerGUI(root)
    root.mainloop()