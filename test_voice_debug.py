#!/usr/bin/env python3
"""
Voice Generation Debug Script
Kiểm tra xem tất cả segments có được tạo voice thành công không
"""

import os
import glob
import time
import subprocess

def test_voice_files():
    """Kiểm tra các file voice đã tạo"""
    print("🔍 KIỂM TRA VOICE FILES")
    print("="*50)
    
    output_dir = "outputs"
    if not os.path.exists(output_dir):
        print("❌ Thư mục outputs không tồn tại!")
        return
    
    # Tìm tất cả voice files
    voice_files = glob.glob(os.path.join(output_dir, "*_voice.wav"))
    
    if not voice_files:
        print("❌ Không tìm thấy file voice nào!")
        return
    
    print(f"✅ Tìm thấy {len(voice_files)} file voice:")
    
    for voice_file in voice_files:
        file_size = os.path.getsize(voice_file)
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"📄 {os.path.basename(voice_file)}")
        print(f"   📏 Kích thước: {file_size_mb:.2f} MB")
        
        # Kiểm tra duration bằng ffprobe
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries', 
                'format=duration', '-of', 'csv=p=0', voice_file
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                print(f"   ⏱️ Thời lượng: {duration:.2f}s")
            else:
                print(f"   ❌ Không đọc được duration")
        except Exception as e:
            print(f"   ❌ Lỗi ffprobe: {e}")
        
        # Kiểm tra volume level
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-af', 'volumedetect', 
                '-f', 'null', '/dev/null', '-i', voice_file
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if "mean_volume" in result.stderr:
                lines = result.stderr.split('\n')
                for line in lines:
                    if "mean_volume" in line:
                        print(f"   🔊 {line.strip()}")
                    elif "max_volume" in line:
                        print(f"   📈 {line.strip()}")
        except Exception as e:
            print(f"   ❌ Lỗi volume detect: {e}")
        
        print()

def test_extreme_amplification():
    """Test extreme voice amplification"""
    print("🚀 TEST EXTREME VOICE AMPLIFICATION")
    print("="*50)
    
    # Tìm file voice mới nhất
    voice_files = glob.glob("outputs/*_voice.wav")
    if not voice_files:
        print("❌ Không có file voice để test!")
        return
    
    latest_voice = max(voice_files, key=os.path.getctime)
    print(f"📄 Testing file: {os.path.basename(latest_voice)}")
    
    # Test với các mức amplification khác nhau
    test_levels = [25, 50, 75, 100]
    
    for level in test_levels:
        output_file = f"temp_test_{level}x.wav"
        print(f"\n🔊 Testing {level}x amplification...")
        
        cmd = [
            'ffmpeg', '-i', latest_voice,
            '-af', f'volume={level},loudnorm=I=-16:LRA=11:TP=-1.5',
            output_file, '-y'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            file_size = os.path.getsize(output_file)
            print(f"   ✅ Thành công! File: {file_size/1024:.1f}KB")
            
            # Kiểm tra volume
            try:
                cmd2 = [
                    'ffprobe', '-v', 'quiet', '-af', 'volumedetect', 
                    '-f', 'null', '/dev/null', '-i', output_file
                ]
                result2 = subprocess.run(cmd2, capture_output=True, text=True)
                if "mean_volume" in result2.stderr:
                    for line in result2.stderr.split('\n'):
                        if "mean_volume" in line:
                            volume_db = line.split(':')[1].strip()
                            print(f"   📊 Mean volume: {volume_db}")
                            break
            except:
                pass
            
            # Cleanup
            if os.path.exists(output_file):
                os.remove(output_file)
        else:
            print(f"   ❌ Thất bại: {result.stderr}")

def check_latest_logs():
    """Kiểm tra logs gần nhất"""
    print("📋 KIỂM TRA LOGS GẦN NHẤT")
    print("="*50)
    
    # Đọc terminal output gần nhất nếu có
    try:
        # Tìm file log nếu có
        log_files = glob.glob("*.log")
        if log_files:
            latest_log = max(log_files, key=os.path.getctime)
            print(f"📄 Log file: {latest_log}")
            
            with open(latest_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()[-50:]  # 50 dòng cuối
                for line in lines:
                    if "TẠO LỒNG TIẾNG" in line or "THÀNH CÔNG" in line or "THẤT BẠI" in line:
                        print(f"   {line.strip()}")
        else:
            print("ℹ️ Không tìm thấy file log")
            print("💡 Bạn có thể check terminal output khi chạy server")
    except Exception as e:
        print(f"❌ Lỗi đọc log: {e}")

if __name__ == "__main__":
    print("🎤 VOICE GENERATION DEBUG TOOL")
    print("=" * 60)
    print()
    
    test_voice_files()
    print()
    test_extreme_amplification()
    print()
    check_latest_logs()
    
    print("\n🎯 KHUYẾN NGHỊ:")
    print("1. Kiểm tra terminal khi tạo voice xem có lỗi segment nào không")
    print("2. Đảm bảo tất cả segments được tạo THÀNH CÔNG")
    print("3. Voice volume giờ đã tăng lên 50x với loudnorm")
    print("4. Nếu vẫn không nghe được, có thể tăng lên 75x hoặc 100x") 