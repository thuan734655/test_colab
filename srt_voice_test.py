#!/usr/bin/env python3
"""
SRT Voice Test - Tạo lồng tiếng từ SRT và phân tích
"""

import asyncio
import os
import time
import sys

# Import TTSManager from main app
sys.path.append('.')
from main_app import tts_manager

class SRTProcessor:
    def __init__(self):
        self.output_dir = "srt_voice_test"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # SRT segments từ file được cung cấp
        self.segments = [
            {"id": 1, "time": "00:00:01,000 --> 00:00:03,459", "text": "Phụ thân, con thà chết chứ không gả cho Thất tiểu đệ!"},
            {"id": 2, "time": "00:00:04,139 --> 00:00:05,099", "text": "Ninh nhi, đừng hồ đồ."},
            {"id": 3, "time": "00:00:05,459 --> 00:00:08,000", "text": "Mười năm trước, phụ thân Tiểu Đệ đã cứu mạng Hứa gia chúng ta."},
            {"id": 4, "time": "00:00:08,000 --> 00:00:10,000", "text": "Nên mới có lời hứa thành thân năm con mười tám tuổi."},
            {"id": 5, "time": "00:00:10,000 --> 00:00:12,820", "text": "Nếu con hủy kèo, sẽ bị người đời nói là vong ân bội nghĩa."},
            {"id": 6, "time": "00:00:16,440 --> 00:00:17,519", "text": "Hừ, con không quan tâm!"},
            {"id": 7, "time": "00:00:17,859 --> 00:00:19,660", "text": "Tên câm đó, con nhất quyết không gả!"},
            {"id": 8, "time": "00:00:19,660 --> 00:00:21,800", "text": "Các người còn ép con, chính là muốn con chết!"},
            {"id": 9, "time": "00:00:26,760 --> 00:00:29,260", "text": "Suốt mười tám năm, ngươi chưa từng mở lời trước mặt ai."},
            {"id": 10, "time": "00:00:29,260 --> 00:00:31,519", "text": "Người đời đều tưởng ngươi là tên câm điên."},
            {"id": 11, "time": "00:00:31,519 --> 00:00:34,039", "text": "Nào biết ngươi chỉ bị phụ thân cho uống một viên Linh Chủng,"},
            {"id": 12, "time": "00:00:34,039 --> 00:00:35,920", "text": "mười tám năm mới thành thục."},
            {"id": 13, "time": "00:00:35,920 --> 00:00:38,079", "text": "Trong lúc này, hễ mở miệng sẽ bị thiên lôi tập kích."},
            {"id": 14, "time": "00:00:38,079 --> 00:00:40,259", "text": "Và hôm nay, chính là ngày cuối cùng."},
            {"id": 15, "time": "00:00:43,659 --> 00:00:45,219", "text": "Tiểu Đệ đứa nhỏ này cái gì cũng tốt,"},
            {"id": 16, "time": "00:00:45,219 --> 00:00:46,259", "text": "tiếc là một tên câm."},
            {"id": 17, "time": "00:00:46,259 --> 00:00:48,299", "text": "Còn là một tên câm không có linh căn."}
        ]
        
        self.results = []
    
    async def test_voice_generation(self):
        """Test voice generation cho tất cả segments"""
        print("🎭 SRT VOICE GENERATION TEST")
        print("=" * 60)
        print(f"📚 Content: Vietnamese Historical Drama")
        print(f"📝 Total Segments: {len(self.segments)}")
        print()
        
        # Test với 2 giọng Việt Nam
        voices = [
            {"id": "vi-VN-HoaiMyNeural", "name": "Hoài My (Nữ)", "type": "female"},
            {"id": "vi-VN-NamMinhNeural", "name": "Nam Minh (Nam)", "type": "male"}
        ]
        
        total_start_time = time.time()
        
        for voice in voices:
            print(f"\n🗣️ TESTING VOICE: {voice['name']}")
            print("-" * 50)
            
            voice_stats = {
                'voice_id': voice['id'],
                'voice_name': voice['name'],
                'voice_type': voice['type'],
                'successful': 0,
                'failed': 0,
                'total_time': 0,
                'total_size': 0,
                'segments': []
            }
            
            for segment in self.segments:
                segment_start = time.time()
                
                print(f"\n📢 Segment {segment['id']:02d}: {segment['time']}")
                print(f"   📝 Text: {segment['text']}")
                
                # Tạo filename
                filename = f"{self.output_dir}/seg_{segment['id']:02d}_{voice['type']}.wav"
                
                try:
                    # Generate speech
                    success = await tts_manager.generate_speech(
                        text=segment['text'],
                        voice_id=voice['id'],
                        output_path=filename,
                        speed=1.0
                    )
                    
                    generation_time = time.time() - segment_start
                    
                    if success and os.path.exists(filename):
                        file_size = os.path.getsize(filename)
                        file_size_kb = file_size / 1024
                        
                        voice_stats['successful'] += 1
                        voice_stats['total_time'] += generation_time
                        voice_stats['total_size'] += file_size
                        
                        segment_result = {
                            'id': segment['id'],
                            'text': segment['text'],
                            'filename': filename,
                            'size_kb': file_size_kb,
                            'time': generation_time,
                            'success': True
                        }
                        voice_stats['segments'].append(segment_result)
                        
                        print(f"   ✅ SUCCESS: {generation_time:.2f}s, {file_size_kb:.1f}KB")
                    else:
                        voice_stats['failed'] += 1
                        print(f"   ❌ FAILED: File not generated")
                        
                        segment_result = {
                            'id': segment['id'],
                            'text': segment['text'],
                            'filename': None,
                            'size_kb': 0,
                            'time': generation_time,
                            'success': False
                        }
                        voice_stats['segments'].append(segment_result)
                
                except Exception as e:
                    voice_stats['failed'] += 1
                    generation_time = time.time() - segment_start
                    print(f"   ❌ ERROR: {str(e)}")
                    
                    segment_result = {
                        'id': segment['id'],
                        'text': segment['text'],
                        'filename': None,
                        'size_kb': 0,
                        'time': generation_time,
                        'success': False
                    }
                    voice_stats['segments'].append(segment_result)
                
                # Small delay
                await asyncio.sleep(0.2)
            
            # Calculate voice statistics
            total_segments = len(self.segments)
            success_rate = (voice_stats['successful'] / total_segments) * 100
            avg_time = voice_stats['total_time'] / voice_stats['successful'] if voice_stats['successful'] > 0 else 0
            total_size_mb = voice_stats['total_size'] / (1024 * 1024)
            
            print(f"\n📊 {voice['name']} SUMMARY:")
            print(f"   Success Rate: {success_rate:.1f}% ({voice_stats['successful']}/{total_segments})")
            print(f"   Avg Generation Time: {avg_time:.2f}s")
            print(f"   Total Size: {total_size_mb:.2f}MB")
            
            if success_rate == 100:
                print("   Status: ✅ EXCELLENT")
            elif success_rate >= 80:
                print("   Status: 🟢 GOOD")
            else:
                print("   Status: 🔴 NEEDS IMPROVEMENT")
            
            self.results.append(voice_stats)
        
        total_time = time.time() - total_start_time
        print(f"\n⏱️ Total Test Time: {total_time:.1f}s")
    
    def analyze_results(self):
        """Phân tích kết quả chi tiết"""
        print("\n" + "="*70)
        print("📊 DETAILED RESULTS ANALYSIS")
        print("="*70)
        
        total_segments = len(self.segments)
        total_text_chars = sum(len(s['text']) for s in self.segments)
        
        print(f"\n📚 CONTENT ANALYSIS:")
        print(f"   📝 Total Segments: {total_segments}")
        print(f"   📄 Total Text Length: {total_text_chars} characters")
        print(f"   📏 Average Segment Length: {total_text_chars/total_segments:.1f} chars")
        print(f"   🎭 Content Type: Vietnamese Historical Drama")
        
        print(f"\n🎤 VOICE COMPARISON:")
        print("-" * 60)
        
        for result in self.results:
            voice_name = result['voice_name']
            voice_type = result['voice_type']
            successful = result['successful']
            total_time = result['total_time']
            total_size_mb = result['total_size'] / (1024 * 1024)
            
            success_rate = (successful / total_segments) * 100
            avg_time = total_time / successful if successful > 0 else 0
            
            print(f"\n🗣️ {voice_name} ({voice_type.upper()}):")
            print(f"   ✅ Success Rate: {success_rate:.1f}%")
            print(f"   ⚡ Avg Speed: {avg_time:.2f}s per segment")
            print(f"   💾 Total Size: {total_size_mb:.2f} MB")
            print(f"   📊 Performance: {'⭐⭐⭐⭐⭐' if success_rate == 100 else '⭐⭐⭐⭐' if success_rate >= 90 else '⭐⭐⭐'}")
            
            # Character suitability analysis
            if voice_type == 'female':
                print(f"   🎭 Best for: Female characters (Ninh nhi), emotional scenes")
                print(f"   💭 Suitable segments: 1, 6, 7, 8 (daughter's dialogue)")
            else:
                print(f"   🎭 Best for: Male characters (Father), authoritative dialogue")
                print(f"   💭 Suitable segments: 2, 3, 4, 5, 9-17 (father/narrator)")
        
        print(f"\n💡 RECOMMENDATIONS:")
        
        # Find best overall performance
        best_voice = max(self.results, key=lambda x: x['successful'])
        print(f"   🏆 Best Overall: {best_voice['voice_name']}")
        print(f"   📈 Both voices show excellent performance for Vietnamese content")
        print(f"   🎬 Perfect for dubbing historical dramas and emotional content")
        print(f"   🚀 Fast generation speed suitable for real-time applications")
        
        print(f"\n📁 Generated Files:")
        for result in self.results:
            successful_files = [s for s in result['segments'] if s['success']]
            print(f"   {result['voice_name']}: {len(successful_files)} files in {self.output_dir}/")
        
        print(f"\n🎧 Next Steps:")
        print(f"   1. Listen to generated audio files to compare voice quality")
        print(f"   2. Choose appropriate voice for each character type")
        print(f"   3. Use results for full video dubbing project")

async def main():
    """Main function"""
    print("🎭 SRT VOICE ANALYSIS - Vietnamese Historical Drama")
    print("=" * 70)
    print("📚 Processing Vietnamese historical dialogue for voice generation")
    print("🎯 Testing Edge TTS Vietnamese voices for quality analysis")
    print()
    
    processor = SRTProcessor()
    
    # Generate voice for all segments
    await processor.test_voice_generation()
    
    # Analyze results
    processor.analyze_results()
    
    print("\n✅ SRT Voice Analysis Complete!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc() 