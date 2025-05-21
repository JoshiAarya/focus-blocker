import os
import sys
import ctypes
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, timedelta
from tkcalendar import Calendar, DateEntry

import blocker_core as bc
from timer_logic import FocusTimer
import tracker_core as tc

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

def is_admin():
    if os.name == 'nt':
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    else:
        return os.geteuid() == 0

class BlockerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("✨ Focus Mode App ✨")
        # self.geometry("480x700") # Remove fixed geometry for fullscreen

        # --- Fullscreen Setup ---
        self._is_fullscreen = True # Start in fullscreen mode
        self.attributes("-fullscreen", self._is_fullscreen)
        # Store an initial reasonable size for when exiting fullscreen
        self._initial_windowed_geometry = "1024x768" # Or your previous "480x700" if preferred

        # Bind Escape and F11 to toggle fullscreen
        self.bind("<Escape>", self.toggle_fullscreen)
        self.bind("<F11>", self.toggle_fullscreen)


        # --- Fonts (same as before) ---
        self.title_font = ctk.CTkFont(family="Arial", size=24, weight="bold")
        self.header_font = ctk.CTkFont(family="Arial", size=18, weight="bold")
        self.label_font = ctk.CTkFont(family="Arial", size=14)
        self.button_font = ctk.CTkFont(family="Arial", size=12, weight="bold")
        self.small_font = ctk.CTkFont(family="Arial", size=12)
        self.countdown_font = ctk.CTkFont(family="Arial", size=22, weight="bold")

        # --- Main Content Frame to help center content ---
        # This frame will hold all your other frames and can be centered.
        # For fullscreen, you might want this to expand or stay centered.
        # Let's try keeping it relatively centered for now.
        # To make it expand, you'd use fill=ctk.BOTH, expand=True on a parent or this.

        # For better fullscreen layout, let's put everything in a central column
        # that doesn't necessarily stretch to full screen width unless we want it to.
        # We'll use a main_container_frame that is packed to expand vertically
        # and then use an inner_content_frame to hold the actual UI elements
        # with a max width to prevent them from becoming too wide on large screens.

        self.main_container_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container_frame.pack(pady=20, padx=20, fill=ctk.BOTH, expand=True)

        # This inner frame will hold the UI elements and have a max width
        self.inner_content_frame = ctk.CTkFrame(self.main_container_frame, fg_color="transparent", width=460) # Adjust width as needed
        self.inner_content_frame.pack(pady=20, padx=20, expand=False) # Centered by default if container expands
        # To truly center it if main_container_frame expands fully:
        # self.main_container_frame.grid_rowconfigure(0, weight=1)
        # self.main_container_frame.grid_columnconfigure(0, weight=1)
        # self.inner_content_frame.grid(row=0, column=0, sticky="")


        # --- Top Status and Title Frame ---
        top_frame = ctk.CTkFrame(self.inner_content_frame, corner_radius=10)
        top_frame.pack(pady=(0, 10), padx=0, fill=ctk.X) # padx=0 as inner_content_frame has padding

        ctk.CTkLabel(top_frame, text="✨ Focus Mode App ✨", font=self.title_font).pack(pady=10)
        self.status_label = ctk.CTkLabel(top_frame, text="Status: Inactive", font=self.header_font, text_color="red")
        self.status_label.pack(pady=(0, 10))

        # --- Timer Input Frame ---
        timer_input_frame = ctk.CTkFrame(self.inner_content_frame, corner_radius=10)
        timer_input_frame.pack(pady=10, padx=0, fill=ctk.X)

        ctk.CTkLabel(timer_input_frame, text="Set Focus Duration (Minutes):", font=self.label_font).pack(pady=(10, 5))

        self.timer_entry = ctk.CTkEntry(timer_input_frame, width=100, font=self.header_font, justify='center', corner_radius=6)
        self.timer_entry.insert(0, "25")
        self.timer_entry.pack(pady=(0, 10))

        self.countdown_label = ctk.CTkLabel(self.inner_content_frame, text="Ready to focus!", font=self.countdown_font, text_color="#4CAF50")
        self.countdown_label.pack(pady=15)

        self.focus_timer = None
        self.timer_running = False
        self.session_start_time = None

        # --- Control Buttons Frame ---
        button_frame = ctk.CTkFrame(self.inner_content_frame, fg_color="transparent")
        button_frame.pack(pady=10, padx=0, fill=ctk.X)

        self.start_color = "#2ECC71"
        self.stop_color = "#E74C3C"
        self.edit_color = "#3498DB"
        self.calendar_color = "#9B59B6"
        self.exit_color = "#7F8C8D" # Gray
        self.fullscreen_toggle_color = "#F39C12" # Orange for fullscreen toggle

        ctk.CTkButton(button_frame, text="🚀 Start Focus Mode", command=self.start_focus_with_timer, font=self.button_font, fg_color=self.start_color, hover_color="#27AE60", corner_radius=8).pack(pady=7, fill=ctk.X, ipady=5)
        ctk.CTkButton(button_frame, text="🛑 Stop Focus Mode", command=self.stop_focus, font=self.button_font, fg_color=self.stop_color, hover_color="#C0392B", corner_radius=8).pack(pady=7, fill=ctk.X, ipady=5)
        ctk.CTkButton(button_frame, text="🚫 Edit Blocklist", command=self.edit_blocklist, font=self.button_font, fg_color=self.edit_color, hover_color="#2980B9", corner_radius=8).pack(pady=7, fill=ctk.X, ipady=5)
        ctk.CTkButton(button_frame, text="📅 View Activity Calendar", command=self.view_activity_calendar, font=self.button_font, fg_color=self.calendar_color, hover_color="#8E44AD", corner_radius=8).pack(pady=7, fill=ctk.X, ipady=5)
        
        # Add a button to toggle fullscreen if Escape/F11 is not obvious
        ctk.CTkButton(button_frame, text="💻 Toggle Fullscreen (Esc/F11)", command=self.toggle_fullscreen, font=self.button_font, fg_color=self.fullscreen_toggle_color, hover_color="#D35400", corner_radius=8).pack(pady=7, fill=ctk.X, ipady=5)
        
        ctk.CTkButton(button_frame, text="🚪 Exit App", command=self.quit_app, font=self.button_font, fg_color=self.exit_color, hover_color="#606B6D", corner_radius=8).pack(pady=7, fill=ctk.X, ipady=5)

        # --- Streak and Total Time Display ---
        stats_frame = ctk.CTkFrame(self.inner_content_frame, corner_radius=10)
        stats_frame.pack(pady=(10,0), padx=0, fill=ctk.X) # pady 0 at bottom as container has padding

        self.streak_label = ctk.CTkLabel(stats_frame, text="", font=self.small_font)
        self.streak_label.pack(pady=(10, 5))
        self.total_time_label = ctk.CTkLabel(stats_frame, text="", font=self.small_font)
        self.total_time_label.pack(pady=(5, 10))

        self._update_activity_display()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def toggle_fullscreen(self, event=None):
        self._is_fullscreen = not self._is_fullscreen
        self.attributes("-fullscreen", self._is_fullscreen)
        if not self._is_fullscreen:
            # When exiting fullscreen, you might want to set a specific size
            self.geometry(self._initial_windowed_geometry)
            # Or simply let the window manager decide by not setting geometry
            # self.state('normal') # May also be useful

    def quit_app(self):
        self.on_closing()

    # ... (rest of your methods: on_closing, _update_activity_display, start_focus, stop_focus, etc. remain the same) ...
    # Make sure to copy ALL your other methods here without changes unless they are UI related.
    # For brevity, I am not re-pasting all of them but you should have them.

    def on_closing(self):
        if messagebox.askokcancel("Exit Application", "Are you sure you want to exit? Ensure Focus Mode is stopped if active."):
            if self.timer_running: 
                self.stop_focus() 
            self.destroy()

    def _update_activity_display(self):
        current_streak, longest_streak = tc.get_streak_info()
        sessions, total_duration = tc.get_session_history()
        self.streak_label.configure(text=f"🔥 Current Streak: {current_streak} days (Longest: {longest_streak} days)")
        self.total_time_label.configure(text=f"⏱️ Total Focus Time: {total_duration:.1f} minutes")

    def start_focus(self):
        try:
            bc.block_sites()
            bc.start_focus_server()
            self.status_label.configure(text="Status: Focus Mode ON", text_color="green")
            self.session_start_time = datetime.now()
        except PermissionError:
            messagebox.showerror("Permission Error", "Admin rights required to modify the hosts file. Please restart as Administrator.")
            self.stop_focus()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while starting Focus Mode: {e}")
            self.stop_focus()

    def stop_focus(self):
        if self.focus_timer and self.focus_timer.running:
            self.focus_timer.stop_timer()
        self.timer_running = False

        try:
            bc.unblock_all()
            bc.stop_focus_server()
            self.status_label.configure(text="Status: Inactive", text_color="red")
            self.countdown_label.configure(text="Ready to focus!", text_color="#4CAF50") # Use a defined color

            if self.session_start_time:
                session_end_time = datetime.now()
                if (session_end_time - self.session_start_time).total_seconds() >= 1:
                    tc.record_session(self.session_start_time, session_end_time)
                    tc.update_streak()
                self.session_start_time = None
            self._update_activity_display()
        except PermissionError:
            messagebox.showwarning("Permission Warning", "Admin rights required to unblock sites. Please manually check your hosts file.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while stopping Focus Mode: {e}")

    def edit_blocklist(self):
        editor = ctk.CTkToplevel(self)
        editor.title("Edit Blocked Websites")
        editor.geometry("450x500")
        editor.transient(self)
        editor.grab_set()

        ctk.CTkLabel(editor, text="Blocked Sites:", font=self.label_font).pack(pady=10)

        input_frame = ctk.CTkFrame(editor, fg_color="transparent")
        input_frame.pack(pady=5, padx=10, fill=ctk.X)

        new_site_entry = ctk.CTkEntry(input_frame, placeholder_text="Enter site to block (e.g., youtube.com)", width=250, font=self.small_font, corner_radius=6)
        new_site_entry.pack(side=ctk.LEFT, expand=True, fill=ctk.X, padx=(0,10))

        self.blocklist_scrollable_frame = ctk.CTkScrollableFrame(editor, height=250, corner_radius=10) # Instance variable if accessed elsewhere
        self.blocklist_scrollable_frame.pack(padx=10, pady=5, fill=ctk.BOTH, expand=True)

        def populate_blocklist_display():
            for widget in self.blocklist_scrollable_frame.winfo_children():
                widget.destroy()
            current_blocklist = sorted(list(bc.get_blocklist()))
            for site in current_blocklist:
                item_frame = ctk.CTkFrame(self.blocklist_scrollable_frame, fg_color=("gray85", "gray20"))
                item_frame.pack(fill=ctk.X, pady=2, padx=2)
                
                site_label = ctk.CTkLabel(item_frame, text=site, font=self.small_font)
                site_label.pack(side=ctk.LEFT, padx=5, pady=5, expand=True, fill=ctk.X) # Make label expand
                
                remove_button = ctk.CTkButton(item_frame, text="X", font=self.small_font, # Shorter text
                                              width=30, height=20, corner_radius=5, # Smaller button
                                              fg_color=self.stop_color, hover_color="#C0392B",
                                              command=lambda s=site: remove_site(s))
                remove_button.pack(side=ctk.RIGHT, padx=5, pady=5)

        def add_site_to_blocklist():
            site = new_site_entry.get().strip().lower()
            if site:
                if bc.add_to_blocklist(site):
                    messagebox.showinfo("Success", f"'{site}' added to blocklist.", parent=editor)
                    populate_blocklist_display()
                    new_site_entry.delete(0, ctk.END)
                else:
                    messagebox.showwarning("Duplicate", f"'{site}' is already in the blocklist.", parent=editor)
            else:
                messagebox.showwarning("Input Error", "Please enter a site to add.", parent=editor)
        
        add_button = ctk.CTkButton(input_frame, text="Add", command=add_site_to_blocklist, font=self.button_font, width=60, corner_radius=6)
        add_button.pack(side=ctk.LEFT)

        def remove_site(site_to_remove):
            if messagebox.askyesno("Confirm Removal", f"Are you sure you want to remove '{site_to_remove}' from the blocklist?", parent=editor):
                bc.remove_from_blocklist(site_to_remove)
                messagebox.showinfo("Success", f"'{site_to_remove}' removed from blocklist.", parent=editor)
                populate_blocklist_display()

        populate_blocklist_display()
        ctk.CTkButton(editor, text="Close", command=editor.destroy, font=self.button_font, corner_radius=8).pack(pady=(10, 10))

    def start_focus_with_timer(self):
        if self.timer_running:
            messagebox.showwarning("Timer Running", "A focus session is already active. Please stop it first.")
            return
        try:
            # The input from self.timer_entry.get() is in minutes, as per the label
            # and user clarification.
            # We will pass this value directly to FocusTimer.
            duration_in_minutes = int(self.timer_entry.get())
            if duration_in_minutes <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number of minutes (greater than 0).")
            return

        self.start_focus()
        # Only proceed if start_focus didn't encounter a permission error that stopped it
        if "Focus Mode ON" in self.status_label.cget("text"):
            # Pass duration_in_minutes directly to FocusTimer,
            # assuming FocusTimer is designed to accept its duration in minutes.
            self.focus_timer = FocusTimer(duration_in_minutes, self._update_countdown_display, self._on_timer_complete)
            self.focus_timer.start_timer()
            self.timer_running = True
            # Ensure text_color is set appropriately; using a theme color or a specific hex.
            # Using a color that generally contrasts well. You can adjust as needed.
            active_timer_color = ("#007ACC", "#60BFFF") # Dark mode, Light mode blue
            self.countdown_label.configure(text_color=active_timer_color)
    def _update_countdown_display(self, mins, secs):
        self.after(0, lambda: self.countdown_label.configure(text=f"⏳ Time Left: {mins:02}:{secs:02}"))

    def _on_timer_complete(self):
        self.after(0, lambda: self.countdown_label.configure(text="✅ Time's up!", text_color="#4CAF50")) # Use a defined color
        self.after(1000, self.stop_focus)

    def view_activity_calendar(self):
        calendar_viewer = ctk.CTkToplevel(self)
        calendar_viewer.title("Focus Activity Calendar")
        calendar_viewer.geometry("600x650") 
        calendar_viewer.transient(self)
        calendar_viewer.grab_set()

        ctk.CTkLabel(calendar_viewer, text="Your Focus History", font=self.header_font).pack(pady=10)

        cal_container_frame = ctk.CTkFrame(calendar_viewer, corner_radius=10)
        cal_container_frame.pack(pady=10, padx=10, fill=ctk.BOTH, expand=True)
        
        sessions, _ = tc.get_session_history()
        daily_durations = {}
        dates_to_highlight = []

        for s in sessions:
            session_start_dt = datetime.fromisoformat(s['start'])
            session_date = session_start_dt.date()
            daily_durations[session_date] = daily_durations.get(session_date, 0) + s['duration_minutes']
            if session_date not in dates_to_highlight:
                dates_to_highlight.append(session_date)
        
        ctk_bg_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        ctk_text_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        ctk_btn_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"])

        self.cal = Calendar(cal_container_frame, selectmode='day',
                            font="Arial 10",
                            background=ctk_bg_color, 
                            foreground=ctk_text_color,
                            headersbackground=ctk_btn_color, 
                            headersforeground=self._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["text_color"]),
                            normalbackground=ctk_bg_color, 
                            normalforeground=ctk_text_color,
                            selectbackground=self._apply_appearance_mode(ctk.ThemeManager.theme["CTkEntry"]["fg_color"]),
                            selectforeground=ctk_text_color,
                            weekendbackground=self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["top_fg_color"]),
                            weekendforeground=ctk_text_color,
                            othermonthbackground=self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["top_fg_color"]),
                            othermonthforeground="gray",
                            bordercolor=self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["border_color"]),
                            borderwidth=1, locale='en_US', cursor="hand1", date_pattern='yyyy-mm-dd')
        self.cal.pack(pady=10, padx=10, fill=ctk.BOTH, expand=True)
        
        for focus_date in dates_to_highlight:
             self.cal.calevent_create(focus_date, 'Focused Day', 'focus_day')
        
        highlight_color = "#3498DB"
        self.cal.tag_config('focus_day', background=highlight_color, foreground='white')

        self.daily_summary_label = ctk.CTkLabel(calendar_viewer, text="Click on a date to see daily summary.", font=self.small_font)
        self.daily_summary_label.pack(pady=10)

        def on_date_select(event=None):
            try:
                selected_date_str = self.cal.get_date()
                selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            except ValueError:
                 self.daily_summary_label.configure(text="Please select a valid date.")
                 return

            total_for_day = daily_durations.get(selected_date, 0)
            if total_for_day > 0:
                self.daily_summary_label.configure(text=f"Focus Time on {selected_date.strftime('%Y-%m-%d')}: {total_for_day:.1f} minutes")
            else:
                self.daily_summary_label.configure(text=f"No focus sessions on {selected_date.strftime('%Y-%m-%d')}.")
        
        self.cal.bind("<<CalendarSelected>>", on_date_select)
        on_date_select() 

        current_streak, longest_streak = tc.get_streak_info()
        _, total_duration_all = tc.get_session_history()
        
        ctk.CTkLabel(calendar_viewer, text=f"Current Streak: {current_streak} days | Longest Streak: {longest_streak} days",
                     font=self.small_font, text_color=("gray10", "gray90")).pack(pady=(0, 5))
        ctk.CTkLabel(calendar_viewer, text=f"Overall Focus Time: {total_duration_all:.1f} minutes",
                     font=self.small_font, text_color=("gray10", "gray90")).pack(pady=(0, 10))

        ctk.CTkButton(calendar_viewer, text="Close", command=calendar_viewer.destroy, font=self.button_font, corner_radius=8).pack(pady=5)

    def refresh_calendar_schedule_highlights(self):
        if not hasattr(self, 'cal') or not self.cal.winfo_exists():
            return
        
        # Clear previous scheduled events from calendar view
        try:
            self.cal.calevent_remove(tag='scheduled_event')
        except Exception: # Might fail if tag doesn't exist yet
            pass

        pending_schedules = tc.get_upcoming_pending_schedules()
        scheduled_dates_to_mark = set()
        for sched in pending_schedules:
            scheduled_dates_to_mark.add(sched['scheduled_datetime'].date())
        
        for sched_date in scheduled_dates_to_mark:
            # Ensure event_text is simple, actual details shown below calendar
            self.cal.calevent_create(sched_date, 'S', 'scheduled_event') 
        self.cal.tag_config('scheduled_event', background='orange', foreground='black')


    def view_activity_calendar(self):
        # ... (setup for calendar_viewer_window Toplevel, title, geometry) ...
        self.calendar_viewer_window = ctk.CTkToplevel(self) # Store reference
        self.calendar_viewer_window.title("Focus Activity & Scheduling")
        self.calendar_viewer_window.geometry("700x750") # Adjust as needed
        self.calendar_viewer_window.transient(self)
        self.calendar_viewer_window.grab_set()
        self.calendar_viewer_window.attributes("-topmost", True)


        ctk.CTkLabel(self.calendar_viewer_window, text="Focus History & Scheduler", font=self.header_font).pack(pady=10)

        cal_container_frame = ctk.CTkFrame(self.calendar_viewer_window, corner_radius=10)
        cal_container_frame.pack(pady=10, padx=10, fill=ctk.BOTH, expand=True)

        # --- Initialize and populate daily_durations for past sessions FIRST ---
        past_sessions_data, _ = tc.get_session_history()
        past_focus_dates = []
        daily_durations = {} # DEFINED AND INITIALIZED HERE
        for s_past in past_sessions_data:
            try:
                session_start_dt = datetime.fromisoformat(s_past['start'])
                session_date = session_start_dt.date()
                daily_durations[session_date] = daily_durations.get(session_date, 0) + s_past['duration_minutes'] # POPULATED HERE
                if session_date not in past_focus_dates:
                    past_focus_dates.append(session_date)
            except ValueError:
                print(f"Warning: Could not parse date from past session: {s_past.get('start')}")
                continue
        # --- End of daily_durations initialization ---

        # --- Calendar Widget setup ---
        # Use your existing styling for tkcalendar, try to match CTk theme
        ctk_bg_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        ctk_text_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        ctk_btn_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"])
        
        self.cal = Calendar(cal_container_frame, selectmode='day',
                            font="Arial 10",
                            background=ctk_bg_color,
                            foreground=ctk_text_color,
                            headersbackground=ctk_btn_color,
                            headersforeground=self._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["text_color"]),
                            selectbackground=self._apply_appearance_mode(ctk.ThemeManager.theme["CTkEntry"]["fg_color"]),
                            weekendbackground=self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["top_fg_color"]),
                            othermonthbackground=self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["top_fg_color"]),
                            bordercolor=self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["border_color"]),
                            date_pattern='yyyy-mm-dd', # Ensure this pattern is used
                            locale='en_US',
                            cursor="hand1")
        
        # Highlight past focus days using the populated daily_durations/past_focus_dates
        for focus_date_past in past_focus_dates:
            self.cal.calevent_create(focus_date_past, 'Past Focus', 'focus_day')
        self.cal.tag_config('focus_day', background="#3498DB", foreground='white') # Blue for past focus

        self.refresh_calendar_schedule_highlights() # For future scheduled events

        self.cal.pack(pady=10, padx=10, fill=ctk.BOTH, expand=True)


        # --- Frame for Schedule Actions (Selected Date Label & New Schedule Button) ---
        self.schedule_details_frame = ctk.CTkFrame(self.calendar_viewer_window, fg_color="transparent")
        self.schedule_details_frame.pack(pady=10, padx=10, fill=ctk.X)
        
        # This label will be updated by on_calendar_date_select_extended
        self.daily_summary_label = ctk.CTkLabel(self.schedule_details_frame, text="Select a date.", font=self.small_font)
        self.daily_summary_label.pack(side=ctk.LEFT, padx=(0,10), expand=True, fill=ctk.X)

        self.add_schedule_button = ctk.CTkButton(self.schedule_details_frame, text="New Schedule",
                                                 command=self.open_schedule_dialog, state=ctk.DISABLED)
        self.add_schedule_button.pack(side=ctk.RIGHT)

        # --- Frame to list scheduled items for the selected date ---
        self.scheduled_items_listbox_frame = ctk.CTkScrollableFrame(self.calendar_viewer_window, height=150, label_text="Scheduled for Selected Date")
        self.scheduled_items_listbox_frame.pack(pady=5, padx=10, fill=ctk.X)
        self._update_scheduled_items_display(None) # Initial placeholder


        # --- Bindings and summary labels ---
        # Now daily_durations is defined and can be passed
        self.cal.bind("<<CalendarSelected>>", lambda event: self.on_calendar_date_select_extended(event, daily_durations))
        # Initial call to set the state based on today's date (or default calendar selection)
        self.on_calendar_date_select_extended(None, daily_durations) 

        # --- Overall Streak and Focus Time (as before) ---
        current_streak_overall, longest_streak_overall = tc.get_streak_info()
        _, total_duration_all_sessions = tc.get_session_history()
        
        ctk.CTkLabel(self.calendar_viewer_window, text=f"Current Streak: {current_streak_overall} days | Longest: {longest_streak_overall} days",
                     font=self.small_font).pack(pady=(5, 0))
        ctk.CTkLabel(self.calendar_viewer_window, text=f"Overall Focus Time: {total_duration_all_sessions:.1f} minutes",
                     font=self.small_font).pack(pady=(0, 10))

        ctk.CTkButton(self.calendar_viewer_window, text="Close", command=self.calendar_viewer_window.destroy, font=self.button_font, corner_radius=8).pack(pady=10)

    # Ensure the on_calendar_date_select_extended method correctly uses daily_durations_past
    def on_calendar_date_select_extended(self, event, daily_durations_past): # Renamed for clarity
        if not hasattr(self, 'cal') or not self.cal.winfo_exists(): return
        try:
            # Get selected date as a datetime.date object directly
            selected_date_obj = self.cal.selection_get()
            if selected_date_obj is None: # selection_get() can return None if no date is truly selected
                 # Fallback to get_date if selection_get is None, though it might be problematic
                 selected_date_str_cal = self.cal.get_date() 
                 selected_date_obj = datetime.strptime(selected_date_str_cal, self.cal._properties['date_pattern']).date()
        except Exception as e:
            print(f"Error getting selected date: {e}")
            self.daily_summary_label.configure(text="Please select a date.")
            self.add_schedule_button.configure(state=ctk.DISABLED)
            self._update_scheduled_items_display(None)
            return

        today = datetime.now().date()
        
        # Update the daily_summary_label based on whether the date is past or future
        if selected_date_obj < today: # Past date
            self.add_schedule_button.configure(state=ctk.DISABLED, text="New Schedule")
            total_for_day = daily_durations_past.get(selected_date_obj, 0)
            if total_for_day > 0:
                self.daily_summary_label.configure(text=f"Past Focus on {selected_date_obj.strftime('%b %d, %Y')}: {total_for_day:.1f} mins")
            else:
                self.daily_summary_label.configure(text=f"No past focus recorded for {selected_date_obj.strftime('%b %d, %Y')}.")
            self._update_scheduled_items_display(None) # Clear scheduled items for past dates
        else: # Today or Future date
            self.daily_summary_label.configure(text=f"Actions for {selected_date_obj.strftime('%b %d, %Y')}:")
            self.add_schedule_button.configure(state=ctk.NORMAL, text=f"Schedule for {selected_date_obj.strftime('%b %d')}")
            self._update_scheduled_items_display(selected_date_obj)

    def _update_scheduled_items_display(self, date_obj):
        for widget in self.scheduled_items_listbox_frame.winfo_children():
            widget.destroy()

        if date_obj is None:
            ctk.CTkLabel(self.scheduled_items_listbox_frame, text="Past date selected or no date.").pack(pady=5)
            return

        schedules = tc.get_scheduled_sessions(start_date=date_obj, end_date=date_obj, status_filter='pending')
        if not schedules:
            ctk.CTkLabel(self.scheduled_items_listbox_frame, text="No pending schedules for this date.").pack(pady=5)
        else:
            for sched in schedules:
                item_text = f"{sched['scheduled_datetime'].strftime('%H:%M')} for {sched['duration_minutes']}m"
                if sched['notes']: item_text += f" ({sched['notes'][:20]}...)"
                
                item_frame = ctk.CTkFrame(self.scheduled_items_listbox_frame)
                item_frame.pack(fill=ctk.X, pady=2)
                ctk.CTkLabel(item_frame, text=item_text).pack(side=ctk.LEFT, padx=5, expand=True, anchor='w')
                
                edit_btn = ctk.CTkButton(item_frame, text="Edit", width=50,
                                        command=lambda s=sched: self.open_schedule_dialog(existing_schedule=s))
                edit_btn.pack(side=ctk.RIGHT, padx=2)
                
                del_btn = ctk.CTkButton(item_frame, text="Del", width=40, fg_color="tomato",
                                        command=lambda s_id=sched['id']: self._delete_schedule_action(s_id))
                del_btn.pack(side=ctk.RIGHT, padx=2)

    def _delete_schedule_action(self, schedule_id):
        if messagebox.askyesno("Confirm Delete", "Delete this scheduled session?"):
            if tc.delete_scheduled_session(schedule_id):
                messagebox.showinfo("Success", "Schedule deleted.")
                self.refresh_calendar_schedule_highlights()
                # Refresh the list for the currently selected date
                if hasattr(self, 'cal') and self.cal.winfo_exists() and self.cal.selection_get():
                    self._update_scheduled_items_display(self.cal.selection_get())
                else: # Fallback if no date is selected somehow
                    self._update_scheduled_items_display(None)

            else:
                messagebox.showerror("Error", "Could not delete schedule.")


    def open_schedule_dialog(self, existing_schedule=None):
        # --- This is where you build the CTkToplevel dialog ---
        # Inputs: Date (pre-filled), Time (HH:MM), Duration (mins), Notes
        # Buttons: Save, Cancel
        # On Save: Call tc.add_scheduled_session or tc.update_scheduled_session
        # Then, refresh calendar highlights and the list for the selected date.

        dialog = ctk.CTkToplevel(self.calendar_viewer_window if hasattr(self, 'calendar_viewer_window') and self.calendar_viewer_window.winfo_exists() else self)
        dialog.grab_set() # Make dialog modal
        dialog.attributes("-topmost", True)

        if existing_schedule:
            dialog.title("Edit Schedule")
            # Pre-fill fields from existing_schedule
            schedule_dt = existing_schedule['scheduled_datetime']
            initial_date = schedule_dt.date()
            initial_hour = f"{schedule_dt.hour:02d}"
            initial_minute = f"{schedule_dt.minute:02d}"
            initial_duration = str(existing_schedule['duration_minutes'])
            initial_notes = existing_schedule['notes'] if existing_schedule['notes'] else ""
        else:
            dialog.title("New Schedule")
            try:
                initial_date = self.cal.selection_get() # Get current selection from calendar
                if initial_date < datetime.now().date(): # Should not happen if button state is managed
                    messagebox.showerror("Error", "Cannot schedule for a past date.", parent=dialog)
                    dialog.destroy()
                    return
            except Exception:
                messagebox.showerror("Error", "No date selected in calendar.", parent=dialog)
                dialog.destroy()
                return
            
            # Default new schedule values
            initial_hour = "09"
            initial_minute = "00"
            initial_duration = "25"
            initial_notes = ""

        dialog.geometry("400x350")
        ctk.CTkLabel(dialog, text=f"Date: {initial_date.strftime('%Y-%m-%d')}", font=self.label_font).pack(pady=10)

        # Time Input Frame
        time_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        time_frame.pack(pady=5, padx=20, fill=ctk.X)
        ctk.CTkLabel(time_frame, text="Time:").pack(side=ctk.LEFT)
        hours_val = [f"{i:02d}" for i in range(24)]
        minutes_val = [f"{i:02d}" for i in range(0, 60, 5)] # Stepped minutes
        
        hour_var = ctk.StringVar(value=initial_hour)
        minute_var = ctk.StringVar(value=initial_minute)

        hour_menu = ctk.CTkOptionMenu(time_frame, variable=hour_var, values=hours_val, width=70)
        hour_menu.pack(side=ctk.LEFT, padx=5)
        ctk.CTkLabel(time_frame, text=":").pack(side=ctk.LEFT)
        minute_menu = ctk.CTkOptionMenu(time_frame, variable=minute_var, values=minutes_val, width=70)
        minute_menu.pack(side=ctk.LEFT, padx=5)

        # Duration Input
        dur_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        dur_frame.pack(pady=5, padx=20, fill=ctk.X)
        ctk.CTkLabel(dur_frame, text="Duration (mins):").pack(side=ctk.LEFT)
        duration_entry = ctk.CTkEntry(dur_frame, width=70)
        duration_entry.insert(0, initial_duration)
        duration_entry.pack(side=ctk.LEFT, padx=5)

        # Notes
        ctk.CTkLabel(dialog, text="Notes:").pack(pady=(5,0), padx=20, anchor='w')
        notes_text = ctk.CTkTextbox(dialog, height=60)
        notes_text.pack(pady=5, padx=20, fill=ctk.X)
        if initial_notes: notes_text.insert("1.0", initial_notes)

        def save_action():
            hour = int(hour_var.get())
            minute = int(minute_var.get())
            try:
                duration = int(duration_entry.get())
                if duration <=0: raise ValueError("Duration must be positive")
            except ValueError as e:
                messagebox.showerror("Invalid Input", f"Duration is invalid: {e}", parent=dialog)
                return
            
            notes = notes_text.get("1.0", "end-1c").strip()
            
            scheduled_dt = datetime.combine(initial_date, datetime(initial_date.year, initial_date.month, initial_date.day, hour, minute).time())

            # Basic validation for future time if it's for today
            if scheduled_dt.date() == datetime.now().date() and scheduled_dt.time() <= datetime.now().time():
                messagebox.showerror("Invalid Time", "Scheduled time for today must be in the future.", parent=dialog)
                return

            if existing_schedule: # Update logic - not fully implemented in tc yet, but structure is there
                # For a full update, you might need a tc.update_scheduled_session(id, dt, dur, notes)
                # For simplicity now, let's delete and re-add if editing is complex
                # Or, if tc.update_scheduled_session handles all fields:
                # success = tc.update_scheduled_session(existing_schedule['id'], scheduled_dt, duration, notes)
                # For now, let's assume we'd delete and add for simplicity if not direct update
                messagebox.showinfo("Info", "Update logic needs full tc.update_scheduled_session.", parent=dialog)
                return # Placeholder
            else:
                new_id = tc.add_scheduled_session(scheduled_dt, duration, notes)
                if new_id:
                    messagebox.showinfo("Success", "Session scheduled!", parent=dialog)
                else:
                    messagebox.showerror("Error", "Failed to schedule session.", parent=dialog)
                    return # Don't close if error

            dialog.destroy()
            self.refresh_calendar_schedule_highlights()
            self._update_scheduled_items_display(initial_date)


        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=10, padx=20, fill=ctk.X)
        ctk.CTkButton(btn_frame, text="Save", command=save_action).pack(side=ctk.RIGHT, padx=5)
        ctk.CTkButton(btn_frame, text="Cancel", command=dialog.destroy, fg_color="gray50").pack(side=ctk.RIGHT)


if __name__ == "__main__":
    if not is_admin():
        try:
            root_check = ctk.CTk()
            root_check.withdraw()
            messagebox.showerror("Permission Error", "This application requires administrator privileges. Please run as Administrator.")
            root_check.destroy()
        except Exception:
            print("❌ Please run this script as administrator.")
        sys.exit(1)

    tc.init_db()
    bc.init_db()

    app = BlockerGUI()
    app.mainloop()