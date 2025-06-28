#!/usr/bin/env python3
"""
PyTorch Fix Script - Resolve DLL Import Errors
Fix lỗi "DLL load failed while importing _C" của PyTorch
"""

import subprocess
import sys
import os
import time

def print_header():
    """Print header"""
    print("🔧 PYTORCH FIX TOOL")
    print("=" * 50)
    print("🚨 Fixing: ImportError: DLL load failed while importing _C")
    print()

def uninstall_pytorch():
    """Gỡ cài đặt PyTorch hoàn toàn"""
    print("🗑️ Uninstalling corrupted PyTorch...")
    
    pytorch_packages = [
        'torch',
        'torchvision', 
        'torchaudio',
        'torch-audio',
        'torchtext'
    ]
    
    for package in pytorch_packages:
        try:
            print(f"🔄 Uninstalling {package}...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "uninstall", package, "-y"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {package} uninstalled")
            else:
                print(f"⚠️ {package} not found or already removed")
        except Exception as e:
            print(f"❌ Error uninstalling {package}: {e}")

def clear_cache():
    """Clear pip cache"""
    print("\n🧹 Clearing pip cache...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "cache", "purge"], 
                      capture_output=True)
        print("✅ Pip cache cleared")
    except:
        print("⚠️ Cache clearing failed (not critical)")

def install_cpu_pytorch():
    """Cài đặt PyTorch CPU version ổn định"""
    print("\n📦 Installing stable CPU PyTorch...")
    
    # Install CPU-only PyTorch (stable)
    cmd = [
        sys.executable, "-m", "pip", "install", 
        "torch==2.1.0+cpu", 
        "torchvision==0.16.0+cpu", 
        "torchaudio==2.1.0+cpu",
        "--index-url", "https://download.pytorch.org/whl/cpu"
    ]
    
    try:
        print("🔄 Installing CPU PyTorch...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ CPU PyTorch installed successfully!")
            return True
        else:
            print(f"❌ Installation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Installation error: {e}")
        return False

def test_pytorch():
    """Test PyTorch import"""
    print("\n🧪 Testing PyTorch import...")
    
    try:
        import torch
        print("✅ PyTorch import: OK")
        
        # Test basic operation
        x = torch.randn(3, 3)
        y = torch.matmul(x, x)
        print("✅ PyTorch operations: OK")
        
        # Check device
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🖥️ Device: {device}")
        
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Operation failed: {e}")
        return False

def install_other_deps():
    """Reinstall other dependencies"""
    print("\n📦 Reinstalling other dependencies...")
    
    deps = [
        "openai-whisper==20231117",
        "numpy==1.24.3",
        "opencv-python==4.9.0.80"
    ]
    
    for dep in deps:
        try:
            print(f"🔄 Installing {dep}...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", dep
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {dep} installed")
            else:
                print(f"⚠️ {dep} failed: {result.stderr}")
        except Exception as e:
            print(f"❌ {dep} error: {e}")

def test_app_imports():
    """Test all app imports"""
    print("\n🔍 Testing application imports...")
    
    test_modules = [
        ('torch', 'PyTorch'),
        ('whisper', 'Whisper'),
        ('cv2', 'OpenCV'),
        ('numpy', 'NumPy'),
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
    """Main fix process"""
    print_header()
    
    # Step 1: Uninstall corrupted PyTorch
    print("🔧 STEP 1: Remove Corrupted PyTorch")
    print("-" * 40)
    uninstall_pytorch()
    
    # Step 2: Clear cache
    print("\n🧹 STEP 2: Clear Cache")
    print("-" * 40)
    clear_cache()
    
    # Step 3: Install stable CPU PyTorch
    print("\n📦 STEP 3: Install Stable PyTorch")
    print("-" * 40)
    pytorch_success = install_cpu_pytorch()
    
    if not pytorch_success:
        print("\n❌ PyTorch installation failed!")
        print("💡 Try manual installation:")
        print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu")
        return
    
    # Step 4: Test PyTorch
    print("\n🧪 STEP 4: Test PyTorch")
    print("-" * 40)
    pytorch_working = test_pytorch()
    
    # Step 5: Reinstall other dependencies
    if pytorch_working:
        print("\n📦 STEP 5: Reinstall Dependencies")
        print("-" * 40)
        install_other_deps()
        
        # Step 6: Final test
        print("\n🔍 STEP 6: Final Import Test")
        print("-" * 40)
        all_working = test_app_imports()
    else:
        all_working = False
    
    # Summary
    print("\n" + "=" * 50)
    print("🎉 PYTORCH FIX COMPLETE!")
    print()
    
    if all_working:
        print("✅ All imports working correctly!")
        print("\n💡 Next Steps:")
        print("   1. Start application: python start.py")
        print("   2. Or run directly: python main_app.py")
        print("   3. App will use CPU mode (stable)")
        print("\n🔮 For GPU acceleration:")
        print("   1. Ensure NVIDIA drivers installed")
        print("   2. Install CUDA Toolkit")
        print("   3. Run: python gpu_optimize.py")
    else:
        print("❌ Some imports still failing")
        print("\n🆘 Manual troubleshooting:")
        print("   1. Restart Python/terminal")
        print("   2. Create new virtual environment")
        print("   3. pip install -r requirements.txt")
    
    print("\n🌟 PyTorch DLL error should be resolved!")

if __name__ == "__main__":
    main() 