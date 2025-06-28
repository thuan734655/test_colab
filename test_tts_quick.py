#!/usr/bin/env python3
"""
Quick Multi-AI TTS Test
Test if the new system is working
"""

import asyncio
import requests
import json

def test_api_endpoints():
    """Test new API endpoints"""
    print("🎤 TESTING MULTI-AI TTS SYSTEM")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # Test 1: Get providers
    print("1. Testing /api/providers")
    try:
        response = requests.get(f"{base_url}/api/providers")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data['total_providers']} providers")
            for provider in data['providers']:
                status_emoji = "✅" if provider['status'] == 'ready' else "⚠️"
                print(f"  {status_emoji} {provider['name']}: {provider['voice_count']} voices")
        else:
            print(f"❌ Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Connection error: {e}")
    
    print()
    
    # Test 2: Get voices
    print("2. Testing /api/voices")
    try:
        response = requests.get(f"{base_url}/api/voices")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data['total_voices']} total voices")
            
            for provider_key, provider_data in data['providers'].items():
                print(f"  📢 {provider_data['name']}: {len(provider_data['voices'])} voices")
                
                # Show first 2 voices of each provider
                for i, voice in enumerate(provider_data['voices'][:2]):
                    quality_emoji = "⭐" * (1 if voice['quality'] == 'standard' else 2 if voice['quality'] == 'premium' else 3)
                    print(f"    {quality_emoji} {voice['name']} ({voice['language']}, {voice['gender']})")
                    
                if len(provider_data['voices']) > 2:
                    print(f"    ... and {len(provider_data['voices']) - 2} more")
        else:
            print(f"❌ Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Connection error: {e}")
    
    print()
    
    # Test 3: Get Vietnamese voices specifically
    print("3. Testing Vietnamese voices")
    try:
        response = requests.get(f"{base_url}/api/voices?language=vi")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data['total_voices']} Vietnamese voices")
            
            for provider_key, provider_data in data['providers'].items():
                for voice in provider_data['voices']:
                    quality_stars = "⭐" * (1 if voice['quality'] == 'standard' else 2 if voice['quality'] == 'premium' else 3)
                    print(f"  🇻🇳 {voice['name']} ({voice['gender']}) {quality_stars}")
                    print(f"     ID: {voice['id']}")
                    print(f"     Provider: {voice['provider']}")
                    print(f"     Description: {voice['description']}")
                    print()
        else:
            print(f"❌ Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Connection error: {e}")

def test_voice_generation():
    """Test actual voice generation"""
    print("4. Testing voice generation")
    print("⚠️  This will require uploading a video and SRT file")
    print("🎯 You can test this through the web interface at http://localhost:5000")
    print()
    print("📝 Steps to test:")
    print("  1. Upload a video file")
    print("  2. Upload an SRT file")
    print("  3. Select different TTS providers/voices")
    print("  4. Generate voice with different settings")
    print("  5. Create final video")

def main():
    """Main test function"""
    print("🚀 MULTI-AI TTS QUICK TEST")
    print("=" * 60)
    print("💡 Make sure the server is running: python start.py")
    print()
    
    test_api_endpoints()
    test_voice_generation()
    
    print("🎯 TEST SUMMARY:")
    print("✅ If all endpoints returned data, the Multi-AI TTS system is working!")
    print("✅ You can now use multiple TTS providers through the web interface")
    print("✅ Try different voices and compare quality")
    print()
    print("🔧 Next steps:")
    print("  - Update frontend to use new voice selection")
    print("  - Add API keys for premium providers")
    print("  - Test voice quality with different providers")

if __name__ == "__main__":
    main() 