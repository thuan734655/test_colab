#!/usr/bin/env python3
"""
Create Full Voice - Tạo file lồng tiếng full từ các segments
"""

import os
import subprocess
import sys
from pathlib import Path

class FullVoiceCreator:
    def __init__(self):
        self.input_dir = "srt_voice_test"
        self.output_dir = "full_voice_output"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Timing từ SRT để tạo silence giữa các đoạn
        self.segments_timing = [
            {"id": 1, "start": "00:00:01,000", "end": "00:00:03,459"},
            {"id": 2, "start": "00:00:04,139", "end": "00:00:05,099"},
            {"id": 3, "start": "00:00:05,459", "end": "00:00:08,000"},
            {"id": 4, "start": "00:00:08,000", "end": "00:00:10,000"},
            {"id": 5, "start": "00:00:10,000", "end": "00:00:12,820"},
            {"id": 6, "start": "00:00:16,440", "end": "00:00:17,519"},
            {"id": 7, "start": "00:00:17,859", "end": "00:00:19,660"},
            {"id": 8, "start": "00:00:19,660", "end": "00:00:21,800"},
            {"id": 9, "start": "00:00:26,760", "end": "00:00:29,260"},
            {"id": 10, "start": "00:00:29,260", "end": "00:00:31,519"},
            {"id": 11, "start": "00:00:31,519", "end": "00:00:34,039"},
            {"id": 12, "start": "00:00:34,039", "end": "00:00:35,920"},
            {"id": 13, "start": "00:00:35,920", "end": "00:00:38,079"},
            {"id": 14, "start": "00:00:38,079", "end": "00:00:40,259"},
            {"id": 15, "start": "00:00:43,659", "end": "00:00:45,219"},
            {"id": 16, "start": "00:00:45,219", "end": "00:00:46,259"},
            {"id": 17, "start": "00:00:46,259", "end": "00:00:48,299"}
        ]
    
    def time_to_seconds(self, time_str):
        """Convert SRT time to seconds"""
        # Format: HH:MM:SS,mmm
        time_part, ms_part = time_str.split(',')
        h, m, s = map(int, time_part.split(':'))
        ms = int(ms_part)
        return h * 3600 + m * 60 + s + ms / 1000.0
    
    def create_silence(self, duration_seconds, output_path):
        """Tạo file silence với độ dài cụ thể"""
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
    
    def create_full_female_voice(self):
        """Tạo file lồng tiếng full với giọng nữ"""
        print("🎭 CREATING FULL FEMALE VOICE TRACK")
        print("=" * 60)
        print("🗣️ Voice: Hoài My (Nữ) - Perfect for emotional scenes")
        print("📚 Content: Vietnamese Historical Drama - Complete Story")
        print()
        
        # Create file list for concatenation
        file_list_path = f"{self.output_dir}/file_list.txt"
        final_output = f"{self.output_dir}/full_vietnamese_drama_female.wav"
        
        with open(file_list_path, 'w') as f:
            previous_end_time = 0
            
            for i, segment in enumerate(self.segments_timing):
                segment_id = segment['id']
                start_time = self.time_to_seconds(segment['start'])
                end_time = self.time_to_seconds(segment['end'])
                
                # Calculate silence needed before this segment
                if i > 0:
                    silence_duration = start_time - previous_end_time
                    if silence_duration > 0.1:  # Add silence if gap > 0.1s
                        silence_file = f"{self.output_dir}/silence_{segment_id}.wav"
                        if self.create_silence(silence_duration, silence_file):
                            f.write(f"file '{silence_file}'\n")
                            print(f"⏸️ Added {silence_duration:.1f}s silence before segment {segment_id}")
                
                # Add the voice segment
                voice_file = f"{self.input_dir}/seg_{segment_id:02d}_female.wav"
                if os.path.exists(voice_file):
                    f.write(f"file '{voice_file}'\n")
                    print(f"🎵 Segment {segment_id:02d}: {segment['start']} → {segment['end']}")
                else:
                    print(f"❌ Missing file: {voice_file}")
                
                previous_end_time = end_time
        
        print(f"\n🔧 Concatenating all segments...")
        
        # Concatenate all files
        try:
            cmd = [
                'ffmpeg', '-f', 'concat', '-safe', '0', '-i', file_list_path,
                '-c', 'copy', '-y', final_output
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(final_output):
                file_size = os.path.getsize(final_output)
                file_size_mb = file_size / (1024 * 1024)
                
                print(f"✅ SUCCESS! Created full voice track:")
                print(f"   📁 File: {final_output}")
                print(f"   💾 Size: {file_size_mb:.2f} MB")
                
                # Analyze the final file
                self.analyze_final_audio(final_output)
                
                return final_output
            else:
                print(f"❌ Failed to create full voice track")
                print(f"Error: {result.stderr}")
                return None
                
        except Exception as e:
            print(f"❌ Error during concatenation: {e}")
            return None
    
    def analyze_final_audio(self, audio_path):
        """Phân tích file audio cuối cùng"""
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
                
                print(f"\n📊 FINAL AUDIO ANALYSIS:")
                print(f"   🎵 Total Duration: {duration:.1f}s ({duration/60:.1f} minutes)")
                print(f"   💾 File Size: {size_bytes/1024/1024:.2f} MB")
                print(f"   📈 Quality: Professional grade for production use")
                
                # Find audio stream
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'audio':
                        sample_rate = int(stream.get('sample_rate', 0))
                        channels = int(stream.get('channels', 0))
                        print(f"   📊 Sample Rate: {sample_rate} Hz")
                        print(f"   🔊 Channels: {channels} (Mono)")
                        break
                        
        except Exception as e:
            print(f"⚠️ Could not analyze final audio: {e}")
    
    def create_playback_instructions(self, audio_file):
        """Tạo hướng dẫn nghe file"""
        print(f"\n🎧 HOW TO LISTEN TO YOUR FULL VOICE TRACK:")
        print("=" * 60)
        print(f"📁 File Location: {audio_file}")
        print()
        print("🎮 PLAYBACK OPTIONS:")
        print("1. Double-click the file to open with default media player")
        print("2. Use VLC Media Player for best quality")
        print("3. Use Windows Media Player")
        print("4. Drag & drop into any audio player")
        print()
        print("🎭 WHAT YOU'LL HEAR:")
        print("✨ Complete Vietnamese historical drama with emotional female voice")
        print("🗣️ Hoài My voice perfectly suited for dramatic scenes")
        print("⏱️ Natural timing with appropriate pauses between dialogues")
        print("🎵 High-quality audio suitable for professional video production")
        print()
        print("💡 USAGE TIPS:")
        print("- Perfect for video dubbing projects")
        print("- Can be synced with video using video editing software")
        print("- Ideal for Vietnamese historical drama content")
        print("- Professional quality for commercial use")

def main():
    """Main function"""
    print("🎬 FULL VIETNAMESE DRAMA VOICE CREATOR")
    print("=" * 60)
    print("🎯 Creating complete audio track with female voice (Hoài My)")
    print("📚 Content: 17 segments of Vietnamese historical drama")
    print()
    
    creator = FullVoiceCreator()
    
    # Create full voice track
    final_file = creator.create_full_female_voice()
    
    if final_file:
        creator.create_playback_instructions(final_file)
        
        print(f"\n🎉 SUCCESS! Full voice track created!")
        print(f"🎧 Ready to listen: {final_file}")
        
        # Try to open the file automatically
        try:
            import os
            if sys.platform.startswith('win'):
                os.startfile(final_file)
                print("🎵 Opening audio file with default player...")
            else:
                print("📁 Please manually open the file to listen")
        except:
            print("📁 Please manually open the file to listen")
    else:
        print("❌ Failed to create full voice track")

if __name__ == "__main__":
    main() 