"""
Voice Announcement API Test Script
Tests the /kiosk/api/audio endpoint
"""

import requests
import json

# Base URL (change if running on different port)
BASE_URL = "http://127.0.0.1:5000"

def test_audio_api():
    """Test the audio announcement API endpoint"""
    
    print("=" * 60)
    print("🔊 VOICE ANNOUNCEMENT API TEST")
    print("=" * 60)
    print()
    
    test_cases = [
        {"name": "Rahul", "status": "check-in", "expected": "Welcome Rahul"},
        {"name": "Priya", "status": "check-out", "expected": "Goodbye Priya"},
        {"name": "Amit", "status": "already", "expected": "Amit, already marked"},
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['status']} for {test['name']}")
        print("-" * 60)
        
        try:
            # Make API request
            response = requests.post(
                f"{BASE_URL}/kiosk/api/audio",
                json={
                    "name": test["name"],
                    "status": test["status"]
                },
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            # Check response
            if response.status_code == 200:
                data = response.json()
                
                print(f"✅ Status: {response.status_code}")
                print(f"📦 Response: {json.dumps(data, indent=2)}")
                
                # Validate response structure
                if data.get("success"):
                    print(f"✅ Success: True")
                else:
                    print(f"❌ Success: False")
                
                if data.get("mode") == "tts":
                    print(f"✅ Mode: {data['mode']}")
                else:
                    print(f"❌ Mode: {data.get('mode', 'N/A')}")
                
                if "config" in data:
                    config = data["config"]
                    print(f"✅ Config:")
                    print(f"   - Text: {config.get('text')}")
                    print(f"   - Language: {config.get('lang')}")
                    print(f"   - Rate: {config.get('rate')}")
                    print(f"   - Pitch: {config.get('pitch')}")
                    print(f"   - Volume: {config.get('volume')}")
                    print(f"   - Preferred Voices: {len(config.get('preferredVoices', []))} voices")
                    
                    # Validate expected text
                    if config.get('text') == test['expected']:
                        print(f"✅ Text matches expected: '{test['expected']}'")
                    else:
                        print(f"❌ Text mismatch!")
                        print(f"   Expected: '{test['expected']}'")
                        print(f"   Got: '{config.get('text')}'")
                else:
                    print(f"❌ Config missing in response")
                
            else:
                print(f"❌ Status: {response.status_code}")
                print(f"📦 Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection Error: Cannot connect to {BASE_URL}")
            print(f"   Make sure Flask app is running: python app.py")
            break
        except requests.exceptions.Timeout:
            print(f"❌ Timeout: Request took too long")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
    
    print("=" * 60)
    print("✅ TEST COMPLETE")
    print("=" * 60)


def check_flask_running():
    """Check if Flask app is running"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=2)
        return True
    except:
        return False


if __name__ == "__main__":
    print()
    
    # Check if Flask is running
    if not check_flask_running():
        print("⚠️  WARNING: Flask app doesn't seem to be running!")
        print(f"   Start it with: python app.py")
        print(f"   Expected URL: {BASE_URL}")
        print()
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Test cancelled.")
            exit(0)
        print()
    
    test_audio_api()
