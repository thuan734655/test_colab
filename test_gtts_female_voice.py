#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test gTTS Female Vietnamese Voice - Tạo audio test giọng nữ tiếng Việt
"""

import asyncio
import tempfile
import os
import sys
from gtts import gTTS
from pydub import AudioSegment
import subprocess

async def create_gtts_test_audio():
    """Tạo file audio test với gTTS giọng nữ tiếng Việt"""
    
    print("🎤 TẠO AUDIO TEST - GIỌNG NỮ GTTS TIẾNG VIỆT")
    print("=" * 60)
    
    # Text test với giọng miền Bắc
    test_texts = [
        "Xin chào, tôi là giọng đọc tiếng Việt từ Google Text-to-Speech.",
        "Đây là bản demo giọng nữ miền Bắc với chất lượng tự nhiên.",
        "Ứng dụng đã tích hợp thành công giọng nói tiếng Việt miễn phí.",
        "Cảm ơn bạn đã sử dụng tính năng tạo subtitle với giọng nữ Việt Nam."
    ]
    
    full_text = " ".join(test_texts)
    print(f"📝 Text để đọc:")
    print(f"   '{full_text}'")
    print()
    
    try:
        # Tạo thư mục tạm
        temp_dir = tempfile.mkdtemp()
        mp3_path = os.path.join(temp_dir, "gtts_test.mp3")
        wav_path = os.path.join(temp_dir, "gtts_vietnamese_female_test.wav")
        
        print("🔊 Đang tạo audio với gTTS...")
        
        # Tạo gTTS object với tiếng Việt
        tts = gTTS(text=full_text, lang='vi', slow=False)
        tts.save(mp3_path)
        
        print(f"✅ Đã tạo MP3: {mp3_path}")
        
        # Convert MP3 to WAV using pydub
        print("🔄 Chuyển đổi MP3 sang WAV...")
        audio = AudioSegment.from_mp3(mp3_path)
        audio.export(wav_path, format="wav")
        
        print(f"✅ Đã tạo WAV: {wav_path}")
        
        # Kiểm tra file size
        wav_size = os.path.getsize(wav_path)
        mp3_size = os.path.getsize(mp3_path)
        
        print()
        print("📊 THÔNG TIN FILE AUDIO:")
        print(f"   💾 File MP3: {mp3_size:,} bytes")
        print(f"   💾 File WAV: {wav_size:,} bytes")
        print(f"   ⏱️  Độ dài audio: {len(audio) / 1000:.1f} giây")
        print(f"   🎵 Sample rate: {audio.frame_rate} Hz")
        print(f"   🔊 Channels: {audio.channels}")
        
        # Copy file đến thư mục hiện tại để user dễ tìm
        final_path = "gtts_vietnamese_female_demo.wav"
        audio.export(final_path, format="wav")
        
        print()
        print("🎉 HOÀN THÀNH!")
        print(f"📁 File audio đã được lưu: {final_path}")
        print("🎧 Bạn có thể phát file này để nghe thử giọng nữ gTTS tiếng Việt")
        
        # Thử phát audio nếu có VLC hoặc player khác
        try:
            if os.name == 'nt':  # Windows
                os.startfile(final_path)
                print("🔊 Đã mở file audio bằng trình phát mặc định")
        except:
            print("💡 Hãy mở file 'gtts_vietnamese_female_demo.wav' bằng trình phát nhạc để nghe")
        
        # Dọn dẹp thư mục tạm
        try:
            os.remove(mp3_path)
            os.remove(wav_path)
            os.rmdir(temp_dir)
        except:
            pass
            
        return True
        
    except Exception as e:
        print(f"❌ Lỗi khi tạo audio: {str(e)}")
        return False

async def test_speed_variations():
    """Test các tốc độ khác nhau của gTTS"""
    
    print("\n🚀 TEST CÁC TỐC ĐỘ KHÁC NHAU")
    print("=" * 40)
    
    test_text = "Đây là test tốc độ đọc của giọng gTTS tiếng Việt."
    
    speeds = [
        (False, "Tốc độ bình thường"),
        (True, "Tốc độ chậm")
    ]
    
    for slow, description in speeds:
        try:
            print(f"🎵 Tạo audio: {description}")
            
            tts = gTTS(text=test_text, lang='vi', slow=slow)
            filename = f"gtts_speed_{'slow' if slow else 'normal'}.wav"
            
            # Tạo MP3 tạm
            temp_mp3 = f"temp_{filename.replace('.wav', '.mp3')}"
            tts.save(temp_mp3)
            
            # Convert sang WAV
            audio = AudioSegment.from_mp3(temp_mp3)
            audio.export(filename, format="wav")
            
            print(f"   ✅ Đã tạo: {filename}")
            
            # Dọn dẹp
            os.remove(temp_mp3)
            
        except Exception as e:
            print(f"   ❌ Lỗi: {str(e)}")

if __name__ == "__main__":
    asyncio.run(create_gtts_test_audio())
    asyncio.run(test_speed_variations()) 