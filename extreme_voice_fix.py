#!/usr/bin/env python3
"""
EXTREME VOICE FIX
Sửa video để voice siêu to, nghe rõ từ đầu đến cuối
"""

import os
import glob
import subprocess
import sys

def find_latest_files():
    """Tìm video và voice file mới nhất"""
    
    # Tìm video gốc
    video_files = glob.glob("uploads/*.mp4")
    if not video_files:
        print("❌ Không tìm thấy video trong uploads/")
        return None, None, None
    
    latest_video = max(video_files, key=os.path.getctime)
    
    # Tìm voice file  
    voice_files = glob.glob("outputs/*_voice.wav")
    if not voice_files:
        print("❌ Không tìm thấy voice file trong outputs/")
        return None, None, None
        
    latest_voice = max(voice_files, key=os.path.getctime)
    
    # Tìm SRT file
    srt_files = glob.glob("outputs/*.srt")
    latest_srt = None
    if srt_files:
        latest_srt = max(srt_files, key=os.path.getctime)
    
    return latest_video, latest_voice, latest_srt

def extreme_voice_boost(video_path, voice_path, srt_path=None, output_path="EXTREME_VOICE_VIDEO.mp4"):
    """Tạo video với voice siêu to"""
    
    print(f"🎬 Tạo video với EXTREME VOICE BOOST")
    print(f"📼 Video: {os.path.basename(video_path)}")
    print(f"🎤 Voice: {os.path.basename(voice_path)}")
    print(f"📄 SRT: {os.path.basename(srt_path) if srt_path else 'Không có'}")
    print("="*60)
    
    # Test các mức volume khác nhau
    test_volumes = [50, 75, 100, 150, 200]
    
    for volume in test_volumes:
        test_output = f"test_voice_{volume}x.mp4"
        print(f"\n🔊 TEST VOLUME {volume}x...")
        
        cmd = ['ffmpeg', '-i', video_path, '-i', voice_path]
        
        if srt_path and os.path.exists(srt_path):
            # Với subtitle + extreme voice boost
            srt_escaped = srt_path.replace('\\', '/')
            filter_complex = f"[0:v]subtitles='{srt_escaped}'[v];[1:a]volume={volume},loudnorm=I=-12:LRA=7:TP=-1.0,volume=2.0[voice];[voice]anull[a]"
            cmd.extend([
                '-filter_complex', filter_complex,
                '-map', '[v]', '-map', '[a]'
            ])
        else:
            # Chỉ extreme voice boost
            filter_complex = f"[1:a]volume={volume},loudnorm=I=-12:LRA=7:TP=-1.0,volume=2.0[voice];[voice]anull[a]"
            cmd.extend([
                '-filter_complex', filter_complex,
                '-map', '0:v', '-map', '[a]'
            ])
        
        # Encoding settings cho quality cao
        cmd.extend([
            '-c:v', 'libx264',
            '-preset', 'fast', 
            '-crf', '20',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-movflags', '+faststart',
            test_output, '-y'
        ])
        
        print(f"   ⚡ Chạy FFmpeg với volume {volume}x...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            file_size = os.path.getsize(test_output) / (1024*1024)
            print(f"   ✅ THÀNH CÔNG! File: {file_size:.1f}MB")
            
            # Đổi tên thành file chính nếu là volume cao nhất
            if volume == test_volumes[-1]:
                if os.path.exists(output_path):
                    os.remove(output_path)
                os.rename(test_output, output_path)
                print(f"   🎯 Lưu làm file chính: {output_path}")
            else:
                # Xóa file test
                if os.path.exists(test_output):
                    os.remove(test_output)
        else:
            print(f"   ❌ THẤT BẠI!")
            print(f"   Lỗi: {result.stderr[:200]}...")
    
    return output_path

def analyze_voice_levels(voice_path):
    """Phân tích mức volume của voice file"""
    print(f"\n🔍 PHÂN TÍCH VOICE LEVELS")
    print("="*40)
    
    cmd = [
        'ffprobe', '-v', 'quiet', '-af', 'volumedetect', 
        '-f', 'null', '/dev/null', '-i', voice_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        lines = result.stderr.split('\n')
        for line in lines:
            if any(keyword in line for keyword in ['mean_volume', 'max_volume', 'histogram']):
                print(f"   {line.strip()}")
        
        # Extract mean volume for analysis
        for line in lines:
            if "mean_volume" in line:
                try:
                    db_value = float(line.split(':')[1].strip().replace(' dB', ''))
                    print(f"\n📊 ANALYSIS:")
                    if db_value < -30:
                        print("   ⚠️ Voice RẤT NHỎ! Cần boost cực mạnh")
                        suggested_boost = int(abs(db_value) * 2)
                        print(f"   💡 Khuyến nghị volume: {suggested_boost}x")
                    elif db_value < -20:
                        print("   ⚠️ Voice nhỏ, cần boost mạnh")
                    elif db_value < -10:
                        print("   ✅ Voice ổn, có thể boost nhẹ")
                    else:
                        print("   ✅ Voice đã đủ to")
                    break
                except:
                    pass
    else:
        print("❌ Không thể phân tích voice levels")

def main():
    print("🚀 EXTREME VOICE FIX TOOL")
    print("=" * 60)
    
    # Tìm files
    video_path, voice_path, srt_path = find_latest_files()
    
    if not video_path or not voice_path:
        print("❌ Không tìm thấy đủ files cần thiết!")
        return
    
    print(f"✅ Tìm thấy files:")
    print(f"   📼 Video: {os.path.basename(video_path)}")
    print(f"   🎤 Voice: {os.path.basename(voice_path)}")
    print(f"   📄 SRT: {os.path.basename(srt_path) if srt_path else 'Không có'}")
    
    # Phân tích voice trước
    analyze_voice_levels(voice_path)
    
    # Tạo video với extreme boost
    output_file = extreme_voice_boost(video_path, voice_path, srt_path)
    
    print(f"\n🎉 HOÀN THÀNH!")
    print(f"📁 File output: {output_file}")
    print(f"💡 Giờ thử nghe video này - voice should be SIÊU TO!")
    
    # Final check
    if os.path.exists(output_file):
        final_size = os.path.getsize(output_file) / (1024*1024)
        print(f"📏 Kích thước final: {final_size:.1f}MB")
    
    print("\n🎯 HƯỚNG DẪN:")
    print("1. Mở file 'EXTREME_VOICE_VIDEO.mp4'")
    print("2. Kiểm tra xem voice có nghe rõ từ đầu video không") 
    print("3. Nếu vẫn không đủ to, chạy lại script này")
    print("4. Script sẽ test nhiều mức volume khác nhau")

if __name__ == "__main__":
    main() 