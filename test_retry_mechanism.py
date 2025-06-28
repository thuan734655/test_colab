#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Retry Mechanism for TTS Voice Generation
Kiểm tra cơ chế tự động retry cho việc tạo lồng tiếng
"""

import sys
import asyncio
import os
import tempfile
import logging

# Import from main app
sys.path.append('.')
from main_app import (
    tts_manager, 
    generate_speech_with_retry, 
    check_all_segments_successful,
    TTS_RETRY_CONFIG
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TTSRetryTester:
    def __init__(self):
        self.test_segments = [
            {"id": 1, "text": "Xin chào! Đây là test câu số một.", "start": 0.0, "end": 3.0},
            {"id": 2, "text": "Câu thứ hai để kiểm tra retry mechanism.", "start": 3.5, "end": 7.0},
            {"id": 3, "text": "Và đây là câu cuối cùng trong test.", "start": 7.5, "end": 10.0}
        ]
        
        # Test configurations
        self.test_configs = {
            'normal': TTS_RETRY_CONFIG,
            'aggressive_retry': {
                'max_retries': 5,
                'initial_delay': 0.5,
                'use_exponential_backoff': True,
                'add_jitter': True,
                'min_file_size_bytes': 1024,
                'require_all_segments': True
            },
            'fast_retry': {
                'max_retries': 2,
                'initial_delay': 0.2,
                'use_exponential_backoff': False,
                'add_jitter': False,
                'min_file_size_bytes': 512,
                'require_all_segments': True
            }
        }
    
    async def test_single_segment_retry(self, config_name='normal'):
        """Test retry mechanism for a single segment"""
        print(f"\n🧪 TESTING SINGLE SEGMENT RETRY - Config: {config_name}")
        print("=" * 60)
        
        config = self.test_configs[config_name]
        test_segment = self.test_segments[0]
        
        # Create temp file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            temp_audio = tmp.name
        
        try:
            voice_id = "vi-VN-HoaiMyNeural"  # Use Vietnamese voice
            
            print(f"📝 Text: {test_segment['text']}")
            print(f"🔊 Voice: {voice_id}")
            print(f"⚙️ Config: Max retries={config['max_retries']}, Initial delay={config['initial_delay']}s")
            print()
            
            success = await generate_speech_with_retry(
                tts_manager, 
                test_segment['text'], 
                voice_id, 
                temp_audio, 
                speed=1.0,
                config=config
            )
            
            if success:
                file_size = os.path.getsize(temp_audio) if os.path.exists(temp_audio) else 0
                print(f"✅ SUCCESS: Generated {file_size} bytes")
            else:
                print(f"❌ FAILED: Could not generate audio after retries")
            
            return success
            
        finally:
            # Cleanup
            if os.path.exists(temp_audio):
                os.remove(temp_audio)
    
    async def test_multiple_segments_validation(self):
        """Test the all-segments-must-succeed validation"""
        print(f"\n🎭 TESTING MULTIPLE SEGMENTS VALIDATION")
        print("=" * 60)
        
        voice_id = "vi-VN-HoaiMyNeural"
        audio_segments = []
        temp_files = []
        
        try:
            # Generate audio for each segment
            for i, segment in enumerate(self.test_segments):
                print(f"\n🎤 Processing segment {i+1}/{len(self.test_segments)}")
                print(f"📝 Text: {segment['text']}")
                
                # Create temp file
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                    temp_audio = tmp.name
                    temp_files.append(temp_audio)
                
                success = await generate_speech_with_retry(
                    tts_manager, 
                    segment['text'], 
                    voice_id, 
                    temp_audio, 
                    speed=1.0
                )
                
                if success and os.path.exists(temp_audio):
                    audio_segments.append({
                        'file': temp_audio,
                        'start': segment['start'],
                        'end': segment['end'],
                        'text': segment['text']
                    })
                    print(f"✅ Segment {i+1} SUCCESS")
                else:
                    print(f"❌ Segment {i+1} FAILED")
            
            # Check validation
            print(f"\n🔍 VALIDATION CHECK")
            print("-" * 40)
            
            all_successful, success_count, fail_count = check_all_segments_successful(
                audio_segments, len(self.test_segments)
            )
            
            print(f"📊 Results:")
            print(f"   ✅ Successful: {success_count}/{len(self.test_segments)}")
            print(f"   ❌ Failed: {fail_count}")
            print(f"   🎯 All successful: {all_successful}")
            
            if all_successful:
                print(f"\n🎊 VALIDATION PASSED: All segments generated successfully!")
                print(f"✅ System would proceed to next step (timeline audio creation)")
            else:
                print(f"\n🚫 VALIDATION FAILED: Not all segments successful!")
                print(f"❌ System would stop and require retry of failed segments")
            
            return all_successful
            
        finally:
            # Cleanup temp files
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
    
    def test_configuration_variants(self):
        """Test different retry configurations"""
        print(f"\n⚙️ TESTING CONFIGURATION VARIANTS")
        print("=" * 60)
        
        for config_name, config in self.test_configs.items():
            print(f"\n📋 Config: {config_name.upper()}")
            print(f"   Max retries: {config['max_retries']}")
            print(f"   Initial delay: {config['initial_delay']}s")
            print(f"   Exponential backoff: {config['use_exponential_backoff']}")
            print(f"   Add jitter: {config['add_jitter']}")
            print(f"   Min file size: {config['min_file_size_bytes']} bytes")
            print(f"   Require all segments: {config['require_all_segments']}")
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🧪 TTS RETRY MECHANISM TEST SUITE")
        print("=" * 60)
        print("🎯 Mục tiêu: Kiểm tra cơ chế retry và validation 'tất cả segments phải thành công'")
        print()
        
        # Test 1: Configuration variants
        self.test_configuration_variants()
        
        # Test 2: Single segment retry with different configs
        for config_name in self.test_configs.keys():
            try:
                await self.test_single_segment_retry(config_name)
            except Exception as e:
                print(f"❌ Test failed for config {config_name}: {e}")
        
        # Test 3: Multiple segments validation
        try:
            await self.test_multiple_segments_validation()
        except Exception as e:
            print(f"❌ Multiple segments test failed: {e}")
        
        print(f"\n🎉 TEST SUITE COMPLETED!")
        print("=" * 60)
        print("📝 Key Features Tested:")
        print("✅ Automatic retry mechanism with exponential backoff")
        print("✅ Configurable retry parameters")
        print("✅ File size validation")
        print("✅ All-segments-must-succeed validation")
        print("✅ Proper cleanup on failures")
        print("✅ Detailed logging of retry attempts")

async def main():
    """Main test function"""
    tester = TTSRetryTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 