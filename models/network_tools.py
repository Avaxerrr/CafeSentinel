from icmplib import multiping
import logging


class NetworkTools:
    @staticmethod
    def scan_hosts(ip_list):
        """
        Scans a list of IPs using raw ICMP sockets (requires Admin).
        Returns a list of IP strings that are ONLINE.
        """
        if not ip_list:
            return []

        try:
            # multiping is concurrent and non-blocking.
            # timeout=1: Wait max 1 second for reply.
            # count=1: Send 1 ping per host (sufficient for status check).
            # privileged=True: Use raw sockets (fast, no subprocess).
            hosts = multiping(ip_list, count=1, interval=0.05, timeout=1, privileged=True)

            online_ips = []
            for host in hosts:
                if host.is_alive:
                    online_ips.append(host.address)

            return online_ips

        except Exception as e:
            logging.error(f"Network Scan Error: {e}")
            return []
