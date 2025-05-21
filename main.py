import os
import sys
import ctypes
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from datetime import datetime, timedelta
from tkcalendar import Calendar, DateEntry # Import DateEntry as well

# Assuming blocker_core.py is bc and tracker_core.py is tc
import blocker_core as bc # Now handles blocklist via SQLite
from timer_logic import FocusTimer # Your existing timer logic
import tracker_core as tc # Your existing time tracking logic via SQLite

def is_admin():
    """Checks if the script is running with administrator privileges."""
    if os.name == 'nt':
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    else:
        # On Linux/macOS, check if effective UID is 0 (root)
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

        # Updated label to indicate seconds
        tk.Label(timer_input_frame, text="Set Focus Duration (Minutes):", font=("Arial", 12), bg="#F8F8F8").pack(pady=(10, 5))

        self.timer_entry = tk.Entry(timer_input_frame, width=8, font=("Arial", 16), justify='center', bd=2, relief=tk.SUNKEN)
        self.timer_entry.insert(0, "25") # Default to 25 minutes in seconds
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

        # Changed button text and command
        ttk.Button(button_frame, text="🚫 Edit Blocklist", command=self.edit_blocklist).pack(pady=7, fill=tk.X)
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
        """Handles graceful shutdown when the window is closed."""
        if messagebox.askokcancel("Exit Application", "Are you sure you want to exit? Ensure Focus Mode is stopped."):
            self.stop_focus()
            self.root.destroy()

    def _update_activity_display(self):
        """Updates the streak and total focus time labels."""
        current_streak, longest_streak = tc.get_streak_info()
        sessions, total_duration = tc.get_session_history()
        
        self.streak_label.config(text=f"🔥 Current Streak: {current_streak} days (Longest: {longest_streak} days)")
        self.total_time_label.config(text=f"⏱️ Total Focus Time: {total_duration:.1f} minutes")

    def start_focus(self):
        """Starts the focus mode by blocking sites and starting the HTTP server."""
        try:
            bc.block_sites() # Call the new block_sites function
            bc.start_focus_server()
            self.status_label.config(text="Status: Focus Mode ON", fg="green")
            self.session_start_time = datetime.now()
        except PermissionError:
            messagebox.showerror("Permission Error", "Admin rights required to modify the hosts file. Please restart as Administrator.")
            self.stop_focus() # Ensure everything is reset if we can't block
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while starting Focus Mode: {e}")
            self.stop_focus()


    def stop_focus(self):
        """Stops the focus mode, unblocks sites, and records the session."""
        # Check if there was a timer associated with this session
        if self.focus_timer:
            # If the FocusTimer object reports it's running (e.g., manual stop)
            if self.focus_timer.running:
                self.focus_timer.stop_timer() # Tell the timer object to stop

        # Crucially, reset the GUI's timer_running flag.
        # This indicates that, from the GUI's perspective, no timed session is active.
        self.timer_running = False

        try:
            bc.unblock_all()
            bc.stop_focus_server()
            self.status_label.config(text="Status: Inactive", fg="red")
            self.countdown_label.config(text="Ready to focus!")

            if self.session_start_time:
                session_end_time = datetime.now()
                # Record session only if it was at least 1 second long
                if (session_end_time - self.session_start_time).total_seconds() >= 1:
                    tc.record_session(self.session_start_time, session_end_time)
                    tc.update_streak()
                self.session_start_time = None

            self._update_activity_display()
            messagebox.showinfo("Focus Mode", "Focus Mode ended. All sites are unblocked.")
        except PermissionError:
            messagebox.showwarning("Permission Warning", "Admin rights required to unblock sites. Please manually check your hosts file.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while stopping Focus Mode: {e}")


    def edit_blocklist(self):
        """Opens a new window to edit the list of blocked websites."""
        editor = tk.Toplevel(self.root)
        editor.title("Edit Blocked Websites")
        editor.geometry("450x450")
        editor.transient(self.root)
        editor.grab_set()
        editor.focus_set()
        editor.configure(bg="#F0F0F0")

        tk.Label(editor, text="Blocked Sites (one per line):", font=("Arial", 12, "bold"), bg="#F0F0F0").pack(pady=10)

        # Frame for input and buttons
        input_frame = tk.Frame(editor, bg="#F0F0F0")
        input_frame.pack(pady=5, padx=10, fill=tk.X)

        tk.Label(input_frame, text="Add New Site:", font=("Arial", 10), bg="#F0F0F0").pack(side=tk.LEFT, padx=(0, 5))
        new_site_entry = tk.Entry(input_frame, width=30, font=("Arial", 10), bd=2, relief=tk.SUNKEN)
        new_site_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

        # Listbox to display blocked sites
        list_frame = tk.Frame(editor, bg="#F0F0F0")
        list_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        blocklist_listbox = tk.Listbox(list_frame, height=10, font=("Arial", 10), bd=2, relief=tk.SUNKEN)
        blocklist_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=blocklist_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        blocklist_listbox.config(yscrollcommand=scrollbar.set)

        def populate_blocklist_listbox():
            """Helper function to refresh the content of the blocklist_listbox."""
            blocklist_listbox.delete(0, tk.END)
            current_blocklist = sorted(list(bc.get_blocklist())) # Sort for consistent display
            for site in current_blocklist:
                blocklist_listbox.insert(tk.END, site)

        def add_site():
            site = new_site_entry.get().strip().lower()
            if site:
                if bc.add_to_blocklist(site):
                    messagebox.showinfo("Success", f"'{site}' added to blocklist.")
                    populate_blocklist_listbox() # Corrected call here
                    new_site_entry.delete(0, tk.END)
                else:
                    messagebox.showwarning("Duplicate", f"'{site}' is already in the blocklist.")
            else:
                messagebox.showwarning("Input Error", "Please enter a site to add.")

        ttk.Button(input_frame, text="Add", command=add_site, style='TButton').pack(side=tk.LEFT, padx=5)

        def remove_selected_site():
            selected_indices = blocklist_listbox.curselection()
            if not selected_indices:
                messagebox.showwarning("No Selection", "Please select a site to remove.")
                return

            selected_site = blocklist_listbox.get(selected_indices[0]) 
            
            if messagebox.askyesno("Confirm Removal", f"Are you sure you want to remove '{selected_site}' from the blocklist?"):
                bc.remove_from_blocklist(selected_site)
                messagebox.showinfo("Success", f"'{selected_site}' removed from blocklist.")
                populate_blocklist_listbox() # Refresh the listbox

        ttk.Button(editor, text="Remove Selected", command=remove_selected_site, style='Red.TButton').pack(pady=(5, 10))
        
        # Initial population of the listbox when the editor opens
        populate_blocklist_listbox()

        ttk.Button(editor, text="Close", command=editor.destroy, style='TButton').pack(pady=(0, 10))

    def start_focus_with_timer(self):
        """Starts the focus timer and initiates focus mode."""
        if self.timer_running:
            messagebox.showwarning("Timer Running", "A focus session is already active. Please stop the current session first.")
            return

        try:
            total_seconds = int(self.timer_entry.get()) # Get input in seconds
            if total_seconds <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number of seconds (greater than 0).")
            return

        self.start_focus()

        self.focus_timer = FocusTimer(total_seconds, self._update_countdown_display, self._on_timer_complete)
        self.focus_timer.start_timer()
        self.timer_running = True
        self.countdown_label.config(fg="#0000FF")

    def _update_countdown_display(self, mins, secs):
        """Updates the countdown label in the GUI."""
        self.root.after(0, lambda: self.countdown_label.config(text=f"⏳ Time Left: {mins:02}:{secs:02}"))

    def _on_timer_complete(self):
        """Callback function when the focus timer finishes."""
        self.root.after(0, lambda: self.countdown_label.config(text="✅ Time's up!", fg="#4CAF50"))
        self.root.after(1000, self.stop_focus) # Stop focus mode after 1 second

    def view_activity_calendar(self):
        """Opens a new window to display the focus activity calendar."""
        calendar_viewer = tk.Toplevel(self.root)
        calendar_viewer.title("Focus Activity Calendar")
        calendar_viewer.geometry("600x550")
        calendar_viewer.transient(self.root)
        calendar_viewer.grab_set()
        calendar_viewer.focus_set()
        calendar_viewer.configure(bg="#F0F0F0")

        tk.Label(calendar_viewer, text="Your Focus History", font=("Arial", 16, "bold"), bg="#F0F0F0").pack(pady=10)

        sessions, _ = tc.get_session_history()
        
        daily_durations = {}
        dates_to_highlight = [] 

        for s in sessions:
            session_start_dt = datetime.fromisoformat(s['start'])
            session_date = session_start_dt.date()
            
            daily_durations[session_date] = daily_durations.get(session_date, 0) + s['duration_minutes']
            # Only add to highlight list if it's not already there to avoid duplicates for display
            if session_date not in dates_to_highlight:
                dates_to_highlight.append(session_date) 

        self.cal = Calendar(calendar_viewer, selectmode='day',
                            font="Arial 10",
                            background="white", foreground="black",
                            normalbackground="white", normalforeground="black",
                            headersbackground="#4CAF50", headersforeground="white",
                            selectbackground="#FFC107", selectforeground="black",
                            weekendbackground="#F5F5DC", weekendforeground="black",
                            othermonthbackground="#E0E0E0", othermonthforeground="gray",
                            bordercolor="#B0B0B0",
                            locale='en_US', # Ensure locale is set for calendar display
                            cursor="hand1",
                            # Pass dates to be highlighted
                            # The tags parameter expects a dictionary: {'tag_name': [list_of_dates]}
                            tags={'focus_day': dates_to_highlight}) 
        self.cal.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # Configure the appearance of the 'focus_day' tag
        self.cal.tag_config('focus_day', background='lightblue', foreground='blue') 

        self.daily_summary_label = tk.Label(calendar_viewer, text="Click on a date to see daily summary.",
                                             font=("Arial", 12), bg="#F0F0F0")
        self.daily_summary_label.pack(pady=10)

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
        messagebox.showerror("Permission Error", "This application requires administrator privileges to modify your system's hosts file. Please run as Administrator.")
        sys.exit(1)

    # Initialize the databases when the application starts
    # This ensures tables are created/connected before any other DB operations
    tc.init_db()
    bc.init_db()

    root = tk.Tk()
    app = BlockerGUI(root)
    root.mainloop()