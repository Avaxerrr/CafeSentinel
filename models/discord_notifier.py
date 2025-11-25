import json
import requests
from datetime import datetime


class DiscordNotifier:
    def __init__(self, config):
        self.config = config.get('discord_settings', {})
        self.enabled = self.config.get('enabled', False)

        # --- LOAD WEBHOOKS ---
        self.alerts_url = self.config.get('webhook_alerts', '')
        self.occupancy_url = self.config.get('webhook_occupancy', '')
        self.screenshots_url = self.config.get('webhook_screenshots', '')
        self.shop_name = self.config.get('shop_name', 'Internet Cafe')

    def _send_payload(self, url, payload, file_buffer=None, filename="image.webp"):
        """Generic sender"""
        if not self.enabled or not url or "YOUR_" in url:
            return

        try:
            data = {'payload_json': json.dumps(payload)}
            files = None
            if file_buffer:
                mime_type = 'image/webp' if filename.endswith('webp') else 'text/plain'
                files = {'file': (filename, file_buffer, mime_type)}

            requests.post(url, data=data, files=files)

        except Exception:
            # Silent fail on network errors to avoid log clutter
            pass

    def send_outage_report(self, duration, cause, client_count, start_time, end_time, screenshot_data=None):
        if not self.alerts_url: return
        color = 15158332 if cause != "ROUTER_DOWN" else 16776960
        start_str = start_time.strftime("%I:%M %p")
        end_str = end_time.strftime("%I:%M %p")
        embed = {
            "title": f"🚨 Service Restored: {cause}",
            "description": f"**Duration:** {duration}\n**Clients Affected:** {client_count}",
            "color": color,
            "fields": [{"name": "Start Time", "value": start_str, "inline": True},
                       {"name": "End Time", "value": end_str, "inline": True}],
            "footer": {"text": f"{self.shop_name} Monitor • {datetime.now().strftime('%Y-%m-%d')}"}
        }
        payload = {"username": self.shop_name, "embeds": [embed]}
        if screenshot_data:
            embed["image"] = {"url": "attachment://evidence.webp"}
            self._send_payload(self.alerts_url, payload, screenshot_data, "evidence.webp")
        else:
            self._send_payload(self.alerts_url, payload)

    def send_hourly_occupancy(self, current_clients, total_pcs, screenshot_data=None):
        if not self.occupancy_url: return
        percent = int((current_clients / total_pcs) * 100)
        embed = {
            "title": "📊 Hourly Occupancy Report",
            "description": f"**Active Clients:** {current_clients} / {total_pcs}\n**Utilization:** {percent}%",
            "color": 3066993,
            "footer": {"text": f"{self.shop_name} • {datetime.now().strftime('%I:%M %p')}"}
        }
        payload = {"username": self.shop_name, "embeds": [embed]}
        target_url = self.screenshots_url if (self.screenshots_url and screenshot_data) else self.occupancy_url
        if screenshot_data:
            embed["image"] = {"url": "attachment://status.webp"}
            self._send_payload(target_url, payload, screenshot_data, "status.webp")
        else:
            self._send_payload(target_url, payload)