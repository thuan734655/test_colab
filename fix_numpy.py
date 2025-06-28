#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Video Editor - NumPy Compatibility Fix
Giải quyết vấn đề NumPy 2.x incompatibility với OpenCV và các thư viện khác
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Chạy command với description"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            return True
        else:
            print(f"❌ {description} - FAILED")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def fix_numpy_compatibility():
    """Fix NumPy compatibility issues"""
    print("🚀 AI Video Editor - NumPy Compatibility Fix")
    print("=" * 60)
    
    print("📋 Detected Issue: NumPy 2.x incompatibility")
    print("💡 Solution: Downgrade NumPy to 1.24.3 for compatibility")
    
    steps = [
        # Step 1: Uninstall current NumPy
        ("pip uninstall numpy -y", "Uninstalling current NumPy"),
        
        # Step 2: Install specific NumPy version
        ("pip install numpy==1.24.3", "Installing NumPy 1.24.3"),
        
        # Step 3: Reinstall OpenCV with compatible NumPy
        ("pip uninstall opencv-python -y", "Uninstalling OpenCV"),
        ("pip install opencv-python==4.9.0.80", "Installing compatible OpenCV"),
        
        # Step 4: Reinstall other packages
        ("pip install -r requirements.txt", "Reinstalling all dependencies"),
    ]
    
    failed_steps = []
    
    for cmd, description in steps:
        if not run_command(cmd, description):
            failed_steps.append(description)
    
    print("\n" + "=" * 60)
    
    if failed_steps:
        print("❌ Some steps failed:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\n💡 Try manual fix:")
        print("pip uninstall numpy opencv-python -y")
        print("pip install numpy==1.24.3")
        print("pip install opencv-python==4.9.0.80")
        print("pip install -r requirements.txt")
        return False
    else:
        print("✅ NumPy compatibility fixed successfully!")
        print("\n🎉 You can now run: python start.py")
        return True

def check_numpy_version():
    """Kiểm tra NumPy version hiện tại"""
    try:
        import numpy as np
        version = np.__version__
        print(f"📊 Current NumPy version: {version}")
        
        major_version = int(version.split('.')[0])
        if major_version >= 2:
            print("⚠️ NumPy 2.x detected - may cause compatibility issues")
            return False
        else:
            print("✅ NumPy 1.x - should be compatible")
            return True
    except ImportError:
        print("❌ NumPy not installed")
        return False

def test_imports():
    """Test critical imports"""
    print("\n🧪 Testing critical imports...")
    
    test_modules = [
        ('numpy', 'NumPy'),
        ('cv2', 'OpenCV'), 
        ('torch', 'PyTorch'),
        ('whisper', 'Whisper'),
        ('edge_tts', 'Edge TTS')
    ]
    
    failed_imports = []
    
    for module, name in test_modules:
        try:
            __import__(module)
            print(f"✅ {name} - OK")
        except Exception as e:
            print(f"❌ {name} - FAILED: {e}")
            failed_imports.append(name)
    
    return len(failed_imports) == 0

def main():
    """Main function"""
    print("🔍 Checking current NumPy status...")
    
    # Check NumPy version
    numpy_ok = check_numpy_version()
    
    # Test imports
    imports_ok = test_imports()
    
    if numpy_ok and imports_ok:
        print("\n🎉 All checks passed! NumPy compatibility is OK.")
        print("✅ You can run: python start.py")
        return True
    
    print(f"\n🔧 Issues detected. Starting fix process...")
    
    # Ask user confirmation
    response = input("\n❓ Do you want to fix NumPy compatibility? (y/n): ").lower()
    
    if response in ['y', 'yes']:
        success = fix_numpy_compatibility()
        
        if success:
            print("\n🧪 Testing after fix...")
            if test_imports():
                print("\n🎉 FIX SUCCESSFUL! All modules working.")
                print("✅ Run: python start.py")
            else:
                print("\n❌ Some imports still failing. Try manual fix.")
        
        return success
    else:
        print("\n💡 Manual fix commands:")
        print("pip uninstall numpy opencv-python -y")
        print("pip install numpy==1.24.3 opencv-python==4.9.0.80")
        print("pip install -r requirements.txt")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n👋 Fix cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1) 