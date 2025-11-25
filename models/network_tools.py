import subprocess
import platform


class NetworkTools:
    @staticmethod
    def ping(host):
        """
        Returns True if host responds, False if timed out.
        Optimized for Windows (hides console window).
        """
        # Select flags based on OS
        is_windows = platform.system().lower() == 'windows'
        param = '-n' if is_windows else '-c'
        timeout_flag = '-w' if is_windows else '-W'
        timeout_val = '1000' if is_windows else '1'  # 1000ms or 1s

        command = ['ping', param, '1', timeout_flag, timeout_val, host]

        try:
            # Windows specific flag to hide the popup console window
            startupinfo = None
            if is_windows:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            subprocess.check_call(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                startupinfo=startupinfo
            )
            return True
        except Exception:
            return False
