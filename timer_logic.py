import time
import threading

class FocusTimer:
    def __init__(self, duration_minutes, on_tick_callback, on_complete_callback):
        self.duration_minutes = duration_minutes
        self.on_tick_callback = on_tick_callback
        self.on_complete_callback = on_complete_callback
        self.remaining_time = 0
        self.timer_thread = None
        self.running = False

    def start_timer(self):
        if self.running:
            return

        self.running = True
        self.remaining_time = self.duration_minutes * 60
        self.timer_thread = threading.Thread(target=self._run_countdown, daemon=True)
        self.timer_thread.start()

    def stop_timer(self):
        self.running = False

    def _run_countdown(self):
        while self.running and self.remaining_time > 0:
            mins, secs = divmod(self.remaining_time, 60)
            self.on_tick_callback(mins, secs)
            time.sleep(1)
            self.remaining_time -= 1

        if self.running:  # Timer completed naturally
            self.running = False
            self.on_complete_callback()