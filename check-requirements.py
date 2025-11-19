#!/usr/bin/env python3
"""
Kraken Kouncil v4.2.1 - Dependency Checker
Verifies all required packages including GPU monitoring support.
"""

import sys
import importlib.util

# Force UTF-8 output for Windows consoles to support emojis
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

def check_dependency(package_display_name, import_name=None):
    """Check if a package is installed by trying to find its spec"""
    if import_name is None:
        import_name = package_display_name
    
    try:
        if importlib.util.find_spec(import_name) is not None:
            print(f"✅ {package_display_name:25} - Installed")
            return True
        else:
            print(f"❌ {package_display_name:25} - NOT INSTALLED")
            return False
    except Exception:
        print(f"❌ {package_display_name:25} - ERROR CHECKING")
        return False

def main():
    print("=" * 60)
    print("🐙 Kraken Kouncil v4.2.1 - Dependency Check")
    print("=" * 60)
    print()
    
    # 1. Core Requirements
    print("Core System:")
    print("-" * 60)
    
    required = [
        ("PySide6", "PySide6"),
        ("aiohttp", "aiohttp"),
        ("requests", "requests"),
    ]
    
    all_required_ok = True
    for package, import_name in required:
        if not check_dependency(package, import_name):
            all_required_ok = False
    
    print()
    
    # 2. Feature Requirements
    print("Feature Modules:")
    print("-" * 60)
    
    optional = [
        ("pyqtdarktheme", "pyqtdarktheme", "Dark Mode UI"),
        ("nvidia-ml-py", "pynvml", "GPU Monitoring (NVIDIA)"),
    ]
    
    optional_missing = []
    for package, import_name, purpose in optional:
        # Print purpose first for context
        print(f"Checking {purpose}...")
        result = check_dependency(package, import_name)
        if not result:
            optional_missing.append(package)
    
    print()
    print("=" * 60)
    
    # 3. Final Summary
    if all_required_ok:
        print("✅ Core system is ready!")
        
        if optional_missing:
            print("⚠️  Missing feature libraries:")
            for pkg in optional_missing:
                print(f"   - {pkg}")
            print("\nTo fix, run:")
            print(f"   pip install {' '.join(optional_missing)}")
            print("\n(Note: App will run without them, but features will be disabled)")
        else:
            print("🎉 FULL POWER: All features (GPU + Dark Mode) enabled!")
            
        print("\n🚀 Launch Command:")
        print("   python kraken_council_v4_2_1.py")
        return 0
    else:
        print("❌ System Halted: Critical dependencies missing.")
        print("\nPlease run setup:")
        print("   pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())