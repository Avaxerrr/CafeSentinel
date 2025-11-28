# CafeSentinel Build Script - Nested Folders Approach
# Builds two independent executables, placing SentinelService INSIDE the main app folder.
# Includes Automatic Resource Compilation.

import subprocess
import sys
import os
import shutil
from pathlib import Path


class NestedBuilder:
    def __init__(self, fast_mode=False):
        self.project_root = Path(__file__).parent
        self.dist_folder = self.project_root / "dist"
        self.fast_mode = fast_mode

    def clean_previous_builds(self):
        """Remove previous build artifacts and compiled resources."""
        print("Cleaning previous builds...")
        if self.dist_folder.exists():
            shutil.rmtree(self.dist_folder)
            print(f"Removed {self.dist_folder.name}")

        for pattern in ["*.build", "*.dist", "*.onefile-build"]:
            for folder in self.project_root.glob(pattern):
                if folder.is_dir():
                    shutil.rmtree(folder)
                    print(f"Removed {folder.name}")

        rcc_file = self.project_root / "resources_rc.py"
        if rcc_file.exists():
            rcc_file.unlink()
            print(f"Removed {rcc_file.name}")

        print("Cleanup complete.")

    def compile_resources(self):
        """Compiles the .qrc file into a Python module using pyside6-rcc."""
        print("-" * 60)
        print("Compiling Resources (Icons)")
        print("-" * 60)

        qrc_file = self.project_root / "resources.qrc"
        py_file = self.project_root / "resources_rc.py"

        if not qrc_file.exists():
            print(f"Warning: {qrc_file.name} not found. Skipping resource compilation.")
            return True

        # Wrap paths in quotes to handle spaces
        cmd = f'pyside6-rcc "{qrc_file}" -o "{py_file}"'

        try:
            subprocess.run(cmd, check=True, shell=True)
            print(f"Compiled {qrc_file.name} -> {py_file.name}")
            return True
        except subprocess.CalledProcessError:
            print("Failed to compile resources. Make sure pyside6-rcc is in your PATH.")
            return False

    def get_common_flags(self):
        """Returns flags based on Fast/Production mode."""
        flags = [sys.executable, "-m", "nuitka", "--standalone"]

        if self.fast_mode:
            # FAST MODE: No LTO, Console Enabled
            flags.append("--lto=no")
        else:
            # PROD MODE: LTO, No Console
            flags.append("--lto=yes")
            flags.append("--windows-console-mode=disable")

        return flags

    def build_main_app(self):
        """Build CafeSentinel.exe."""
        print("-" * 60)
        print(f"Building CafeSentinel.exe ({'FAST' if self.fast_mode else 'PROD'})")
        print("-" * 60)

        cmd = self.get_common_flags() + [
            "--enable-plugin=pyside6",
            f"--windows-icon-from-ico={self.project_root / 'icon.ico'}",
            "--company-name=Avaxerr",
            "--product-name=CafeSentinel",
            "--file-version=1.3.0.0",
            "--product-version=1.3.0",
            "--file-description=Internet Cafe Network Monitoring",
            "--windows-uac-admin",
            "--assume-yes-for-downloads",
            "--output-dir=build_temp",
            "interface.py"
        ]

        result = subprocess.run(cmd, cwd=self.project_root)
        if result.returncode != 0:
            print("Build failed!")
            return False
        print("CafeSentinel.exe built!")
        return True

    def build_watchdog(self):
        """Build SentinelService.exe."""
        print("-" * 60)
        print(f"Building SentinelService.exe ({'FAST' if self.fast_mode else 'PROD'})")
        print("-" * 60)

        cmd = self.get_common_flags() + [
            "--company-name=Avaxerrr",
            "--product-name=SentinelService",
            "--file-version=1.3.0.0",
            "--product-version=1.3.0",
            "--file-description=SentinelService",
            "--windows-uac-admin",
            "--assume-yes-for-downloads",
            "--output-dir=build_temp",
            "watchdog_service.py"
        ]

        result = subprocess.run(cmd, cwd=self.project_root)
        if result.returncode != 0:
            print("Build failed!")
            return False
        print("SentinelService.exe built!")
        return True

    def organize_deployment(self):
        """Organize builds into nested folders."""
        print("Creating deployment structure...")

        deploy_root = self.dist_folder / "CafeSentinelDeploy"
        deploy_root.mkdir(parents=True, exist_ok=True)

        # 1. Move Main App to CafeSentinel folder
        main_source = self.project_root / "build_temp" / "interface.dist"
        main_dest = deploy_root / "CafeSentinel"

        if main_source.exists():
            shutil.copytree(main_source, main_dest, dirs_exist_ok=True)
            (main_dest / "interface.exe").rename(main_dest / "CafeSentinel.exe")

            print("Copying resources...")
            shutil.copy2(self.project_root / "config.json", main_dest / "config.json")

            if (self.project_root / "icon.svg").exists():
                shutil.copy2(self.project_root / "icon.svg", main_dest / "icon.svg")

            if (self.project_root / "install_monitor.bat").exists():
                shutil.copy2(self.project_root / "install_monitor.bat", main_dest / "install_monitor.bat")
                print("Included install_monitor.bat")

            print("CafeSentinel folder created")

            # 2. Move Watchdog INSIDE the Main App folder (Nested)
            watchdog_source = self.project_root / "build_temp" / "watchdog_service.dist"
            watchdog_dest = main_dest / "SentinelService"

            if watchdog_source.exists():
                shutil.copytree(watchdog_source, watchdog_dest, dirs_exist_ok=True)
                (watchdog_dest / "watchdog_service.exe").rename(watchdog_dest / "SentinelService.exe")
                print("SentinelService subfolder created")

        shutil.rmtree(self.project_root / "build_temp")

        print(f"Deployment ready at: {deploy_root}")
        return deploy_root

    def build_all(self):
        """Run complete build process."""
        print("*" * 58)
        print("*" + " " * 10 + "CafeSentinel Build System" + " " * 24 + "*")
        print("*" * 58)

        self.clean_previous_builds()

        if not self.compile_resources():
            return False

        if not self.build_main_app():
            return False

        if not self.build_watchdog():
            return False

        deploy_root = self.organize_deployment()

        print("*" * 58)
        print("*" + " " * 15 + "BUILD SUCCESSFUL!" + " " * 26 + "*")
        print("*" * 58)
        print(f"Mode: {'⚡ FAST (Debug)' if self.fast_mode else '🐢 PRODUCTION (Optimized)'}")
        print("Deployment Structure:")
        print(f"{deploy_root}")
        print(" └── CafeSentinel")
        print("      ├── CafeSentinel.exe")
        print("      ├── config.json")
        print("      ├── install_monitor.bat")
        print("      └── SentinelService")
        print("           └── SentinelService.exe")
        print("\nTo deploy: Copy entire 'CafeSentinelDeploy' folder")
        print("To install: Open CafeSentinel folder -> Run install_monitor.bat as Admin")

        return True


def main():
    print("\nSelect Build Mode:")
    print("1. ⚡ Fast Build (No LTO, Console Visible) - For Testing")
    print("2. 🐢 Production Build (LTO, No Console) - For Deployment")

    choice = input("\nEnter choice (1 or 2): ").strip()

    if choice == "1":
        fast_mode = True
    elif choice == "2":
        fast_mode = False
    else:
        print("Invalid choice. Defaulting to Fast Build.")
        fast_mode = True

    builder = NestedBuilder(fast_mode=fast_mode)
    try:
        success = builder.build_all()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nBuild cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\nBuild error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()