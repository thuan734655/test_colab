#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Video Editor - Startup Script
Kiểm tra môi trường và khởi chạy ứng dụng
"""

import os
import sys
import subprocess
import platform
import importlib
import logging

def check_python_version():
    """Kiểm tra phiên bản Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Error: Python 3.8+ is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
    return True

def check_dependencies():
    """Kiểm tra các dependencies cần thiết"""
    required_packages = [
        'flask',
        'torch', 
        'whisper',
        'edge_tts',
        'cv2'  # opencv-python
    ]
    
    missing_packages = []
    numpy_error = False
    
    for package in required_packages:
        try:
            if package == 'cv2':
                importlib.import_module('cv2')
            else:
                importlib.import_module(package)
            print(f"✅ {package} - OK")
        except ImportError as e:
            print(f"❌ {package} - Missing")
            missing_packages.append(package)
        except Exception as e:
            if "_ARRAY_API not found" in str(e) or "NumPy" in str(e):
                print(f"❌ {package} - NumPy Compatibility Error")
                numpy_error = True
            else:
                print(f"❌ {package} - Error: {e}")
                missing_packages.append(package)
    
    if numpy_error:
        print(f"\n🚨 NUMPY COMPATIBILITY ISSUE DETECTED!")
        print("💡 Quick fix: Run the NumPy fix script")
        print("   python fix_numpy.py")
        print("\n🔧 Or manual fix:")
        print("   pip uninstall numpy opencv-python -y")
        print("   pip install numpy==1.24.3 opencv-python==4.9.0.80")
        print("   pip install -r requirements.txt")
        return False
    
    if missing_packages:
        print(f"\n📦 Missing packages: {missing_packages}")
        print("💡 Run: pip install -r requirements.txt")
        return False
    
    return True

def check_ffmpeg():
    """Kiểm tra FFmpeg"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ FFmpeg - OK")
            return True
        else:
            print("❌ FFmpeg - Error")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ FFmpeg - Not found")
        print("💡 Please install FFmpeg:")
        if platform.system() == "Windows":
            print("   - Download from https://ffmpeg.org/download.html")
            print("   - Add to PATH")
        elif platform.system() == "Darwin":  # macOS
            print("   - brew install ffmpeg")
        else:  # Linux
            print("   - sudo apt install ffmpeg")
        return False

def check_gpu():
    """Kiểm tra GPU"""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print(f"✅ GPU: {gpu_name}")
            return True
        else:
            print("⚠️ GPU: CUDA not available (will use CPU)")
            return True  # Not critical error
    except ImportError:
        print("⚠️ GPU: Cannot check (torch not available)")
        return True

def create_directories():
    """Tạo các thư mục cần thiết"""
    directories = ['uploads', 'outputs', 'temp']
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"📁 Created directory: {directory}")
        else:
            print(f"✅ Directory exists: {directory}")

def main():
    """Main startup function"""
    print("🚀 AI Video Editor - Startup Check")
    print("=" * 50)
    
    # Perform checks
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies), 
        ("FFmpeg", check_ffmpeg),
        ("GPU", check_gpu)
    ]
    
    failed_checks = []
    
    for check_name, check_func in checks:
        print(f"\n🔍 Checking {check_name}...")
        if not check_func():
            failed_checks.append(check_name)
    
    print(f"\n📁 Creating directories...")
    create_directories()
    
    print("\n" + "=" * 50)
    
    if failed_checks:
        print(f"❌ Failed checks: {failed_checks}")
        print("Please fix the issues above before starting the application.")
        return False
    else:
        print("✅ All checks passed!")
        print("\n🎬 Starting AI Video Editor...")
        
        try:
            # Import and run the main app
            from main_app import app, logger
            
            print("\n🌐 Server starting on http://localhost:5000")
            print("💡 Tips:")
            print("   - Use Chrome/Firefox for best experience")
            print("   - Ensure stable internet for model downloads")
            print("   - GPU will be used if available")
            print("\n🔧 Press Ctrl+C to stop the server")
            print("=" * 50)
            
            app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
            
        except KeyboardInterrupt:
            print("\n👋 Shutting down AI Video Editor...")
            return True
        except Exception as e:
            print(f"\n❌ Error starting application: {e}")
            return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 