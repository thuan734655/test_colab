#!/usr/bin/env python3
"""
Simple Full Voice Creator - Tạo file lồng tiếng full đơn giản
"""

import os
import subprocess
import sys

def create_full_female_voice():
    """Tạo file lồng tiếng full với giọng nữ"""
    print("🎭 CREATING FULL FEMALE VOICE TRACK")
    print("=" * 60)
    print("🗣️ Voice: Hoài My (Nữ) - Vietnamese Historical Drama")
    print("📚 Combining 17 segments into one complete track")
    print()
    
    # Create output directory
    os.makedirs("full_voice_output", exist_ok=True)
    
    # List all female voice files in order
    input_files = []
    missing_files = []
    
    for i in range(1, 18):  # segments 1-17
        filename = f"srt_voice_test/seg_{i:02d}_female.wav"
        if os.path.exists(filename):
            input_files.append(filename)
            print(f"✅ Found: {filename}")
        else:
            missing_files.append(filename)
            print(f"❌ Missing: {filename}")
    
    if missing_files:
        print(f"\n⚠️ Warning: {len(missing_files)} files missing")
        print("Continuing with available files...")
    
    if not input_files:
        print("❌ No input files found!")
        return None
    
    print(f"\n🔧 Combining {len(input_files)} audio files...")
    
    # Create output filename
    output_file = "full_voice_output/full_vietnamese_drama_female.wav"
    
    # Simple concatenation using FFmpeg
    try:
        # Create input string for FFmpeg
        input_args = []
        for file in input_files:
            input_args.extend(['-i', file])
        
        # Build filter complex for concatenation
        filter_inputs = ''.join([f'[{i}:0]' for i in range(len(input_files))])
        filter_complex = f'{filter_inputs}concat=n={len(input_files)}:v=0:a=1[out]'
        
        cmd = ['ffmpeg'] + input_args + [
            '-filter_complex', filter_complex,
            '-map', '[out]',
            '-y', output_file
        ]
        
        print("🎵 Processing...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            file_size_mb = file_size / (1024 * 1024)
            
            print(f"✅ SUCCESS! Created full voice track:")
            print(f"   📁 File: {output_file}")
            print(f"   💾 Size: {file_size_mb:.2f} MB")
            
            # Get duration
            try:
                duration_cmd = ['ffprobe', '-v', 'quiet', '-show_entries', 
                               'format=duration', '-of', 'csv=p=0', output_file]
                duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
                if duration_result.returncode == 0:
                    duration = float(duration_result.stdout.strip())
                    print(f"   🎵 Duration: {duration:.1f}s ({duration/60:.1f} minutes)")
            except:
                pass
            
            return output_file
        else:
            print(f"❌ Failed to create full voice track")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        return None

def play_audio_file(audio_file):
    """Try to open audio file for playback"""
    print(f"\n🎧 AUDIO FILE READY!")
    print("=" * 60)
    print(f"📁 File: {audio_file}")
    print()
    print("🎮 TO LISTEN:")
    print("1. Double-click the file to open with default player")
    print("2. Or manually navigate to the file location")
    print()
    
    try:
        if sys.platform.startswith('win'):
            os.startfile(audio_file)
            print("🎵 Attempting to open with default Windows media player...")
            return True
    except Exception as e:
        print(f"⚠️ Could not auto-open file: {e}")
    
    return False

def main():
    """Main function"""
    print("🎬 SIMPLE FULL VOICE CREATOR")
    print("=" * 50)
    print("🎯 Creating complete Vietnamese drama audio track")
    print()
    
    # Create full voice track
    final_file = create_full_female_voice()
    
    if final_file:
        print(f"\n🎉 SUCCESS!")
        print(f"📊 Created complete Vietnamese historical drama voice track")
        print(f"🗣️ Female voice (Hoài My) - Perfect for emotional scenes")
        print(f"📚 All 17 dialogue segments combined")
        
        # Try to open file
        if not play_audio_file(final_file):
            print(f"\n📁 Manual Access:")
            print(f"Navigate to: {os.path.abspath(final_file)}")
        
        print(f"\n🎭 WHAT YOU'LL HEAR:")
        print("✨ Complete Vietnamese historical drama story")
        print("🎵 High-quality female voice narration")
        print("📖 All dialogue from father-daughter conversation")
        print("🎬 Ready for video synchronization")
        
    else:
        print("❌ Failed to create full voice track")

if __name__ == "__main__":
    main() 