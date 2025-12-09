import json
import requests
from datetime import datetime

class DiscordNotifier:
    def __init__(self, config):
        self.update_config(config)

    def update_config(self, config):
        """Reload settings from new config dict."""
        self.config = config.get('discord_settings', {})
        self.enabled = self.config.get('enabled', False)
        self.alerts_url = self.config.get('webhook_alerts', "")
        self.occupancy_url = self.config.get('webhook_occupancy', "")
        self.screenshots_url = self.config.get('webhook_screenshots', "")
        self.shop_name = self.config.get('shop_name', "Internet Cafe")

    def send_payload(self, url, payload, file_buffer=None, filename="image.webp"):
        if not self.enabled or not url or "YOUR_" in url:
            return

        try:
            data = {"payload_json": json.dumps(payload)}
            files = None
            if file_buffer:
                mimetype = 'image/webp' if filename.endswith('webp') else 'text/plain'
                files = {
                    'file': (filename, file_buffer, mimetype)
                }

            response = requests.post(url, data=data, files=files)

            # --- ADDED LOGGING ---
            if response.status_code not in [200, 204]:
                from models.app_logger import AppLogger
                AppLogger.log(f"Discord Upload Failed: {response.status_code} - {response.text}", category="ERROR")
            # ---------------------

        except Exception as e:
            # --- ADDED LOGGING ---
            from models.app_logger import AppLogger
            AppLogger.log(f"Discord Connection Error: {str(e)}", category="ERROR")
            # ---------------------

    def send_outage_report(self, duration, cause, client_count, start_time, end_time, screenshot_data=None):
        if not self.alerts_url:
            return

        color = 15158332 if "ROUTER" not in cause else 16776960 # Red vs Yellow
        start_str = start_time.strftime("%I:%M %p")
        end_str = end_time.strftime("%I:%M %p")

        title = "Service Restored"
        if "ROUTER" in cause: title = "Router Restored"
        elif "SERVER" in cause: title = "Server Restored"
        elif "ISP" in cause: title = "Internet Restored"

        embed = {
            "title": title,
            "description": f"**Duration:** {duration}\n**Active:** {client_count}",
            "color": color,
            "fields": [
                {"name": "Start Time", "value": start_str, "inline": True},
                {"name": "End Time", "value": end_str, "inline": True}
            ],
            "footer": {"text": f"{self.shop_name} Monitor • {datetime.now().strftime('%Y-%m-%d')}"}
        }

        payload = {
            "username": self.shop_name,
            "embeds": [embed]
        }

        if screenshot_data:
            embed["image"] = {"url": "attachment://evidence.webp"}
            self.send_payload(self.alerts_url, payload, screenshot_data, "evidence.webp")
        else:
            self.send_payload(self.alerts_url, payload)

    def send_session_start(self, pc_list):
        if not self.occupancy_url:
            return

        count = len(pc_list)
        if count > 5:
            desc = f"{count} Clients Came Online"
        else:
            names = ", ".join(pc_list)
            desc = f"New Sessions: {names}"

        embed = {
            "title": "New Activity",
            "description": desc,
            "color": 5763719, # Green
            "footer": {"text": f"{self.shop_name} • {datetime.now().strftime('%I:%M %p')}"}
        }

        self.send_payload(self.occupancy_url, {"username": self.shop_name, "embeds": [embed]})

    def send_session_end(self, pc_data_list):
        if not self.occupancy_url:
            return

        count = len(pc_data_list)
        if count > 5:
            desc = f"{count} Clients Went Offline"
        else:
            lines = []
            for name, duration in pc_data_list:
                lines.append(f"• {name} ({duration})")
            desc = "\n".join(lines)

        embed = {
            "title": "Session Ended",
            "description": desc,
            "color": 15548997, # Red
            "footer": {"text": f"{self.shop_name} • {datetime.now().strftime('%I:%M %p')}"}
        }

        self.send_payload(self.occupancy_url, {"username": self.shop_name, "embeds": [embed]})

    def send_hourly_snapshot(self, current, total):
        if not self.occupancy_url:
            return

        percent = int((current / total) * 100)
        embed = {
            "title": "Hourly Snapshot",
            "description": f"Active Clients: **{current}/{total}** ({percent}%)",
            "color": 3066993, # Blue
            "footer": {"text": f"{self.shop_name} • {datetime.now().strftime('%I:%M %p')}"}
        }

        self.send_payload(self.occupancy_url, {"username": self.shop_name, "embeds": [embed]})

    def send_routine_screenshot(self, screenshot_data):
        if not self.screenshots_url or not screenshot_data:
            return

        embed = {
            "title": "Routine Screenshot",
            "color": 9807270, # Gray
            "image": {"url": "attachment://routine.webp"},
            "footer": {"text": f"{self.shop_name} • {datetime.now().strftime('%I:%M %p')}"}
        }

        payload = {
            "username": self.shop_name,
            "embeds": [embed]
        }

        self.send_payload(self.screenshots_url, payload, screenshot_data, "routine.webp")