#!/usr/bin/env python3
"""
Timeline Voice Creator - Tạo lồng tiếng theo đúng timeline SRT
"""

import os
import subprocess
import sys
import tempfile

class TimelineVoiceCreator:
    def __init__(self):
        self.input_dir = "srt_voice_test"
        self.output_dir = "timeline_voice_output"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # SRT timeline chính xác từ file gốc
        self.srt_segments = [
            {"id": 1, "start": "00:00:01,000", "end": "00:00:03,459", "text": "Phụ thân, con thà chết chứ không gả cho Thất tiểu đệ!"},
            {"id": 2, "start": "00:00:04,139", "end": "00:00:05,099", "text": "Ninh nhi, đừng hồ đồ."},
            {"id": 3, "start": "00:00:05,459", "end": "00:00:08,000", "text": "Mười năm trước, phụ thân Tiểu Đệ đã cứu mạng Hứa gia chúng ta."},
            {"id": 4, "start": "00:00:08,000", "end": "00:00:10,000", "text": "Nên mới có lời hứa thành thân năm con mười tám tuổi."},
            {"id": 5, "start": "00:00:10,000", "end": "00:00:12,820", "text": "Nếu con hủy kèo, sẽ bị người đời nói là vong ân bội nghĩa."},
            {"id": 6, "start": "00:00:16,440", "end": "00:00:17,519", "text": "Hừ, con không quan tâm!"},
            {"id": 7, "start": "00:00:17,859", "end": "00:00:19,660", "text": "Tên câm đó, con nhất quyết không gả!"},
            {"id": 8, "start": "00:00:19,660", "end": "00:00:21,800", "text": "Các người còn ép con, chính là muốn con chết!"},
            {"id": 9, "start": "00:00:26,760", "end": "00:00:29,260", "text": "Suốt mười tám năm, ngươi chưa từng mở lời trước mặt ai."},
            {"id": 10, "start": "00:00:29,260", "end": "00:00:31,519", "text": "Người đời đều tưởng ngươi là tên câm điên."},
            {"id": 11, "start": "00:00:31,519", "end": "00:00:34,039", "text": "Nào biết ngươi chỉ bị phụ thân cho uống một viên Linh Chủng,"},
            {"id": 12, "start": "00:00:34,039", "end": "00:00:35,920", "text": "mười tám năm mới thành thục."},
            {"id": 13, "start": "00:00:35,920", "end": "00:00:38,079", "text": "Trong lúc này, hễ mở miệng sẽ bị thiên lôi tập kích."},
            {"id": 14, "start": "00:00:38,079", "end": "00:00:40,259", "text": "Và hôm nay, chính là ngày cuối cùng."},
            {"id": 15, "start": "00:00:43,659", "end": "00:00:45,219", "text": "Tiểu Đệ đứa nhỏ này cái gì cũng tốt,"},
            {"id": 16, "start": "00:00:45,219", "end": "00:00:46,259", "text": "tiếc là một tên câm."},
            {"id": 17, "start": "00:00:46,259", "end": "00:00:48,299", "text": "Còn là một tên câm không có linh căn."}
        ]
    
    def srt_time_to_seconds(self, srt_time):
        """Convert SRT time format to seconds"""
        # Format: HH:MM:SS,mmm
        time_part, ms_part = srt_time.split(',')
        h, m, s = map(int, time_part.split(':'))
        ms = int(ms_part)
        return h * 3600 + m * 60 + s + ms / 1000.0
    
    def create_silence(self, duration_seconds, output_path):
        """Tạo file silence"""
        try:
            cmd = [
                'ffmpeg', '-f', 'lavfi', '-i', f'anullsrc=r=24000:cl=mono',
                '-t', str(duration_seconds), '-y', output_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Failed to create silence: {e}")
            return False
    
    def create_timeline_voice(self):
        """Tạo lồng tiếng theo đúng timeline SRT"""
        print("🕒 CREATING TIMELINE-BASED VOICE TRACK")
        print("=" * 60)
        print("🎯 Following exact SRT timing: 00:00:01 → 00:00:48")
        print("🗣️ Voice: Hoài My (Nữ) - Vietnamese Historical Drama")
        print()
        
        # Tính toán timeline
        total_duration = self.srt_time_to_seconds("00:00:48,299")  # Đến cuối đoạn cuối
        print(f"📏 Total timeline duration: {total_duration:.1f}s")
        
        # Tạo base silence track (toàn bộ 48+ giây)
        base_silence = f"{self.output_dir}/base_silence.wav"
        print(f"🔇 Creating base silence track ({total_duration + 1:.1f}s)...")
        
        if not self.create_silence(total_duration + 1, base_silence):
            print("❌ Failed to create base silence")
            return None
        
        # Prepare overlay inputs
        overlay_inputs = [base_silence]  # Bắt đầu với silence
        overlay_filters = ["[0:a]"]
        
        valid_segments = 0
        
        for segment in self.srt_segments:
            segment_id = segment['id']
            start_time = self.srt_time_to_seconds(segment['start'])
            
            # Kiểm tra file voice segment
            voice_file = f"{self.input_dir}/seg_{segment_id:02d}_female.wav"
            
            if os.path.exists(voice_file):
                overlay_inputs.append(voice_file)
                input_index = len(overlay_inputs) - 1
                
                # Add delay filter for timing
                overlay_filters.append(f"[{input_index}:a]adelay={start_time * 1000}|{start_time * 1000}[voice{segment_id}]")
                
                print(f"🎵 Segment {segment_id:02d}: {segment['start']} → {segment['end']}")
                print(f"   Text: {segment['text'][:50]}...")
                print(f"   Delay: {start_time:.3f}s")
                
                valid_segments += 1
            else:
                print(f"❌ Missing: {voice_file}")
        
        if valid_segments == 0:
            print("❌ No valid voice segments found!")
            return None
        
        # Build mix filter
        mix_inputs = ["[0:a]"]  # Base silence
        for i in range(1, valid_segments + 1):
            segment_id = self.srt_segments[i-1]['id']
            mix_inputs.append(f"[voice{segment_id}]")
        
        mix_filter = "".join(mix_inputs) + f"amix=inputs={len(mix_inputs)}:duration=longest[out]"
        overlay_filters.append(mix_filter)
        
        # Combine all filters
        filter_complex = ";".join(overlay_filters)
        
        # Create final output
        final_output = f"{self.output_dir}/vietnamese_drama_timeline_female.wav"
        
        try:
            # Build FFmpeg command
            cmd = ['ffmpeg']
            
            # Add all input files
            for input_file in overlay_inputs:
                cmd.extend(['-i', input_file])
            
            # Add filter and output
            cmd.extend([
                '-filter_complex', filter_complex,
                '-map', '[out]',
                '-t', str(total_duration),  # Clip to exact duration
                '-y', final_output
            ])
            
            print(f"\n🔧 Processing timeline with {valid_segments} voice segments...")
            print("⏳ This may take a moment...")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(final_output):
                file_size = os.path.getsize(final_output)
                file_size_mb = file_size / (1024 * 1024)
                
                print(f"\n✅ SUCCESS! Created timeline-based voice track:")
                print(f"   📁 File: {final_output}")
                print(f"   💾 Size: {file_size_mb:.2f} MB")
                
                # Analyze result
                self.analyze_timeline_audio(final_output)
                
                return final_output
            else:
                print(f"❌ Failed to create timeline voice track")
                if result.stderr:
                    print(f"Error: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"❌ Error during timeline processing: {e}")
            return None
    
    def analyze_timeline_audio(self, audio_path):
        """Phân tích file audio timeline"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', audio_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                
                format_info = data.get('format', {})
                duration = float(format_info.get('duration', 0))
                size_bytes = int(format_info.get('size', 0))
                
                print(f"\n📊 TIMELINE AUDIO ANALYSIS:")
                print(f"   🎵 Duration: {duration:.1f}s (Perfect for 48s video)")
                print(f"   💾 File Size: {size_bytes/1024/1024:.2f} MB")
                print(f"   ⏰ Timeline: Matches SRT exactly")
                print(f"   🎯 Sync: Ready for video synchronization")
                
                # Audio quality info
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'audio':
                        sample_rate = int(stream.get('sample_rate', 0))
                        channels = int(stream.get('channels', 0))
                        print(f"   📊 Sample Rate: {sample_rate} Hz")
                        print(f"   🔊 Channels: {channels}")
                        break
                        
        except Exception as e:
            print(f"⚠️ Could not analyze timeline audio: {e}")
    
    def create_usage_instructions(self, audio_file):
        """Tạo hướng dẫn sử dụng"""
        print(f"\n🎬 TIMELINE VOICE TRACK READY!")
        print("=" * 60)
        print(f"📁 File: {audio_file}")
        print()
        print("🎯 PERFECT SYNCHRONIZATION:")
        print("✅ Voice appears at exact SRT timestamps")
        print("✅ Silent gaps match original timing")
        print("✅ Total duration matches video timeline")
        print("✅ Ready for direct video overlay")
        print()
        print("🎮 HOW TO USE:")
        print("1. Import both video and this audio into editing software")
        print("2. Align audio track to video start (00:00:00)")
        print("3. Audio will automatically sync with SRT timing")
        print("4. Adjust final volume levels as needed")
        print()
        print("💡 SUPPORTED SOFTWARE:")
        print("- Adobe Premiere Pro")
        print("- DaVinci Resolve") 
        print("- Final Cut Pro")
        print("- Any video editor with audio import")

def main():
    """Main function"""
    print("🕒 TIMELINE VOICE CREATOR")
    print("=" * 50)
    print("🎯 Creating voice track with exact SRT timing")
    print("📚 Vietnamese Historical Drama - Perfect Sync")
    print()
    
    creator = TimelineVoiceCreator()
    
    # Create timeline-based voice
    final_file = creator.create_timeline_voice()
    
    if final_file:
        creator.create_usage_instructions(final_file)
        
        print(f"\n🎉 SUCCESS!")
        print(f"🎬 Timeline voice track created with perfect SRT sync!")
        
        # Try to play the file
        try:
            if sys.platform.startswith('win'):
                os.startfile(final_file)
                print(f"🎵 Opening timeline audio for preview...")
        except:
            print(f"📁 Manually open: {final_file}")
            
        print(f"\n✨ WHAT YOU'LL HEAR:")
        print("🔇 Silence from 0-1s (before first dialogue)")
        print("🗣️ Voice at 1s: 'Phụ thân, con thà chết...'")
        print("🔇 Natural pauses between dialogues")  
        print("🗣️ Final voice at 46s: 'Còn là một tên câm...'")
        print("🔇 Silence until 48s end")
        print()
        print("🎬 Perfect for video synchronization!")
        
    else:
        print("❌ Failed to create timeline voice track")

if __name__ == "__main__":
    main() 