"""
CafeSentinel Unified Build Script
Builds both executables with shared dependencies to avoid conflicts.
"""
import subprocess
import sys
import os
import shutil
from pathlib import Path


class UnifiedBuilder:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.dist_folder = self.project_root / "dist_unified"

    def clean_previous_builds(self):
        """Remove previous build artifacts."""
        print("🧹 Cleaning previous builds...")

        if self.dist_folder.exists():
            shutil.rmtree(self.dist_folder)
            print(f"   Removed: {self.dist_folder.name}")

        # Clean Nuitka cache folders
        for pattern in ["*.build", "*.dist", "*.onefile-build"]:
            for folder in self.project_root.glob(pattern):
                if folder.is_dir():
                    shutil.rmtree(folder)
                    print(f"   Removed: {folder.name}")

        print("✅ Cleanup complete.\n")

    def build_main_app(self):
        """Build the main GUI application."""
        print("=" * 60)
        print("📦 Building CafeSentinel.exe (Main Application)")
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
            "--copyright=Copyright 2025",
            "--windows-uac-admin",
            "--assume-yes-for-downloads",
            f"--output-dir={self.dist_folder}",
            "interface.py"
        ]

        print("Compiling main application...\n")
        result = subprocess.run(cmd, cwd=self.project_root)

        if result.returncode != 0:
            print("\n❌ Build failed for CafeSentinel.exe\n")
            return False

        print("\n✅ Main app built successfully!\n")
        return True

    def build_watchdog(self):
        """Build the watchdog service."""
        print("=" * 60)
        print("📦 Building SentinelService.exe (Watchdog)")
        print("=" * 60)

        cmd = [
            sys.executable, "-m", "nuitka",
            "--standalone",
            # Keep console for watchdog messages
            "--company-name=CafeSentinel",
            "--product-name=SentinelService",
            "--file-version=1.0.0.0",
            "--product-version=1.0.0",
            "--file-description=CafeSentinel Watchdog Service",
            "--copyright=Copyright 2025",
            "--windows-uac-admin",
            "--assume-yes-for-downloads",
            f"--output-dir={self.dist_folder}",
            "watchdog_service.py"
        ]

        print("Compiling watchdog service...\n")
        result = subprocess.run(cmd, cwd=self.project_root)

        if result.returncode != 0:
            print("\n❌ Build failed for SentinelService.exe\n")
            return False

        print("\n✅ Watchdog built successfully!\n")
        return True

    def merge_builds(self):
        """Merge both builds into a single deployment folder."""
        print("🔗 Merging executables into single folder...")

        deploy_folder = self.dist_folder / "CafeSentinel_Deploy"

        # Remove old deployment folder if it exists
        if deploy_folder.exists():
            shutil.rmtree(deploy_folder)

        deploy_folder.mkdir(exist_ok=True)

        # Copy main app distribution (all files)
        main_dist = self.dist_folder / "interface.dist"
        if main_dist.exists():
            print("   Copying main app files...")
            for item in main_dist.iterdir():
                if item.is_file():
                    shutil.copy2(item, deploy_folder / item.name)
                elif item.is_dir():
                    shutil.copytree(item, deploy_folder / item.name, dirs_exist_ok=True)

        # Copy watchdog executable and its unique dependencies
        watchdog_dist = self.dist_folder / "watchdog_service.dist"
        if watchdog_dist.exists():
            print("   Copying watchdog files...")
            for item in watchdog_dist.iterdir():
                dest_path = deploy_folder / item.name

                # Always copy the watchdog exe
                if item.name.lower() == "watchdog_service.exe":
                    shutil.copy2(item, deploy_folder / "SentinelService.exe")
                    print(f"      • watchdog_service.exe → SentinelService.exe")
                # For other files, only copy if they don't exist (avoid overwriting shared DLLs)
                elif not dest_path.exists():
                    if item.is_file():
                        shutil.copy2(item, dest_path)
                    elif item.is_dir():
                        shutil.copytree(item, dest_path, dirs_exist_ok=True)

        # Rename main exe
        old_main = deploy_folder / "interface.exe"
        new_main = deploy_folder / "CafeSentinel.exe"
        if old_main.exists():
            old_main.rename(new_main)
            print("   Renamed: interface.exe → CafeSentinel.exe")

        print(f"\n✅ Merged into: {deploy_folder}\n")
        return deploy_folder

    def copy_resources(self, deploy_folder):
        """Copy necessary resources."""
        print("📋 Copying resources...")

        resources = ["config.json", "icon.svg", "icon.ico"]

        for resource in resources:
            src = self.project_root / resource
            if src.exists():
                shutil.copy2(src, deploy_folder / resource)
                print(f"   Copied: {resource}")

        print("✅ Resources copied.\n")

    def build_all(self):
        """Run the complete build process."""
        print("\n")
        print("╔" + "=" * 58 + "╗")
        print("║" + " " * 8 + "CafeSentinel Unified Build System" + " " * 17 + "║")
        print("╚" + "=" * 58 + "╝")
        print("\n")

        # Step 1: Clean
        self.clean_previous_builds()

        # Step 2: Build Main App
        if not self.build_main_app():
            print("❌ Build process aborted.")
            return False

        # Step 3: Build Watchdog
        if not self.build_watchdog():
            print("❌ Build process aborted.")
            return False

        # Step 4: Merge into single folder
        deploy_folder = self.merge_builds()

        # Step 5: Copy resources
        self.copy_resources(deploy_folder)

        # Final Summary
        print("\n")
        print("╔" + "=" * 58 + "╗")
        print("║" + " " * 15 + "BUILD SUCCESSFUL!" + " " * 26 + "║")
        print("╚" + "=" * 58 + "╝")
        print("\n")
        print("📁 Deployment folder:", deploy_folder)
        print("\n📦 Contents:")
        print("   • CafeSentinel.exe (Main GUI)")
        print("   • SentinelService.exe (Watchdog)")
        print("   • Shared DLLs and dependencies")
        print("   • config.json, icons")
        print("\n🚀 To run: Execute SentinelService.exe")
        print("\n💡 Tip: Copy the entire CafeSentinel_Deploy folder to deploy")
        print("\n")

        return True


def main():
    builder = UnifiedBuilder()

    try:
        success = builder.build_all()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Build cancelled by user.\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Build error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
