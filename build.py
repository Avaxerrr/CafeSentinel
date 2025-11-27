"""
CafeSentinel Build Script - Separate Folders Approach
Builds two independent executables in their own folders.
Includes Stealth VBS Launcher and Automatic Resource Compilation.
"""
import subprocess
import sys
import os
import shutil
from pathlib import Path


class SeparateFoldersBuilder:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.dist_folder = self.project_root / "dist"

    def clean_previous_builds(self):
        """Remove previous build artifacts and compiled resources."""
        print("🧹 Cleaning previous builds...")

        if self.dist_folder.exists():
            shutil.rmtree(self.dist_folder)
            print(f"   Removed: {self.dist_folder.name}")

        # Clean Nuitka cache
        for pattern in ["*.build", "*.dist", "*.onefile-build"]:
            for folder in self.project_root.glob(pattern):
                if folder.is_dir():
                    shutil.rmtree(folder)
                    print(f"   Removed: {folder.name}")

        # Clean compiled resources to force regeneration
        rcc_file = self.project_root / "resources_rc.py"
        if rcc_file.exists():
            rcc_file.unlink()
            print(f"   Removed: {rcc_file.name}")

        print("✅ Cleanup complete.\n")

    def compile_resources(self):
        """Compiles the .qrc file into a Python module using pyside6-rcc."""
        print("=" * 60)
        print("🎨 Compiling Resources (Icons)")
        print("=" * 60)

        qrc_file = self.project_root / "resources.qrc"
        py_file = self.project_root / "resources_rc.py"

        if not qrc_file.exists():
            print(f"⚠️ Warning: {qrc_file.name} not found. Skipping resource compilation.")
            # We return True to allow build to proceed, but app might fail if it imports it
            return True

        # Command: pyside6-rcc resources.qrc -o resources_rc.py
        # using shell=True to ensure Windows finds the command in PATH
        cmd = f"pyside6-rcc \"{qrc_file}\" -o \"{py_file}\""

        try:
            subprocess.run(cmd, check=True, shell=True)
            print(f"✅ Compiled: {qrc_file.name} -> {py_file.name}\n")
            return True
        except subprocess.CalledProcessError:
            print(f"❌ Failed to compile resources. Make sure 'pyside6-rcc' is in your PATH.\n")
            return False

    def build_main_app(self):
        """Build CafeSentinel.exe."""
        print("=" * 60)
        print("📦 Building CafeSentinel.exe")
        print("=" * 60)

        cmd = [
            sys.executable, "-m", "nuitka",
            "--standalone",
            "--windows-console-mode=disable",
            "--enable-plugin=pyside6",
            f"--windows-icon-from-ico={self.project_root / 'icon.ico'}",
            "--company-name=CafeSentinel",
            "--product-name=CafeSentinel Monitor",
            "--file-version=1.0.0.0",
            "--product-version=1.0.0",
            "--file-description=Internet Cafe Network Monitor",
            "--windows-uac-admin",
            "--assume-yes-for-downloads",
            "--output-dir=build_temp",
            "interface.py"
        ]

        result = subprocess.run(cmd, cwd=self.project_root)

        if result.returncode != 0:
            print("\n❌ Build failed\n")
            return False

        print("\n✅ CafeSentinel.exe built!\n")
        return True

    def build_watchdog(self):
        """Build SentinelService.exe."""
        print("=" * 60)
        print("📦 Building SentinelService.exe")
        print("=" * 60)

        cmd = [
            sys.executable, "-m", "nuitka",
            "--standalone",
            "--company-name=CafeSentinel",
            "--product-name=SentinelService",
            "--file-version=1.0.0.0",
            "--product-version=1.0.0",
            "--file-description=CafeSentinel Watchdog",
            "--windows-uac-admin",
            "--assume-yes-for-downloads",
            "--output-dir=build_temp",
            "--windows-console-mode=disable",
            "watchdog_service.py"
        ]

        result = subprocess.run(cmd, cwd=self.project_root)

        if result.returncode != 0:
            print("\n❌ Build failed\n")
            return False

        print("\n✅ SentinelService.exe built!\n")
        return True

    def organize_deployment(self):
        """Organize builds into separate folders."""
        print("📁 Creating deployment structure...")

        # Create deployment root
        deploy_root = self.dist_folder / "CafeSentinel_Deploy"
        deploy_root.mkdir(parents=True, exist_ok=True)

        # Move main app to its folder
        main_source = self.project_root / "build_temp" / "interface.dist"
        main_dest = deploy_root / "CafeSentinel"

        if main_source.exists():
            shutil.copytree(main_source, main_dest, dirs_exist_ok=True)

            # Rename exe
            (main_dest / "interface.exe").rename(main_dest / "CafeSentinel.exe")

            # Copy resources
            print("   Copying resources...")
            shutil.copy2(self.project_root / "config.json", main_dest / "config.json")

            # Optional icon check
            if (self.project_root / "icon.svg").exists():
                shutil.copy2(self.project_root / "icon.svg", main_dest / "icon.svg")

            # Copy Installer Script
            if (self.project_root / "install_monitor.bat").exists():
                shutil.copy2(self.project_root / "install_monitor.bat", main_dest / "install_monitor.bat")
                print("   ✓ Included install_monitor.bat")
            else:
                print("   ⚠️ install_monitor.bat not found (skipped)")

            print("   ✓ CafeSentinel/ folder created")

        # Move watchdog to its folder
        watchdog_source = self.project_root / "build_temp" / "watchdog_service.dist"
        watchdog_dest = deploy_root / "SentinelService"

        if watchdog_source.exists():
            shutil.copytree(watchdog_source, watchdog_dest, dirs_exist_ok=True)

            # Rename exe
            (watchdog_dest / "watchdog_service.exe").rename(watchdog_dest / "SentinelService.exe")

            print("   ✓ SentinelService/ folder created")

        # Clean up build_temp
        shutil.rmtree(self.project_root / "build_temp")

        print(f"\n✅ Deployment ready at: {deploy_root}\n")
        return deploy_root

    def create_launcher(self, deploy_root):
        """Create the Stealth VBS Launcher."""
        launcher_path = deploy_root / "START_SENTINEL.vbs"

        launcher_content = """Set WshShell = CreateObject("WScript.Shell")
strScriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
strExePath = strScriptDir & "\\SentinelService\\SentinelService.exe"
WshShell.Run chr(34) & strExePath & chr(34), 0
Set WshShell = Nothing
"""

        launcher_path.write_text(launcher_content)
        print(f"✅ Created: START_SENTINEL.vbs (Stealth Launcher)\n")

    def build_all(self):
        """Run complete build process."""
        print("\n╔" + "=" * 58 + "╗")
        print("║" + " " * 10 + "CafeSentinel Build System" + " " * 24 + "║")
        print("╚" + "=" * 58 + "╝\n")

        self.clean_previous_builds()

        # STEP 1: Compile Resources
        if not self.compile_resources():
            return False

        # STEP 2: Build Apps
        if not self.build_main_app():
            return False

        if not self.build_watchdog():
            return False

        deploy_root = self.organize_deployment()
        self.create_launcher(deploy_root)

        print("\n╔" + "=" * 58 + "╗")
        print("║" + " " * 15 + "BUILD SUCCESSFUL!" + " " * 26 + "║")
        print("╚" + "=" * 58 + "╝\n")

        print("📦 Deployment Structure:")
        print(f"   {deploy_root}/")
        print("   ├── CafeSentinel/")
        print("   │   ├── CafeSentinel.exe")
        print("   │   ├── install_monitor.bat (RUN THIS ONCE)")
        print("   │   ├── config.json")
        print("   │   └── (DLLs)")
        print("   ├── SentinelService/")
        print("   │   ├── SentinelService.exe")
        print("   │   └── (DLLs)")
        print("   └── START_SENTINEL.vbs (Alternate Launcher)")
        print("\n🚀 To deploy: Copy entire CafeSentinel_Deploy folder")
        print("🚀 To install: Open CafeSentinel folder -> Run install_monitor.bat as Admin\n")

        return True


def main():
    builder = SeparateFoldersBuilder()

    try:
        success = builder.build_all()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Build cancelled\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Build error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()