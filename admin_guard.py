import win32api
import win32security
import win32con
import ctypes
import sys


class AdminGuard:
    @staticmethod
    def is_admin():
        """Checks if the script is running with Admin privileges."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    @staticmethod
    def protect_process():
        """
        Modifies the current process security token to DENY 'Terminate'
        rights to everyone (including the user running it).
        """
        if not AdminGuard.is_admin():
            print("⚠️ GUARD WARNING: Script not running as Admin. Protection failed.")
            return False

        try:
            # 1. Get the handle to the current process
            # PROCESS_ALL_ACCESS allows us to read/change the DACL
            h_process = win32api.OpenProcess(
                win32con.PROCESS_ALL_ACCESS, False, win32api.GetCurrentProcessId()
            )

            # 2. Get the current Security Descriptor (DACL)
            sd = win32security.GetSecurityInfo(
                h_process,
                win32security.SE_KERNEL_OBJECT,
                win32security.DACL_SECURITY_INFORMATION
            )
            dacl = sd.GetSecurityDescriptorDacl()

            # 3. Find the SID for "Everyone" (S-1-1-0) to apply the rule globally
            everyone_sid = win32security.LookupAccountName("", "Everyone")[0]

            # 4. Add a DENY ACE (Access Control Entry) for Termination
            # This explicitly says: "Everyone is FORBIDDEN from killing this."
            dacl.AddAccessDeniedAce(
                win32security.ACL_REVISION,
                win32con.PROCESS_TERMINATE,
                everyone_sid
            )

            # 5. Save the new DACL back to the process
            win32security.SetSecurityInfo(
                h_process,
                win32security.SE_KERNEL_OBJECT,
                win32security.DACL_SECURITY_INFORMATION,
                None, None, dacl, None
            )

            print("🛡️ PROCESS PROTECTION ACTIVE: Task Manager kill blocked.")
            return True

        except Exception as e:
            print(f"❌ PROTECTION ERROR: {e}")
            return False
