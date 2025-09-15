#!/usr/bin/env python3
"""
Simple verification script to confirm everything is working
"""
import requests
import json

def main():
    print("🔍 Verifying Fake Job Guru Setup...")
    print("=" * 50)
    
    # Test 1: Check if server is running
    try:
        health_response = requests.get('http://127.0.0.1:8000/health', timeout=5)
        if health_response.status_code == 200:
            print("✅ Server is running and healthy")
        else:
            print("❌ Server health check failed")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    # Test 2: Check UI endpoint
    try:
        ui_response = requests.get('http://127.0.0.1:8000/', timeout=5)
        if ui_response.status_code == 200 and 'Fake Job Guru' in ui_response.text:
            print("✅ Web UI is accessible")
        else:
            print("❌ Web UI not working properly")
            return
    except Exception as e:
        print(f"❌ UI endpoint error: {e}")
        return
    
    # Test 3: Test analysis with sample data
    sample_data = {
        "title": "Data Entry Clerk",
        "description": "Earn $500/day working from home. No experience required. Apply via Gmail.",
        "requirements": "Basic typing skills",
        "company_profile": "Small startup",
        "followers": 120,
        "employees": 3,
        "engagement": 1
    }
    
    try:
        analysis_response = requests.post(
            'http://127.0.0.1:8000/analyze_job',
            json=sample_data,
            timeout=10
        )
        
        if analysis_response.status_code == 200:
            result = analysis_response.json()
            print("✅ Analysis endpoint working")
            print(f"   Prediction: {result['prediction']}")
            print(f"   Risk Score: {result['risk_score']}")
            print(f"   Keywords Found: {result['signals']['keywords_triggered']}")
        else:
            print(f"❌ Analysis failed: {analysis_response.status_code}")
            return
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        return
    
    print("\n" + "=" * 50)
    print("🎉 ALL TESTS PASSED!")
    print("🌐 Your web UI is ready at: http://127.0.0.1:8000")
    print("📝 You can now analyze job postings through the web interface!")
    print("=" * 50)

if __name__ == "__main__":
    main()
