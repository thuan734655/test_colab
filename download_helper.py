#!/usr/bin/env python3
"""
Download Helper - Easy video download for users
Hỗ trợ download video dễ dàng cho users
"""

import os
import shutil
import requests
from datetime import datetime

def print_header():
    print("📥 VIDEO DOWNLOAD HELPER")
    print("=" * 50)
    print("🎬 Download your processed videos easily!")
    print()

def list_available_videos():
    """List all available processed videos"""
    print("📁 Available processed videos:")
    print("-" * 40)
    
    if not os.path.exists('outputs'):
        print("❌ No outputs folder found")
        return []
    
    videos = []
    files = os.listdir('outputs')
    
    # Group files by task ID
    tasks = {}
    for file in files:
        if '_final.mp4' in file:
            task_id = file.replace('_final.mp4', '')
            tasks[task_id] = {'final': file}
        elif '_voice.wav' in file:
            task_id = file.replace('_voice.wav', '')
            if task_id not in tasks:
                tasks[task_id] = {}
            tasks[task_id]['voice'] = file
        elif '_uploaded.srt' in file or '_subtitles.srt' in file:
            task_id = file.replace('_uploaded.srt', '').replace('_subtitles.srt', '')
            if task_id not in tasks:
                tasks[task_id] = {}
            tasks[task_id]['srt'] = file
    
    # Display organized results
    for i, (task_id, files) in enumerate(tasks.items(), 1):
        if 'final' in files:
            video_path = os.path.join('outputs', files['final'])
            size_mb = os.path.getsize(video_path) / (1024*1024)
            mod_time = datetime.fromtimestamp(os.path.getmtime(video_path))
            
            print(f"{i}. Task: {task_id[:8]}...")
            print(f"   📹 Final Video: {files['final']} ({size_mb:.1f}MB)")
            print(f"   📅 Created: {mod_time.strftime('%Y-%m-%d %H:%M')}")
            
            if 'voice' in files:
                print(f"   🎵 Voice: {files['voice']}")
            if 'srt' in files:
                print(f"   📝 Subtitles: {files['srt']}")
            
            videos.append({
                'index': i,
                'task_id': task_id,
                'files': files,
                'size_mb': size_mb
            })
            print()
    
    return videos

def copy_to_desktop(videos):
    """Copy selected videos to desktop"""
    if not videos:
        print("❌ No videos available")
        return
    
    print("📋 Copy videos to Desktop:")
    print("-" * 30)
    
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    if not os.path.exists(desktop):
        print("❌ Desktop folder not found")
        return
    
    for video in videos:
        try:
            # Copy final video
            src = os.path.join('outputs', video['files']['final'])
            dst = os.path.join(desktop, f"ai_video_{video['index']}.mp4")
            
            shutil.copy2(src, dst)
            print(f"✅ Copied: ai_video_{video['index']}.mp4 ({video['size_mb']:.1f}MB)")
            
            # Copy voice if exists
            if 'voice' in video['files']:
                voice_src = os.path.join('outputs', video['files']['voice'])
                voice_dst = os.path.join(desktop, f"ai_voice_{video['index']}.wav")
                shutil.copy2(voice_src, voice_dst)
                print(f"   🎵 Voice: ai_voice_{video['index']}.wav")
            
            # Copy SRT if exists
            if 'srt' in video['files']:
                srt_src = os.path.join('outputs', video['files']['srt'])
                srt_dst = os.path.join(desktop, f"ai_subtitles_{video['index']}.srt")
                shutil.copy2(srt_src, srt_dst)
                print(f"   📝 Subtitles: ai_subtitles_{video['index']}.srt")
            
        except Exception as e:
            print(f"❌ Error copying video {video['index']}: {e}")

def generate_download_urls(videos):
    """Generate download URLs for web access"""
    print("🌐 Download URLs (copy to browser):")
    print("-" * 50)
    
    base_url = "http://localhost:5000/api/download"
    
    for video in videos:
        task_id = video['task_id']
        print(f"\n📹 Video {video['index']} (Task: {task_id[:8]}...):")
        
        # Final video URL
        final_url = f"{base_url}/{task_id}/final"
        print(f"   🎬 Final Video: {final_url}")
        
        # Voice URL
        if 'voice' in video['files']:
            voice_url = f"{base_url}/{task_id}/voice"
            print(f"   🎵 Voice Audio: {voice_url}")
        
        # SRT URL
        if 'srt' in video['files']:
            srt_url = f"{base_url}/{task_id}/srt"
            print(f"   📝 Subtitles: {srt_url}")

def test_downloads(videos):
    """Test if download endpoints work"""
    print("🧪 Testing download endpoints...")
    print("-" * 40)
    
    base_url = "http://localhost:5000/api/download"
    
    for video in videos:
        task_id = video['task_id']
        print(f"\n📹 Testing Video {video['index']}:")
        
        # Test final video
        try:
            url = f"{base_url}/{task_id}/final"
            response = requests.head(url, timeout=5)
            if response.status_code == 200:
                print(f"   ✅ Final video: OK")
            else:
                print(f"   ❌ Final video: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Final video: Error - {e}")

def main():
    """Main function"""
    print_header()
    
    # List available videos
    videos = list_available_videos()
    
    if not videos:
        print("💡 No processed videos found!")
        print("   1. Go to http://localhost:5000")
        print("   2. Upload a video and process it")
        print("   3. Run this script again")
        return
    
    # Generate download URLs
    generate_download_urls(videos)
    
    # Test download endpoints
    test_downloads(videos)
    
    # Ask user what to do
    print("\n" + "=" * 50)
    print("💡 What would you like to do?")
    print("1. Copy all videos to Desktop")
    print("2. Just use the URLs above")
    print("3. Exit")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            copy_to_desktop(videos)
            print(f"\n✅ All videos copied to Desktop!")
            print(f"📁 Check your Desktop folder")
        elif choice == "2":
            print("\n📋 Copy the URLs above and paste into browser")
        else:
            print("\n👋 Goodbye!")
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main() 