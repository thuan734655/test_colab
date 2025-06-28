#!/usr/bin/env python3
"""
Audio Quality Test & Playback
Nghe thử và phân tích chất lượng audio
"""

import os
import subprocess
import json
import time
import sys
from pathlib import Path

class AudioQualityAnalyzer:
    def __init__(self, results_dir="voice_analysis_results"):
        self.results_dir = results_dir
        self.audio_files = []
        self.discover_audio_files()
    
    def discover_audio_files(self):
        """Tìm tất cả file audio trong thư mục results"""
        if not os.path.exists(self.results_dir):
            print(f"❌ Results directory not found: {self.results_dir}")
            return
        
        for file in os.listdir(self.results_dir):
            if file.endswith('.wav'):
                full_path = os.path.join(self.results_dir, file)
                file_info = self.parse_filename(file)
                file_info['path'] = full_path
                file_info['size_mb'] = os.path.getsize(full_path) / (1024 * 1024)
                self.audio_files.append(file_info)
        
        # Sort by provider and language
        self.audio_files.sort(key=lambda x: (x['provider'], x['language'], x['voice_id']))
    
    def parse_filename(self, filename):
        """Parse filename to extract info"""
        # Format: provider_voice-id_language.wav
        name_without_ext = filename.replace('.wav', '')
        parts = name_without_ext.split('_', 2)
        
        if len(parts) >= 3:
            provider = parts[0]
            voice_id_part = parts[1]
            language = parts[2]
            
            return {
                'filename': filename,
                'provider': provider,
                'voice_id': voice_id_part,
                'language': language,
                'full_voice_id': '_'.join(parts[1:-1])  # Everything except provider and language
            }
        
        return {
            'filename': filename,
            'provider': 'unknown',
            'voice_id': 'unknown',
            'language': 'unknown',
            'full_voice_id': 'unknown'
        }
    
    def analyze_audio_properties(self, file_path):
        """Phân tích chi tiết properties của audio file"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                audio_stream = None
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'audio':
                        audio_stream = stream
                        break
                
                if audio_stream:
                    format_info = data.get('format', {})
                    
                    return {
                        'duration': float(format_info.get('duration', 0)),
                        'size_bytes': int(format_info.get('size', 0)),
                        'bit_rate': int(format_info.get('bit_rate', 0)),
                        'sample_rate': int(audio_stream.get('sample_rate', 0)),
                        'channels': int(audio_stream.get('channels', 0)),
                        'codec': audio_stream.get('codec_name', 'unknown'),
                        'bits_per_sample': audio_stream.get('bits_per_raw_sample', 'N/A')
                    }
            
            return None
            
        except Exception as e:
            print(f"⚠️ Failed to analyze {file_path}: {e}")
            return None
    
    def play_audio_file(self, file_path):
        """Play audio file using system default player"""
        try:
            print(f"🎵 Playing: {os.path.basename(file_path)}")
            
            # Try different methods to play audio
            if sys.platform.startswith('win'):
                # Windows - use default media player
                os.startfile(file_path)
                print("   ✅ Opened with default Windows media player")
            elif sys.platform.startswith('darwin'):
                # macOS
                subprocess.run(['open', file_path])
                print("   ✅ Opened with default macOS player")  
            else:
                # Linux
                subprocess.run(['xdg-open', file_path])
                print("   ✅ Opened with default Linux player")
                
            # Give time for player to start
            time.sleep(1)
            
        except Exception as e:
            print(f"   ❌ Failed to play audio: {e}")
            print(f"   📁 You can manually open: {file_path}")
    
    def generate_quality_report(self):
        """Tạo báo cáo chi tiết về chất lượng audio"""
        print("\n" + "="*80)
        print("🎧 DETAILED AUDIO QUALITY ANALYSIS")
        print("="*80)
        
        if not self.audio_files:
            print("❌ No audio files found to analyze")
            return
        
        print(f"📁 Found {len(self.audio_files)} audio files")
        print()
        
        # Group by provider for comparison
        providers = {}
        for audio in self.audio_files:
            provider = audio['provider']
            if provider not in providers:
                providers[provider] = []
            providers[provider].append(audio)
        
        for provider, files in providers.items():
            print(f"🔊 {provider.upper()} ANALYSIS:")
            print("-" * 60)
            
            for audio in files:
                print(f"\n📢 {audio['filename']}")
                print(f"   Language: {audio['language']}")
                print(f"   Voice ID: {audio['full_voice_id']}")
                print(f"   File Size: {audio['size_mb']:.2f} MB")
                
                # Analyze audio properties
                props = self.analyze_audio_properties(audio['path'])
                if props:
                    print(f"   🎵 Duration: {props['duration']:.2f}s")
                    print(f"   📊 Sample Rate: {props['sample_rate']} Hz")
                    print(f"   🔊 Channels: {props['channels']}")
                    print(f"   💾 Bit Rate: {props['bit_rate']} bps")
                    print(f"   🎼 Codec: {props['codec']}")
                    
                    # Quality assessment
                    quality_score = self.assess_quality(props)
                    print(f"   ⭐ Quality Score: {quality_score}/10")
                    
                    if quality_score >= 8:
                        print("   Status: ✅ EXCELLENT")
                    elif quality_score >= 6:
                        print("   Status: 🟢 GOOD")
                    elif quality_score >= 4:
                        print("   Status: 🟡 FAIR")
                    else:
                        print("   Status: 🔴 POOR")
                else:
                    print("   ❌ Could not analyze audio properties")
            
            print()
        
        # Overall comparison
        self.generate_comparison_table()
    
    def assess_quality(self, props):
        """Đánh giá chất lượng audio dựa trên properties"""
        score = 0
        
        # Sample rate scoring (max 3 points)
        if props['sample_rate'] >= 48000:
            score += 3
        elif props['sample_rate'] >= 24000:
            score += 2.5
        elif props['sample_rate'] >= 16000:
            score += 2
        elif props['sample_rate'] >= 8000:
            score += 1
        
        # Bit rate scoring (max 3 points)
        if props['bit_rate'] >= 256000:
            score += 3
        elif props['bit_rate'] >= 128000:
            score += 2.5
        elif props['bit_rate'] >= 64000:
            score += 2
        elif props['bit_rate'] >= 32000:
            score += 1
        
        # Duration scoring (max 2 points) - should be around 5-6 seconds for our test
        duration = props['duration']
        if 5.0 <= duration <= 6.0:
            score += 2
        elif 4.0 <= duration <= 7.0:
            score += 1.5
        elif 3.0 <= duration <= 8.0:
            score += 1
        
        # Channels scoring (max 1 point)
        if props['channels'] == 1:  # Mono is fine for TTS
            score += 1
        elif props['channels'] == 2:  # Stereo
            score += 0.8
        
        # Codec scoring (max 1 point)
        if props['codec'] in ['pcm_s16le', 'pcm_s24le', 'pcm_f32le']:
            score += 1
        elif props['codec'] in ['mp3', 'aac']:
            score += 0.8
        
        return min(score, 10)  # Cap at 10
    
    def generate_comparison_table(self):
        """Tạo bảng so sánh providers"""
        print("📊 PROVIDER COMPARISON TABLE:")
        print("-" * 80)
        
        # Calculate averages by provider
        provider_stats = {}
        
        for audio in self.audio_files:
            provider = audio['provider']
            props = self.analyze_audio_properties(audio['path'])
            
            if props and provider not in provider_stats:
                provider_stats[provider] = {
                    'count': 0,
                    'total_duration': 0,
                    'total_size': 0,
                    'total_quality': 0,
                    'sample_rates': [],
                    'bit_rates': []
                }
            
            if props:
                stats = provider_stats[provider]
                stats['count'] += 1
                stats['total_duration'] += props['duration']
                stats['total_size'] += audio['size_mb']
                stats['total_quality'] += self.assess_quality(props)
                stats['sample_rates'].append(props['sample_rate'])
                stats['bit_rates'].append(props['bit_rate'])
        
        # Print comparison
        print(f"{'Provider':<15} {'Avg Quality':<12} {'Avg Duration':<12} {'Avg Size':<10} {'Sample Rate':<12}")
        print("-" * 80)
        
        for provider, stats in provider_stats.items():
            if stats['count'] > 0:
                avg_quality = stats['total_quality'] / stats['count']
                avg_duration = stats['total_duration'] / stats['count'] 
                avg_size = stats['total_size'] / stats['count']
                avg_sample_rate = sum(stats['sample_rates']) / len(stats['sample_rates'])
                
                print(f"{provider:<15} {avg_quality:<12.1f} {avg_duration:<12.2f}s {avg_size:<10.2f}MB {avg_sample_rate:<12.0f}Hz")
        
        print()
    
    def interactive_playback(self):
        """Interactive mode để nghe từng file"""
        print("\n🎮 INTERACTIVE PLAYBACK MODE")
        print("=" * 60)
        print("Chọn file để nghe (hoặc 'all' để nghe tất cả):")
        print()
        
        for i, audio in enumerate(self.audio_files, 1):
            print(f"{i}. {audio['provider']} - {audio['language']} - {audio['full_voice_id']}")
        
        print(f"\n{len(self.audio_files) + 1}. Play all files")
        print(f"{len(self.audio_files) + 2}. Exit")
        
        while True:
            try:
                choice = input(f"\nChọn (1-{len(self.audio_files) + 2}): ").strip()
                
                if choice == str(len(self.audio_files) + 2) or choice.lower() == 'exit':
                    break
                elif choice == str(len(self.audio_files) + 1) or choice.lower() == 'all':
                    print("\n🎵 Playing all files sequentially...")
                    for audio in self.audio_files:
                        print(f"\n▶️  Now playing: {audio['provider']} - {audio['language']}")
                        self.play_audio_file(audio['path'])
                        input("Press Enter to continue to next file...")
                else:
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(self.audio_files):
                        audio = self.audio_files[choice_num - 1]
                        print(f"\n▶️  Playing: {audio['provider']} - {audio['language']}")
                        self.play_audio_file(audio['path'])
                    else:
                        print("❌ Invalid choice!")
                        
            except (ValueError, KeyboardInterrupt):
                print("\n👋 Exiting interactive mode...")
                break

def main():
    """Main function"""
    print("🎧 AUDIO QUALITY ANALYSIS & PLAYBACK TEST")
    print("=" * 80)
    
    analyzer = AudioQualityAnalyzer()
    
    if not analyzer.audio_files:
        print("❌ No audio files found. Run voice_analysis_test.py first!")
        return
    
    # Generate quality report
    analyzer.generate_quality_report()
    
    # Ask user if they want interactive playback
    print("\n" + "="*80)
    choice = input("🎮 Do you want to listen to the audio files? (y/n): ").strip().lower()
    
    if choice in ['y', 'yes']:
        analyzer.interactive_playback()
    
    print("\n✅ Audio quality analysis completed!")
    print(f"📁 Audio files location: {analyzer.results_dir}/")

if __name__ == "__main__":
    main() 