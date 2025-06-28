#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick API Test - Verify all endpoints working
"""
import requests
import time

BASE_URL = "http://localhost:5000"

def test_api_endpoints():
    """Test all API endpoints"""
    print("🧪 Testing AI Video Editor API...")
    
    tests = [
        ("GET", "/", "Main page"),
        ("GET", "/api/gpu_status", "GPU status"),
    ]
    
    for method, endpoint, description in tests:
        try:
            url = f"{BASE_URL}{endpoint}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ {description}: OK")
            else:
                print(f"❌ {description}: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {description}: Error - {e}")
    
    print("\n🎉 API Test Complete!")
    print(f"🌐 App running at: {BASE_URL}")
    print("💡 Try uploading a video now!")

if __name__ == "__main__":
    test_api_endpoints() 