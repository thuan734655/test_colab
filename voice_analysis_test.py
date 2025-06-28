#!/usr/bin/env python3
"""
Voice Analysis Test - Multi-AI TTS System
Tự động tạo lồng tiếng và phân tích kết quả
"""

import asyncio
import os
import time
import subprocess
import sys
from pathlib import Path

# Import TTSManager from main app
sys.path.append('.')
from main_app import tts_manager, TTSProvider

class VoiceAnalyzer:
    def __init__(self):
        self.test_texts = {
            'vi': [
                "Xin chào, tôi là trợ lý AI. Hôm nay thời tiết thật đẹp.",
                "Phụ thân, con thà chết chứ không gả cho Thất tiểu đệ!",
                "Mười tám năm trước, phụ thân Tiểu Đệ đã cứu mạng Hứa gia chúng ta."
            ],
            'en': [
                "Hello, I am an AI assistant. The weather is beautiful today.",
                "This is a test of the emergency broadcast system.",
                "Artificial intelligence is transforming the world we live in."
            ]
        }
        self.results = []
        self.output_dir = "voice_analysis_results"
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def test_voice_provider(self, provider, voices, language='vi'):
        """Test tất cả voices của một provider"""
        print(f"\n🔊 TESTING {provider.value.upper()}")
        print("=" * 60)
        
        provider_results = {
            'provider': provider.value,
            'language': language,
            'voices_tested': [],
            'total_voices': len(voices),
            'success_count': 0,
            'avg_generation_time': 0,
            'avg_file_size': 0
        }
        
        test_text = self.test_texts[language][0]  # Use first test text
        
        for i, voice in enumerate(voices):
            print(f"\n📢 Testing Voice {i+1}/{len(voices)}: {voice.name}")
            print(f"   ID: {voice.id}")
            print(f"   Quality: {voice.quality}")
            print(f"   Description: {voice.description}")
            
            voice_result = await self.test_single_voice(voice, test_text, language)
            provider_results['voices_tested'].append(voice_result)
            
            if voice_result['success']:
                provider_results['success_count'] += 1
                provider_results['avg_generation_time'] += voice_result['generation_time']
                provider_results['avg_file_size'] += voice_result['file_size_kb']
                
                # Log success
                print(f"   ✅ SUCCESS: {voice_result['generation_time']:.2f}s, {voice_result['file_size_kb']:.1f}KB")
                
                # Analyze audio quality
                audio_analysis = self.analyze_audio_file(voice_result['file_path'])
                voice_result.update(audio_analysis)
                
                if audio_analysis.get('duration'):
                    print(f"   🎵 Duration: {audio_analysis['duration']:.2f}s")
                if audio_analysis.get('sample_rate'):
                    print(f"   📊 Sample Rate: {audio_analysis['sample_rate']}Hz")
                if audio_analysis.get('channels'):
                    print(f"   🔊 Channels: {audio_analysis['channels']}")
                    
            else:
                print(f"   ❌ FAILED: {voice_result['error']}")
            
            # Small delay between tests
            await asyncio.sleep(0.5)
        
        # Calculate averages
        if provider_results['success_count'] > 0:
            provider_results['avg_generation_time'] /= provider_results['success_count']
            provider_results['avg_file_size'] /= provider_results['success_count']
        
        self.results.append(provider_results)
        return provider_results
    
    async def test_single_voice(self, voice, text, language):
        """Test một voice cụ thể"""
        start_time = time.time()
        
        # Create unique filename
        safe_name = voice.id.replace(':', '_').replace('/', '_')
        filename = f"{self.output_dir}/{voice.provider.value}_{safe_name}_{language}.wav"
        
        try:
            # Generate speech
            success = await tts_manager.generate_speech(
                text=text,
                voice_id=voice.id, 
                output_path=filename,
                speed=1.0
            )
            
            generation_time = time.time() - start_time
            
            if success and os.path.exists(filename):
                file_size = os.path.getsize(filename)
                file_size_kb = file_size / 1024
                
                return {
                    'voice_id': voice.id,
                    'voice_name': voice.name,
                    'success': True,
                    'generation_time': generation_time,
                    'file_size_bytes': file_size,
                    'file_size_kb': file_size_kb,
                    'file_path': filename,
                    'error': None
                }
            else:
                return {
                    'voice_id': voice.id,
                    'voice_name': voice.name,
                    'success': False,
                    'generation_time': generation_time,
                    'file_size_bytes': 0,
                    'file_size_kb': 0,
                    'file_path': None,
                    'error': 'File not generated'
                }
                
        except Exception as e:
            generation_time = time.time() - start_time
            return {
                'voice_id': voice.id,
                'voice_name': voice.name,
                'success': False,
                'generation_time': generation_time,
                'file_size_bytes': 0,
                'file_size_kb': 0,
                'file_path': None,
                'error': str(e)
            }
    
    def analyze_audio_file(self, file_path):
        """Phân tích file audio bằng ffprobe"""
        try:
            # Get audio info using ffprobe
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                
                audio_stream = None
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'audio':
                        audio_stream = stream
                        break
                
                if audio_stream:
                    duration = float(data.get('format', {}).get('duration', 0))
                    sample_rate = int(audio_stream.get('sample_rate', 0))
                    channels = int(audio_stream.get('channels', 0))
                    bit_rate = int(audio_stream.get('bit_rate', 0)) if audio_stream.get('bit_rate') else 0
                    
                    return {
                        'duration': duration,
                        'sample_rate': sample_rate,
                        'channels': channels,
                        'bit_rate': bit_rate,
                        'codec': audio_stream.get('codec_name', 'unknown')
                    }
            
            return {}
            
        except Exception as e:
            print(f"   ⚠️ Audio analysis failed: {e}")
            return {}
    
    def generate_analysis_report(self):
        """Tạo báo cáo phân tích chi tiết"""
        print("\n" + "="*80)
        print("📊 VOICE ANALYSIS REPORT")
        print("="*80)
        
        total_voices_tested = sum(r['total_voices'] for r in self.results)
        total_success = sum(r['success_count'] for r in self.results)
        
        print(f"🎤 Total Voices Tested: {total_voices_tested}")
        print(f"✅ Successful Generations: {total_success}")
        print(f"📈 Success Rate: {total_success/total_voices_tested*100:.1f}%")
        print()
        
        # Provider comparison
        print("🏭 PROVIDER COMPARISON:")
        print("-" * 80)
        
        working_providers = [r for r in self.results if r['success_count'] > 0]
        
        if working_providers:
            # Sort by success rate
            working_providers.sort(key=lambda x: x['success_count']/x['total_voices'], reverse=True)
            
            for result in working_providers:
                success_rate = result['success_count'] / result['total_voices'] * 100
                
                print(f"📢 {result['provider'].upper()}")
                print(f"   Success Rate: {success_rate:.1f}% ({result['success_count']}/{result['total_voices']})")
                print(f"   Avg Generation Time: {result['avg_generation_time']:.2f}s")
                print(f"   Avg File Size: {result['avg_file_size']:.1f}KB")
                
                # Quality assessment
                if success_rate == 100:
                    print("   Status: ✅ EXCELLENT")
                elif success_rate >= 80:
                    print("   Status: 🟢 GOOD") 
                elif success_rate >= 50:
                    print("   Status: 🟡 FAIR")
                else:
                    print("   Status: 🔴 POOR")
                print()
        
        # Speed ranking
        if working_providers:
            print("⚡ SPEED RANKING (fastest to slowest):")
            speed_ranking = sorted(working_providers, key=lambda x: x['avg_generation_time'])
            for i, result in enumerate(speed_ranking, 1):
                print(f"   {i}. {result['provider']}: {result['avg_generation_time']:.2f}s")
            print()
        
        # File size comparison
        if working_providers:
            print("📁 FILE SIZE COMPARISON:")
            size_ranking = sorted(working_providers, key=lambda x: x['avg_file_size'])
            for i, result in enumerate(size_ranking, 1):
                efficiency = "Efficient" if result['avg_file_size'] < 50 else "Standard" if result['avg_file_size'] < 100 else "Large"
                print(f"   {i}. {result['provider']}: {result['avg_file_size']:.1f}KB ({efficiency})")
            print()
        
        # Failed providers
        failed_providers = [r for r in self.results if r['success_count'] == 0]
        if failed_providers:
            print("❌ FAILED PROVIDERS:")
            for result in failed_providers:
                print(f"   {result['provider']}: Requires API key or setup")
            print()
        
        # Recommendations
        print("💡 RECOMMENDATIONS:")
        if working_providers:
            best_overall = working_providers[0]  # Already sorted by success rate
            fastest = min(working_providers, key=lambda x: x['avg_generation_time'])
            most_efficient = min(working_providers, key=lambda x: x['avg_file_size'])
            
            print(f"   🏆 Best Overall: {best_overall['provider']} ({best_overall['success_count']}/{best_overall['total_voices']} success)")
            print(f"   ⚡ Fastest: {fastest['provider']} ({fastest['avg_generation_time']:.2f}s avg)")
            print(f"   📁 Most Efficient: {most_efficient['provider']} ({most_efficient['avg_file_size']:.1f}KB avg)")
        
        print(f"\n📂 Generated files saved in: {self.output_dir}/")
        print("🎧 Listen to the samples to compare voice quality!")

async def main():
    """Main test function"""
    print("🎤 COMPREHENSIVE VOICE ANALYSIS TEST")
    print("=" * 80)
    print("🚀 Testing all available TTS providers...")
    print("⏱️  This may take several minutes depending on providers")
    print()
    
    analyzer = VoiceAnalyzer()
    
    # Test Vietnamese voices first
    print("🇻🇳 TESTING VIETNAMESE VOICES")
    vi_voices = tts_manager.get_available_voices('vi')
    
    if vi_voices:
        # Group by provider
        providers_vi = {}
        for voice in vi_voices:
            if voice.provider not in providers_vi:
                providers_vi[voice.provider] = []
            providers_vi[voice.provider].append(voice)
        
        # Test each provider
        for provider, voices in providers_vi.items():
            await analyzer.test_voice_provider(provider, voices, 'vi')
    else:
        print("❌ No Vietnamese voices found!")
    
    # Test English voices (first 2 from each provider for speed)
    print("\n🇺🇸 TESTING ENGLISH VOICES (SAMPLE)")
    en_voices = tts_manager.get_available_voices('en')
    
    if en_voices:
        # Group by provider and take first 2
        providers_en = {}
        for voice in en_voices:
            if voice.provider not in providers_en:
                providers_en[voice.provider] = []
            if len(providers_en[voice.provider]) < 2:  # Limit to 2 per provider
                providers_en[voice.provider].append(voice)
        
        # Test each provider
        for provider, voices in providers_en.items():
            await analyzer.test_voice_provider(provider, voices, 'en')
    
    # Generate final report
    analyzer.generate_analysis_report()

if __name__ == "__main__":
    print("🎯 Starting comprehensive voice analysis...")
    print("Make sure the TTS system is properly initialized...")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc() 