import time
from datetime import datetime

class SessionManager:
    def __init__(self, config, notifier):
        self.notifier = notifier
        self.settings = config.get('occupancy_settings', {})

        # Config Parameters
        self.enabled = self.settings.get('enabled', True)
        self.mode = self.settings.get('mode', 'session')  # 'session' or 'timer'
        self.min_session_mins = self.settings.get('min_session_minutes', 3)
        self.batch_delay = self.settings.get('batch_delay_seconds', 30)
        self.hourly_snapshot = self.settings.get('hourly_snapshot_enabled', True)

        # State Tracking
        # { "PC-01": { "state": "OFFLINE", "last_change": timestamp, "session_start": timestamp } }
        self.pc_states = {}

        # Batching Queue
        # { "start": [pc_names], "end": [(pc_name, duration)] }
        self.batch_queue = {"start": [], "end": []}
        self.batch_timer_start = None

        # Hourly Snapshot Timer
        self.last_snapshot = datetime.now()

    def update_config(self, config):
        self.settings = config.get('occupancy_settings', {})
        self.enabled = self.settings.get('enabled', True)
        self.min_session_mins = self.settings.get('min_session_minutes', 3)

    def process_scan(self, current_online_ips, all_pc_list):
        # Main logic loop called every scan cycle.
        if not self.enabled or self.mode != 'session':
            return

        now = time.time()

        # 1. Initialize State for new PCs
        for i, ip in enumerate(all_pc_list):
            name = f"PC-{i + 1}"
            if name not in self.pc_states:
                self.pc_states[name] = {
                    "state": "OFFLINE",  # Assumed start state
                    "last_change": now,
                    "session_start": None,
                    "pending_state": None # If waiting for stability
                }

        # 2. Check Status Changes
        for i, ip in enumerate(all_pc_list):
            name = f"PC-{i + 1}"
            is_online = ip in current_online_ips
            data = self.pc_states[name]

            # --- STABILITY LOGIC ---
            # We don't flip "state" immediately. We check "pending_state".

            current_detected = "ONLINE" if is_online else "OFFLINE"

            if data["state"] == current_detected:
                # No change needed, reset pending
                data["pending_state"] = None
                continue

            # Change detected!
            if data["pending_state"] != current_detected:
                # First time seeing this change? Start stability timer.
                data["pending_state"] = current_detected
                data["last_change"] = now
            else:
                # Stability Check
                elapsed = (now - data["last_change"]) / 60.0 # minutes
                if elapsed >= self.min_session_mins:
                    # CONFIRMED CHANGE
                    self._handle_confirmed_change(name, current_detected, now)

        # 3. Process Batch Queue
        self._process_batch()

        # 4. Hourly Snapshot (Optional)
        if self.hourly_snapshot:
            self._check_hourly_snapshot(len(current_online_ips), len(all_pc_list))

    def _handle_confirmed_change(self, name, new_state, timestamp):
        data = self.pc_states[name]

        # Update State
        old_state = data["state"]
        data["state"] = new_state
        data["pending_state"] = None # Reset pending

        # LOGIC: SESSION START
        if new_state == "ONLINE":
            data["session_start"] = datetime.now()
            # Add to Batch
            self._add_to_batch("start", name)

        # LOGIC: SESSION END
        elif new_state == "OFFLINE":
            start_time = data["session_start"]
            duration_str = "Unknown"

            if start_time:
                duration = datetime.now() - start_time
                # Format duration (e.g., "2h 15m")
                total_seconds = int(duration.total_seconds())
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                if hours > 0:
                    duration_str = f"{hours}h {minutes}m"
                else:
                    duration_str = f"{minutes}m"

            data["session_start"] = None # Reset

            # Add to Batch
            self._add_to_batch("end", (name, duration_str))

    def _add_to_batch(self, type_key, item):
        # Start timer if not running
        if self.batch_timer_start is None:
            self.batch_timer_start = time.time()

        self.batch_queue[type_key].append(item)

    def _process_batch(self):
        if self.batch_timer_start is None:
            return

        elapsed = time.time() - self.batch_timer_start
        if elapsed >= self.batch_delay:
            # FIRE!
            starts = self.batch_queue["start"]
            ends = self.batch_queue["end"]

            if starts:
                self.notifier.send_session_start(starts)
            if ends:
                self.notifier.send_session_end(ends)

            # Reset
            self.batch_queue = {"start": [], "end": []}
            self.batch_timer_start = None

    def _check_hourly_snapshot(self, current_count, total_count):
        now = datetime.now()
        elapsed = now - self.last_snapshot
        if elapsed.total_seconds() > 3600: # 1 hour fixed
            self.last_snapshot = now
            self.notifier.send_hourly_snapshot(current_count, total_count)