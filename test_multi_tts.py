#!/usr/bin/env python3
"""
Multi-AI TTS System Test Script
Test all available TTS providers and voices
"""

import asyncio
import os
import sys
from main_app import tts_manager, TTSProvider

async def test_all_providers():
    """Test all TTS providers with sample text"""
    
    test_text = "Xin chào, đây là test giọng nói tiếng Việt."
    test_text_en = "Hello, this is a voice test in English."
    
    print("🎤 MULTI-AI TTS SYSTEM TEST")
    print("=" * 60)
    
    # Get all available voices
    all_voices = tts_manager.get_available_voices()
    print(f"📊 Total voices available: {len(all_voices)}")
    
    # Group by provider
    providers = {}
    for voice in all_voices:
        provider = voice.provider.value
        if provider not in providers:
            providers[provider] = []
        providers[provider].append(voice)
    
    print(f"🏭 Providers found: {list(providers.keys())}\n")
    
    # Test each provider
    for provider_name, voices in providers.items():
        print(f"🔊 TESTING {provider_name.upper()}")
        print("-" * 40)
        
        # Test first voice for this provider
        if voices:
            voice = voices[0]
            print(f"Voice: {voice.name}")
            print(f"Language: {voice.language}")
            print(f"Quality: {voice.quality}")
            print(f"Description: {voice.description}")
            
            # Choose appropriate test text
            text = test_text if voice.language == 'vi' else test_text_en
            output_file = f"test_{provider_name}_{voice.language}.wav"
            
            try:
                print(f"Generating audio: {output_file}...")
                success = await tts_manager.generate_speech(
                    text, voice.id, output_file, speed=1.0
                )
                
                if success and os.path.exists(output_file):
                    file_size = os.path.getsize(output_file) / 1024
                    print(f"✅ SUCCESS! Generated {file_size:.1f}KB")
                else:
                    print("❌ FAILED!")
                    
            except Exception as e:
                print(f"❌ ERROR: {e}")
        
        print()

def test_voice_listing():
    """Test voice listing APIs"""
    print("📋 TESTING VOICE LISTING")
    print("=" * 40)
    
    # Test get all voices
    all_voices = tts_manager.get_available_voices()
    print(f"Total voices: {len(all_voices)}")
    
    # Test filter by language
    vi_voices = tts_manager.get_available_voices('vi')
    print(f"Vietnamese voices: {len(vi_voices)}")
    
    en_voices = tts_manager.get_available_voices('en')
    print(f"English voices: {len(en_voices)}")
    
    # Test filter by provider
    edge_voices = tts_manager.get_available_voices(provider=TTSProvider.EDGE_TTS)
    print(f"Edge TTS voices: {len(edge_voices)}")
    
    # List all voices with details
    print("\n📝 VOICE INVENTORY:")
    print("-" * 80)
    for voice in all_voices:
        provider_emoji = {
            'edge_tts': '🆓',
            'openai_tts': '💎',
            'elevenlabs': '👑',
            'google_tts': '🏭',
            'azure_tts': '☁️'
        }.get(voice.provider.value, '❓')
        
        quality_emoji = {
            'standard': '⭐',
            'premium': '⭐⭐',
            'ultra': '⭐⭐⭐'
        }.get(voice.quality, '❓')
        
        print(f"{provider_emoji} {voice.name:<25} {voice.language:<3} {quality_emoji} {voice.provider.value}")

def test_api_keys():
    """Test API key configuration"""
    print("🔑 TESTING API KEY CONFIGURATION")
    print("=" * 40)
    
    for provider, api_key in tts_manager.api_keys.items():
        status = "✅ Configured" if api_key else "❌ Missing"
        print(f"{provider.value:<15}: {status}")
        
        if not api_key and provider != TTSProvider.EDGE_TTS:
            print(f"   💡 Set environment variable for {provider.value}")

def main():
    """Main test function"""
    print("🚀 MULTI-AI TTS SYSTEM COMPREHENSIVE TEST")
    print("=" * 70)
    
    # Test 1: Voice listing
    test_voice_listing()
    print()
    
    # Test 2: API keys
    test_api_keys()
    print()
    
    # Test 3: Generate audio with all providers
    print("⚠️  Starting audio generation tests...")
    print("This will create test audio files for each provider.")
    
    proceed = input("Continue? (y/N): ").lower().strip()
    if proceed == 'y':
        asyncio.run(test_all_providers())
    else:
        print("Skipping audio generation tests.")
    
    print("\n🎯 TEST COMPLETED!")
    print("Check generated .wav files to test audio quality.")
    
    # Cleanup option
    cleanup = input("Delete test audio files? (y/N): ").lower().strip()
    if cleanup == 'y':
        test_files = [f for f in os.listdir('.') if f.startswith('test_') and f.endswith('.wav')]
        for file in test_files:
            os.remove(file)
            print(f"Deleted: {file}")

if __name__ == "__main__":
    main() 