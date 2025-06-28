#!/usr/bin/env python3
"""
Fix Audio Volume - Sửa vấn đề âm lượng tăng dần trong video
"""

import os
import subprocess
import sys

class AudioVolumeFixer:
    def __init__(self):
        self.input_files = {
            'video': 'uploads/3700dd88-ddba-482f-83af-1ab9bfd0dbd1_v1.mp4',
            'voice': 'outputs/3700dd88-ddba-482f-83af-1ab9bfd0dbd1_voice.wav', 
            'srt': 'outputs/3700dd88-ddba-482f-83af-1ab9bfd0dbd1_uploaded.srt'
        }
        self.output_dir = "fixed_audio_output"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def analyze_current_issue(self):
        """Phân tích vấn đề hiện tại"""
        print("🔍 PHÂN TÍCH VẤN ĐỀ ÂM LƯỢNG")
        print("=" * 60)
        print("❌ Vấn đề từ log:")
        print("   1. Voice volume: 50x (QUÁ CAO - gây méo)")
        print("   2. loudnorm filter (gây tăng âm lượng dần dần)")
        print("   3. Original audio = 0.0 (tắt hoàn toàn)")
        print("   4. Normalize = 0 (không cân bằng)")
        print()
        print("🎯 Nguyên nhân:")
        print("   - Volume quá cao → distortion")
        print("   - loudnorm tự động điều chỉnh → tăng dần")
        print("   - Thiếu cân bằng audio gốc")
        print()
    
    def check_files_exist(self):
        """Kiểm tra file tồn tại"""
        print("📂 KIỂM TRA FILES:")
        print("-" * 30)
        
        missing_files = []
        for name, path in self.input_files.items():
            if os.path.exists(path):
                size = os.path.getsize(path)
                size_mb = size / (1024 * 1024)
                print(f"✅ {name}: {path} ({size_mb:.1f}MB)")
            else:
                print(f"❌ {name}: {path} (MISSING)")
                missing_files.append(path)
        
        if missing_files:
            print(f"\n❌ Thiếu {len(missing_files)} files!")
            return False
        
        print("\n✅ Tất cả files đều có sẵn")
        return True
    
    def test_different_volumes(self):
        """Test các mức volume khác nhau"""
        print("\n🎚️ TEST CÁC MỨC VOLUME KHÁC NHAU")
        print("=" * 60)
        
        # Test volumes: reasonable levels
        test_volumes = [
            {"voice": 2.0, "orig": 0.3, "desc": "Voice nhẹ (2x)"},
            {"voice": 4.0, "orig": 0.2, "desc": "Voice vừa (4x)"},  
            {"voice": 6.0, "orig": 0.1, "desc": "Voice rõ (6x)"},
            {"voice": 8.0, "orig": 0.1, "desc": "Voice mạnh (8x)"}
        ]
        
        for i, vol in enumerate(test_volumes, 1):
            print(f"\n🔧 Test {i}/4: {vol['desc']}")
            output_file = f"{self.output_dir}/test_volume_{i}_voice{vol['voice']:.0f}x.mp4"
            
            success = self.create_fixed_video(
                output_file,
                voice_volume=vol['voice'],
                orig_volume=vol['orig'],
                test_mode=True
            )
            
            if success:
                print(f"   ✅ Created: {os.path.basename(output_file)}")
            else:
                print(f"   ❌ Failed: {vol['desc']}")
        
        print(f"\n📁 Test files saved in: {self.output_dir}/")
        print("🎧 Nghe thử từng file để chọn volume tốt nhất!")
    
    def create_fixed_video(self, output_path, voice_volume=6.0, orig_volume=0.1, test_mode=False):
        """Tạo video với volume cố định (không dùng loudnorm)"""
        try:
            # Build FFmpeg command với volume cố định
            cmd = [
                'ffmpeg',
                '-i', self.input_files['video'],  # Input video
                '-i', self.input_files['voice'],  # Input voice
                '-filter_complex',
                f'[0:v]subtitles=\'{self.input_files["srt"].replace(chr(92), "/")}\'[v];'  # Add subtitles
                f'[0:a]volume={orig_volume}[orig];'  # Original audio (low)
                f'[1:a]volume={voice_volume}[voice];'  # Voice audio (fixed volume)
                f'[orig][voice]amix=inputs=2:duration=first[a]',  # Mix without normalize
                '-map', '[v]',  # Map video
                '-map', '[a]',  # Map audio
                '-c:v', 'libx264',  # Video codec
                '-preset', 'fast',  # Encoding speed
                '-crf', '23',  # Quality
                '-c:a', 'aac',  # Audio codec  
                '-b:a', '128k',  # Audio bitrate
                '-movflags', '+faststart',  # Web optimization
                '-y', output_path  # Output file
            ]
            
            if not test_mode:
                print(f"🔧 Creating fixed video...")
                print(f"   Voice volume: {voice_volume}x (cố định)")
                print(f"   Original volume: {orig_volume}x")
                print(f"   NO loudnorm (tránh tăng dần)")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(output_path):
                if not test_mode:
                    file_size = os.path.getsize(output_path)
                    file_size_mb = file_size / (1024 * 1024)
                    print(f"   ✅ Success: {file_size_mb:.1f}MB")
                return True
            else:
                if not test_mode:
                    print(f"   ❌ Failed: {result.stderr[:200]}...")
                return False
                
        except Exception as e:
            if not test_mode:
                print(f"   ❌ Error: {e}")
            return False
    
    def create_recommended_fix(self):
        """Tạo video với cài đặt đề xuất"""
        print("\n🎯 TẠO VIDEO FIXED ĐỀ XUẤT")
        print("=" * 60)
        print("🎚️ Cài đặt đề xuất:")
        print("   - Voice: 6x (rõ ràng nhưng không méo)")
        print("   - Original: 0.1x (giữ âm thanh nền nhẹ)")
        print("   - NO loudnorm (âm lượng cố định)")
        print("   - Proper mixing (cân bằng tốt)")
        print()
        
        output_file = f"{self.output_dir}/vietnamese_drama_FIXED_VOLUME.mp4"
        
        success = self.create_fixed_video(
            output_file,
            voice_volume=6.0,
            orig_volume=0.1,
            test_mode=False
        )
        
        if success:
            print(f"\n🎉 SUCCESS! Fixed video created:")
            print(f"   📁 File: {output_file}")
            print(f"   ✅ Volume: Cố định, không tăng dần")
            print(f"   ✅ Audio: Cân bằng tốt")
            print(f"   ✅ Quality: Professional")
            
            return output_file
        else:
            print(f"\n❌ Failed to create fixed video")
            return None
    
    def play_comparison(self, fixed_file=None):
        """So sánh file gốc và file đã fix"""
        print(f"\n🎧 SO SÁNH AUDIO")
        print("=" * 40)
        
        original_file = "outputs/3700dd88-ddba-482f-83af-1ab9bfd0dbd1_final.mp4"
        
        print("🔴 ORIGINAL (có vấn đề):")
        print(f"   📁 {original_file}")
        print("   ❌ Volume tăng dần, phần đầu không nghe được")
        
        if fixed_file:
            print(f"\n🟢 FIXED (đã sửa):")
            print(f"   📁 {fixed_file}")
            print("   ✅ Volume cố định, nghe rõ từ đầu đến cuối")
            
            # Auto-play comparison
            choice = input(f"\n🎮 Nghe so sánh? (y/n): ").strip().lower()
            if choice in ['y', 'yes']:
                print("\n🔴 Playing ORIGINAL (problematic)...")
                try:
                    os.startfile(original_file)
                    input("Press Enter khi nghe xong để chuyển sang FIXED...")
                    
                    print("🟢 Playing FIXED (corrected)...")
                    os.startfile(fixed_file)
                    print("✅ So sánh hoàn tất!")
                except:
                    print("📁 Please manually open both files to compare")

def main():
    print("🎚️ AUDIO VOLUME FIXER")
    print("=" * 50)
    print("🎯 Sửa vấn đề âm lượng tăng dần dần trong video")
    print()
    
    fixer = AudioVolumeFixer()
    
    # Step 1: Analyze issue
    fixer.analyze_current_issue()
    
    # Step 2: Check files
    if not fixer.check_files_exist():
        print("❌ Không thể tiếp tục - thiếu files")
        return
    
    # Step 3: Ask user what they want
    print("\n🎯 CHỌN PHƯƠNG PHÁP:")
    print("1. Tạo video fixed đề xuất (khuyến nghị)")
    print("2. Test nhiều mức volume khác nhau")
    print("3. Thoát")
    
    choice = input("\nChọn (1-3): ").strip()
    
    if choice == "1":
        # Create recommended fix
        fixed_file = fixer.create_recommended_fix()
        if fixed_file:
            fixer.play_comparison(fixed_file)
            
    elif choice == "2":
        # Test different volumes
        fixer.test_different_volumes()
        print("\n💡 Sau khi nghe test, chạy lại script và chọn option 1")
        
    elif choice == "3":
        print("👋 Thoát")
        
    else:
        print("❌ Lựa chọn không hợp lệ")

if __name__ == "__main__":
    main() 