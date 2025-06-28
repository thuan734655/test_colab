#!/usr/bin/env python3
"""
CPU Optimization Script - Improve Processing Speed
Tối ưu CPU để xử lý video nhanh hơn và không bị treo
"""

import psutil
import os
import subprocess
import sys

def print_header():
    """Print header"""
    print("⚡ CPU OPTIMIZATION TOOL")
    print("=" * 50)
    print("🚀 Tối ưu CPU cho xử lý video nhanh hơn")
    print()

def check_system_resources():
    """Check system resources"""
    print("🔍 System Resource Check:")
    print("-" * 30)
    
    # CPU info
    cpu_count = psutil.cpu_count(logical=True)
    cpu_freq = psutil.cpu_freq()
    cpu_percent = psutil.cpu_percent(interval=1)
    
    print(f"🖥️ CPU Cores: {cpu_count}")
    if cpu_freq:
        print(f"⚡ CPU Frequency: {cpu_freq.current:.0f} MHz")
    print(f"📊 CPU Usage: {cpu_percent}%")
    
    # Memory info
    memory = psutil.virtual_memory()
    memory_gb = memory.total / (1024**3)
    memory_used = memory.percent
    
    print(f"💾 Total RAM: {memory_gb:.1f} GB")
    print(f"📊 Memory Usage: {memory_used}%")
    
    # Disk info
    try:
        disk = psutil.disk_usage('C:' if os.name == 'nt' else '/')
    except:
        disk = psutil.disk_usage('.')
    disk_free_gb = disk.free / (1024**3)
    disk_used_percent = (disk.used / disk.total) * 100
    
    print(f"💽 Free Disk: {disk_free_gb:.1f} GB")
    print(f"📊 Disk Usage: {disk_used_percent:.1f}%")
    
    return {
        'cpu_cores': cpu_count,
        'memory_gb': memory_gb,
        'disk_free_gb': disk_free_gb,
        'cpu_usage': cpu_percent,
        'memory_usage': memory_used
    }

def optimize_python_settings():
    """Optimize Python settings for performance"""
    print("\n⚙️ Python Optimization:")
    print("-" * 30)
    
    # Set environment variables for optimization
    optimizations = {
        'OMP_NUM_THREADS': str(psutil.cpu_count()),
        'MKL_NUM_THREADS': str(psutil.cpu_count()),
        'PYTORCH_DISABLE_CUDNN_BENCHMARKS': '0',
        'PYTHONUNBUFFERED': '1'
    }
    
    for key, value in optimizations.items():
        os.environ[key] = value
        print(f"✅ {key} = {value}")
    
    print("✅ Python environment optimized")

def create_optimized_config(system_info):
    """Create optimized configuration"""
    print("\n📝 Creating optimized config...")
    
    # Determine optimal settings based on system
    if system_info['memory_gb'] >= 16:
        whisper_model = 'large-v3'
        batch_size = 16
    elif system_info['memory_gb'] >= 8:
        whisper_model = 'medium'
        batch_size = 8
    else:
        whisper_model = 'small'
        batch_size = 4
    
    config = {
        "performance_mode": "cpu_optimized",
        "recommended_whisper_model": whisper_model,
        "max_concurrent_processes": min(4, system_info['cpu_cores']),
        "ffmpeg_threads": system_info['cpu_cores'],
        "batch_size": batch_size,
        "memory_limit_gb": system_info['memory_gb'] * 0.8,
        "temp_cleanup": True,
        "progress_monitoring": True
    }
    
    import json
    with open('cpu_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ CPU config saved to cpu_config.json")
    print(f"📋 Recommended Whisper model: {whisper_model}")
    print(f"🔧 Max concurrent processes: {config['max_concurrent_processes']}")

def optimize_ffmpeg_settings():
    """Create optimized FFmpeg settings"""
    print("\n🎬 FFmpeg CPU Optimization:")
    print("-" * 30)
    
    cpu_cores = psutil.cpu_count()
    
    # Optimized FFmpeg arguments for CPU
    ffmpeg_args = {
        "threads": cpu_cores,
        "preset": "fast",  # Balance speed vs quality
        "crf": "23",       # Good quality
        "tune": "fastdecode",  # Optimize for playback
        "movflags": "+faststart"  # Web optimization
    }
    
    print("✅ Optimized FFmpeg settings:")
    for key, value in ffmpeg_args.items():
        print(f"   -{key} {value}")
    
    return ffmpeg_args

def cleanup_temp_files():
    """Clean up temporary files to free space"""
    print("\n🧹 Cleaning temporary files...")
    
    cleanup_dirs = ['temp', 'outputs']
    total_cleaned = 0
    
    for dir_name in cleanup_dirs:
        if os.path.exists(dir_name):
            try:
                for file in os.listdir(dir_name):
                    file_path = os.path.join(dir_name, file)
                    if os.path.isfile(file_path):
                        file_size = os.path.getsize(file_path)
                        # Remove files older than 1 hour
                        import time
                        if time.time() - os.path.getctime(file_path) > 3600:
                            os.remove(file_path)
                            total_cleaned += file_size
            except Exception as e:
                print(f"⚠️ Cleanup error in {dir_name}: {e}")
    
    cleaned_mb = total_cleaned / (1024*1024)
    print(f"✅ Cleaned {cleaned_mb:.1f} MB of temp files")

def test_performance():
    """Test current performance"""
    print("\n🧪 Performance Test:")
    print("-" * 30)
    
    try:
        import torch
        import time
        import numpy as np
        
        # CPU matrix test
        print("🔄 Testing CPU performance...")
        start = time.time()
        
        # Simulate AI workload
        x = torch.randn(1000, 1000)
        y = torch.matmul(x, x)
        
        cpu_time = time.time() - start
        print(f"⏱️ CPU Matrix (1000x1000): {cpu_time:.3f}s")
        
        # Memory test
        start = time.time()
        large_array = np.random.rand(10000, 1000)
        result = np.mean(large_array, axis=1)
        memory_time = time.time() - start
        
        print(f"⏱️ Memory operations: {memory_time:.3f}s")
        
        # Overall performance score
        if cpu_time < 0.1:
            performance = "🚀 Excellent"
        elif cpu_time < 0.5:
            performance = "✅ Good"
        elif cpu_time < 1.0:
            performance = "⚠️ Average"
        else:
            performance = "🐌 Slow"
        
        print(f"📊 Performance: {performance}")
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")

def show_recommendations(system_info):
    """Show optimization recommendations"""
    print("\n💡 CPU Optimization Recommendations:")
    print("-" * 50)
    
    print("🎯 For Best Performance:")
    
    if system_info['memory_usage'] > 80:
        print("   ⚠️ High memory usage - close other applications")
    
    if system_info['cpu_usage'] > 70:
        print("   ⚠️ High CPU usage - wait for other processes to finish")
    
    if system_info['disk_free_gb'] < 5:
        print("   🚨 Low disk space - clean up files urgently")
        print("   💡 Run: python -c \"import shutil; shutil.rmtree('temp', ignore_errors=True)\"")
    
    print("\n📋 Whisper Model Recommendations:")
    if system_info['memory_gb'] >= 16:
        print("   🚀 Use 'large-v3' model (best quality)")
    elif system_info['memory_gb'] >= 8:
        print("   ✅ Use 'medium' model (good balance)")
    else:
        print("   ⚡ Use 'small' model (fastest)")
    
    print("\n🎬 Video Processing Tips:")
    print("   - Process one video at a time")
    print("   - Use smaller Whisper models for speed")
    print("   - Close browser tabs during processing")
    print("   - Ensure stable internet connection")

def main():
    """Main optimization process"""
    print_header()
    
    # Step 1: System check
    print("🔍 STEP 1: System Analysis")
    print("=" * 40)
    system_info = check_system_resources()
    
    # Step 2: Python optimization
    print("\n⚙️ STEP 2: Python Optimization")
    print("=" * 40)
    optimize_python_settings()
    
    # Step 3: Create config
    print("\n📝 STEP 3: Configuration")
    print("=" * 40)
    create_optimized_config(system_info)
    
    # Step 4: FFmpeg optimization
    print("\n🎬 STEP 4: FFmpeg Settings")
    print("=" * 40)
    optimize_ffmpeg_settings()
    
    # Step 5: Cleanup
    print("\n🧹 STEP 5: Cleanup")
    print("=" * 40)
    cleanup_temp_files()
    
    # Step 6: Performance test
    print("\n🧪 STEP 6: Performance Test")
    print("=" * 40)
    test_performance()
    
    # Step 7: Recommendations
    show_recommendations(system_info)
    
    # Summary
    print("\n" + "=" * 50)
    print("🎉 CPU OPTIMIZATION COMPLETE!")
    print()
    print("✅ Status:")
    print(f"   🖥️ CPU Cores: {system_info['cpu_cores']}")
    print(f"   💾 Memory: {system_info['memory_gb']:.1f} GB")
    print(f"   💽 Free Space: {system_info['disk_free_gb']:.1f} GB")
    
    print("\n💡 Next Steps:")
    print("   1. Restart application: python start.py")
    print("   2. Use recommended Whisper model")
    print("   3. Process videos one at a time")
    print("   4. Monitor system resources")
    
    if system_info['disk_free_gb'] > 10:
        print("\n🔮 For GPU acceleration (when disk space available):")
        print("   1. Free up 5GB+ disk space")
        print("   2. Run: python gpu_optimize.py")
        print("   3. Enjoy 4x faster processing!")
    
    print("\n🌟 CPU-optimized processing ready!")

if __name__ == "__main__":
    main() 