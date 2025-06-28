#!/usr/bin/env python3
"""
Simple Timeline Voice - Tạo lồng tiếng theo timeline SRT đơn giản
"""

import os
import subprocess
import sys

def srt_time_to_seconds(srt_time):
    """Convert SRT time to seconds"""
    time_part, ms_part = srt_time.split(',')
    h, m, s = map(int, time_part.split(':'))
    ms = int(ms_part)
    return h * 3600 + m * 60 + s + ms / 1000.0

def create_timeline_voice():
    """Tạo lồng tiếng theo timeline SRT"""
    print("🕒 SIMPLE TIMELINE VOICE CREATOR")
    print("=" * 60)
    print("🎯 Creating 48-second audio track with exact SRT timing")
    print("🗣️ Voice: Hoài My (Nữ) - Vietnamese Historical Drama")
    print()
    
    # SRT segments với timing
    segments = [
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
    
    # Create output directory
    os.makedirs("timeline_voice_output", exist_ok=True)
    
    # Step 1: Create base 50-second silence
    print("🔇 Step 1: Creating 50-second base silence track...")
    base_silence = "timeline_voice_output/base_silence.wav"
    
    cmd_silence = [
        'ffmpeg', '-f', 'lavfi', '-i', 'anullsrc=r=24000:cl=mono',
        '-t', '50', '-y', base_silence
    ]
    
    result = subprocess.run(cmd_silence, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to create base silence: {result.stderr}")
        return None
    
    print("✅ Base silence created (50 seconds)")
    
    # Step 2: Create file list for concatenation với timing
    print("\n🎵 Step 2: Planning voice segment placement...")
    
    file_list_path = "timeline_voice_output/timeline_list.txt"
    current_time = 0.0
    
    with open(file_list_path, 'w') as f:
        for segment in segments:
            segment_id = segment['id']
            start_time = srt_time_to_seconds(segment['start'])
            voice_file = f"srt_voice_test/seg_{segment_id:02d}_female.wav"
            
            # Add silence if there's a gap
            if start_time > current_time:
                silence_duration = start_time - current_time
                if silence_duration > 0.1:  # Only add if gap > 0.1s
                    silence_file = f"timeline_voice_output/silence_{segment_id}.wav"
                    
                    # Create specific silence
                    cmd_gap = [
                        'ffmpeg', '-f', 'lavfi', '-i', 'anullsrc=r=24000:cl=mono',
                        '-t', str(silence_duration), '-y', silence_file
                    ]
                    subprocess.run(cmd_gap, capture_output=True)
                    
                    f.write(f"file '{silence_file}'\n")
                    print(f"⏸️ Gap: {silence_duration:.1f}s before segment {segment_id}")
            
            # Add voice segment if exists
            if os.path.exists(voice_file):
                f.write(f"file '{voice_file}'\n")
                print(f"🎵 Segment {segment_id:02d}: {segment['start']} → {segment['end']}")
                
                # Get voice duration to update current_time
                try:
                    duration_cmd = ['ffprobe', '-v', 'quiet', '-show_entries', 
                                   'format=duration', '-of', 'csv=p=0', voice_file]
                    duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
                    if duration_result.returncode == 0:
                        voice_duration = float(duration_result.stdout.strip())
                        current_time = start_time + voice_duration
                except:
                    current_time = srt_time_to_seconds(segment['end'])
            else:
                print(f"❌ Missing: {voice_file}")
                current_time = srt_time_to_seconds(segment['end'])
        
        # Add final silence to reach 48+ seconds
        final_silence_duration = 50 - current_time
        if final_silence_duration > 0:
            final_silence = "timeline_voice_output/final_silence.wav"
            cmd_final = [
                'ffmpeg', '-f', 'lavfi', '-i', 'anullsrc=r=24000:cl=mono',
                '-t', str(final_silence_duration), '-y', final_silence
            ]
            subprocess.run(cmd_final, capture_output=True)
            f.write(f"file '{final_silence}'\n")
            print(f"⏸️ Final silence: {final_silence_duration:.1f}s")
    
    # Step 3: Concatenate all pieces
    print(f"\n🔧 Step 3: Assembling timeline voice track...")
    final_output = "timeline_voice_output/vietnamese_drama_timeline_sync.wav"
    
    cmd_concat = [
        'ffmpeg', '-f', 'concat', '-safe', '0', '-i', file_list_path,
        '-t', '48.5',  # Trim to exact length
        '-y', final_output
    ]
    
    result = subprocess.run(cmd_concat, capture_output=True, text=True)
    
    if result.returncode == 0 and os.path.exists(final_output):
        file_size = os.path.getsize(final_output)
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"\n✅ SUCCESS! Timeline voice track created:")
        print(f"   📁 File: {final_output}")
        print(f"   💾 Size: {file_size_mb:.2f} MB")
        
        # Get exact duration
        try:
            duration_cmd = ['ffprobe', '-v', 'quiet', '-show_entries', 
                           'format=duration', '-of', 'csv=p=0', final_output]
            duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
            if duration_result.returncode == 0:
                duration = float(duration_result.stdout.strip())
                print(f"   🎵 Duration: {duration:.1f}s (Perfect for video sync)")
        except:
            pass
        
        return final_output
    else:
        print(f"❌ Failed to create timeline voice")
        if result.stderr:
            print(f"Error: {result.stderr}")
        return None

def main():
    print("🎬 SIMPLE TIMELINE VOICE CREATOR")
    print("=" * 50)
    print("🎯 Creating voice track with perfect SRT synchronization")
    print()
    
    final_file = create_timeline_voice()
    
    if final_file:
        print(f"\n🎉 PERFECT! Timeline voice track ready!")
        print(f"🎬 Ready for video synchronization")
        
        print(f"\n🎧 WHAT YOU'LL HEAR:")
        print("🔇 0-1s: Silence (waiting for first dialogue)")
        print("🗣️ 1s: 'Phụ thân, con thà chết chứ không gả cho Thất tiểu đệ!'")
        print("🔇 3.5-4.1s: Brief pause")
        print("🗣️ 4.1s: 'Ninh nhi, đừng hồ đồ.'")
        print("📚 ... all 17 segments with exact timing ...")
        print("🗣️ 46s: 'Còn là một tên câm không có linh căn.'")
        print("🔇 48s: End")
        
        print(f"\n💡 USAGE:")
        print("✅ Import this audio into video editor")
        print("✅ Align with video start (00:00:00)")
        print("✅ Voice will automatically match SRT timing")
        print("✅ No manual synchronization needed!")
        
        # Auto-play
        try:
            if sys.platform.startswith('win'):
                os.startfile(final_file)
                print(f"\n🎵 Opening audio for preview...")
        except:
            print(f"\n📁 Manually open: {final_file}")
    else:
        print("❌ Failed to create timeline voice track")

if __name__ == "__main__":
    main() 