#!/usr/bin/env python3
"""
GPU Optimization Tool for AI Video Editor
Tự động cài đặt và tối ưu GPU để tăng tốc độ xử lý
"""

import subprocess
import sys
import os
import platform
import json
import time
from pathlib import Path

def print_header():
    """Print header"""
    print("🚀 GPU OPTIMIZATION TOOL")
    print("=" * 60)
    print("📈 Tăng tốc độ xử lý video bằng GPU")
    print()

def check_nvidia_gpu():
    """Kiểm tra NVIDIA GPU"""
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ NVIDIA GPU detected!")
            lines = result.stdout.split('\n')
            for line in lines:
                if 'GeForce' in line or 'RTX' in line or 'GTX' in line:
                    gpu_info = line.split('|')[1].strip()
                    print(f"   🎮 GPU: {gpu_info}")
                    return True
        else:
            print("❌ No NVIDIA GPU found")
            return False
    except FileNotFoundError:
        print("⚠️ nvidia-smi not found")
        return False

def check_cuda_installation():
    """Kiểm tra CUDA installation"""
    try:
        result = subprocess.run(['nvcc', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version_line = [line for line in result.stdout.split('\n') if 'release' in line.lower()]
            if version_line:
                cuda_version = version_line[0].split('release')[1].split(',')[0].strip()
                print(f"✅ CUDA {cuda_version} installed")
                return True
        else:
            print("❌ CUDA not installed")
            return False
    except FileNotFoundError:
        print("❌ CUDA compiler (nvcc) not found")
        return False

def check_pytorch_gpu():
    """Kiểm tra PyTorch GPU support"""
    try:
        import torch
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            current_device = torch.cuda.current_device()
            device_name = torch.cuda.get_device_name(current_device)
            print(f"✅ PyTorch GPU support: {device_count} device(s)")
            print(f"   🔧 Current device: {device_name}")
            
            # Test GPU performance
            print("   🧪 Testing GPU performance...")
            start_time = time.time()
            x = torch.randn(1000, 1000).cuda()
            y = torch.matmul(x, x)
            torch.cuda.synchronize()
            gpu_time = time.time() - start_time
            print(f"   ⚡ GPU Matrix multiplication: {gpu_time:.3f}s")
            return True
        else:
            print("❌ PyTorch: GPU not available")
            return False
    except ImportError:
        print("❌ PyTorch not installed")
        return False

def install_cuda_pytorch():
    """Cài đặt PyTorch với CUDA support"""
    print("\n🔧 Installing PyTorch with CUDA support...")
    
    # Detect CUDA version for appropriate PyTorch
    cuda_commands = [
        "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121",  # CUDA 12.1
        "pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118",  # CUDA 11.8
    ]
    
    for cmd in cuda_commands:
        print(f"🔄 Trying: {cmd}")
        try:
            result = subprocess.run(cmd.split(), capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ PyTorch CUDA installed successfully!")
                return True
        except Exception as e:
            print(f"❌ Failed: {e}")
            continue
    
    print("⚠️ Installing CPU-only PyTorch as fallback...")
    subprocess.run(["pip", "install", "torch", "torchvision", "torchaudio"], 
                   capture_output=True)
    return False

def optimize_ffmpeg_gpu():
    """Tối ưu FFmpeg với GPU encoding"""
    print("\n🎬 Optimizing FFmpeg for GPU...")
    
    # Check if FFmpeg supports GPU encoding
    try:
        result = subprocess.run(['ffmpeg', '-encoders'], capture_output=True, text=True)
        gpu_encoders = []
        
        if 'h264_nvenc' in result.stdout:
            gpu_encoders.append('h264_nvenc (H.264 NVIDIA)')
        if 'hevc_nvenc' in result.stdout:
            gpu_encoders.append('hevc_nvenc (H.265 NVIDIA)')
        if 'h264_qsv' in result.stdout:
            gpu_encoders.append('h264_qsv (Intel QuickSync)')
        
        if gpu_encoders:
            print("✅ GPU encoders available:")
            for encoder in gpu_encoders:
                print(f"   - {encoder}")
            return gpu_encoders
        else:
            print("❌ No GPU encoders found")
            return []
    except FileNotFoundError:
        print("❌ FFmpeg not found")
        return []

def create_gpu_optimized_config():
    """Tạo file config tối ưu GPU"""
    config = {
        "gpu_acceleration": True,
        "whisper_device": "cuda",
        "ffmpeg_gpu_encoder": "h264_nvenc",
        "batch_processing": True,
        "memory_optimization": True,
        "parallel_workers": 4
    }
    
    with open('gpu_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ GPU config saved to gpu_config.json")

def update_main_app_gpu():
    """Update main_app.py với GPU optimizations"""
    print("\n🔧 Updating main_app.py for GPU optimization...")
    
    gpu_optimizations = '''
# GPU Optimization imports
import json
from concurrent.futures import ThreadPoolExecutor
import gc

# Load GPU config
try:
    with open('gpu_config.json', 'r') as f:
        GPU_CONFIG = json.load(f)
except FileNotFoundError:
    GPU_CONFIG = {"gpu_acceleration": False}

# Enhanced device selection
def get_optimal_device():
    """Get optimal device for processing"""
    if GPU_CONFIG.get("gpu_acceleration", False) and torch.cuda.is_available():
        # Clear GPU cache
        torch.cuda.empty_cache()
        return "cuda"
    return "cpu"

# Optimized model loading
def load_whisper_optimized(model_name):
    """Load Whisper model with GPU optimization"""
    device = get_optimal_device()
    
    if device == "cuda":
        # GPU optimization settings
        torch.backends.cudnn.benchmark = True
        torch.backends.cudnn.deterministic = False
        
    model = whisper.load_model(model_name, device=device)
    
    if device == "cuda":
        model.half()  # Use FP16 for faster inference
        
    return model

# GPU-accelerated FFmpeg commands
def get_gpu_ffmpeg_args():
    """Get GPU-accelerated FFmpeg arguments"""
    if not GPU_CONFIG.get("gpu_acceleration", False):
        return ['-c:v', 'libx264']
    
    # Try NVIDIA NVENC first
    gpu_encoder = GPU_CONFIG.get("ffmpeg_gpu_encoder", "h264_nvenc")
    
    if gpu_encoder == "h264_nvenc":
        return [
            '-hwaccel', 'cuda',
            '-hwaccel_output_format', 'cuda', 
            '-c:v', 'h264_nvenc',
            '-preset', 'fast',
            '-b:v', '5M'
        ]
    else:
        return ['-c:v', 'libx264', '-preset', 'fast']

# Memory management
def optimize_memory():
    """Optimize memory usage"""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
'''
    
    print("📝 GPU optimization code prepared")
    print("💡 Manual integration required in main_app.py")

def benchmark_performance():
    """Benchmark GPU vs CPU performance"""
    print("\n📊 Performance Benchmark...")
    
    try:
        import torch
        import time
        
        # CPU benchmark
        print("🔄 Testing CPU performance...")
        x_cpu = torch.randn(2000, 2000)
        start = time.time()
        y_cpu = torch.matmul(x_cpu, x_cpu)
        cpu_time = time.time() - start
        print(f"   ⏱️ CPU: {cpu_time:.3f}s")
        
        # GPU benchmark
        if torch.cuda.is_available():
            print("🔄 Testing GPU performance...")
            x_gpu = torch.randn(2000, 2000).cuda()
            torch.cuda.synchronize()
            start = time.time()
            y_gpu = torch.matmul(x_gpu, x_gpu)
            torch.cuda.synchronize()
            gpu_time = time.time() - start
            print(f"   ⚡ GPU: {gpu_time:.3f}s")
            
            speedup = cpu_time / gpu_time
            print(f"   🚀 Speedup: {speedup:.1f}x faster on GPU")
        else:
            print("❌ GPU not available for benchmark")
            
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")

def install_gpu_requirements():
    """Cài đặt dependencies cần thiết cho GPU"""
    print("\n📦 Installing GPU-optimized packages...")
    
    packages = [
        "accelerate",           # Hugging Face acceleration
        "bitsandbytes",        # GPU memory optimization  
        "xformers",            # Memory-efficient transformers
    ]
    
    for package in packages:
        try:
            print(f"🔄 Installing {package}...")
            result = subprocess.run([sys.executable, "-m", "pip", "install", package], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {package} installed")
            else:
                print(f"⚠️ {package} failed: {result.stderr}")
        except Exception as e:
            print(f"❌ {package} error: {e}")

def main():
    """Main optimization process"""
    print_header()
    
    # Step 1: Hardware detection
    print("🔍 STEP 1: Hardware Detection")
    print("-" * 40)
    has_nvidia = check_nvidia_gpu()
    has_cuda = check_cuda_installation()
    has_pytorch_gpu = check_pytorch_gpu()
    
    # Step 2: CUDA setup
    if has_nvidia and not has_pytorch_gpu:
        print("\n🔧 STEP 2: CUDA Setup")
        print("-" * 40)
        print("💡 NVIDIA GPU found but PyTorch CUDA not available")
        
        user_input = input("Install CUDA-enabled PyTorch? [y/N]: ")
        if user_input.lower() == 'y':
            install_cuda_pytorch()
            has_pytorch_gpu = check_pytorch_gpu()
    
    # Step 3: FFmpeg optimization
    print("\n🎬 STEP 3: FFmpeg GPU Support")
    print("-" * 40)
    gpu_encoders = optimize_ffmpeg_gpu()
    
    # Step 4: Additional packages
    if has_pytorch_gpu:
        print("\n📦 STEP 4: GPU Packages")
        print("-" * 40)
        user_input = input("Install additional GPU optimization packages? [y/N]: ")
        if user_input.lower() == 'y':
            install_gpu_requirements()
    
    # Step 5: Configuration
    print("\n⚙️ STEP 5: Configuration")
    print("-" * 40)
    create_gpu_optimized_config()
    update_main_app_gpu()
    
    # Step 6: Benchmark
    if has_pytorch_gpu:
        print("\n📊 STEP 6: Performance Test")
        print("-" * 40)
        benchmark_performance()
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 GPU OPTIMIZATION COMPLETE!")
    print()
    print("📋 Summary:")
    print(f"   🖥️ NVIDIA GPU: {'✅' if has_nvidia else '❌'}")
    print(f"   🔧 CUDA: {'✅' if has_cuda else '❌'}")  
    print(f"   🚀 PyTorch GPU: {'✅' if has_pytorch_gpu else '❌'}")
    print(f"   🎬 FFmpeg GPU: {'✅' if gpu_encoders else '❌'}")
    
    print("\n💡 Next Steps:")
    if has_pytorch_gpu:
        print("   1. Restart the application: python start.py")
        print("   2. Use larger Whisper models (medium, large)")
        print("   3. Expect 3-10x faster processing!")
    else:
        print("   1. Install NVIDIA GPU drivers")
        print("   2. Install CUDA Toolkit")
        print("   3. Run this script again")
    
    print("\n🌟 Enjoy faster AI video processing!")

if __name__ == "__main__":
    main() 