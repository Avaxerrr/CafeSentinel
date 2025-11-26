"""
Resource Manager - Nuitka Edition
Handles file paths for both script mode and Nuitka-compiled executables.
"""
import sys
import os


class ResourceManager:
    @staticmethod
    def get_base_dir():
        """
        Get the base directory of the application.
        """
        if getattr(sys, 'frozen', False):
            # Running as compiled EXE (Nuitka sets sys.frozen = True)
            return os.path.dirname(sys.executable)
        elif hasattr(sys, '__compiled__'):
             # Nuitka compiled (sometimes frozen isn't set depending on flags)
             return os.path.dirname(os.path.abspath(sys.argv[0]))
        else:
            # Running as Python script
            # Go up one level from utils/ to get project root
            return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @staticmethod
    def get_resource_path(relative_path):
        """
        Get absolute path to a resource file.
        In Nuitka standalone mode, resources are next to the exe.
        """
        base_dir = ResourceManager.get_base_dir()
        return os.path.join(base_dir, relative_path)

    # ✅ ADD THIS METHOD BACK as an alias
    @staticmethod
    def get_bundled_resource(relative_path):
        """
        Alias for get_resource_path since Nuitka standalone
        keeps resources in the same folder, not bundled inside the exe.
        """
        return ResourceManager.get_resource_path(relative_path)