#!/usr/bin/env python3
"""
Test script for streaming code execution
Tests the /run_code_streaming endpoint directly
"""

import requests
import json
import time

def test_code_manager_streaming():
    """Test CodeManager streaming endpoint directly"""
    
    url = "http://localhost:5001/run_code_streaming"
    
    # Test code with streaming output
    test_code = '''
import time
print("Starting streaming test...")
for i in range(5):
    print(f"Count: {i}")
    time.sleep(3)
print("Test completed!")
'''
    
    payload = {
        "user_id": "test_user_123",
        "code": test_code.strip()
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print("🚀 Testing CodeManager streaming endpoint...")
    print(f"URL: {url}")
    print(f"Code: {test_code.strip()}")
    print("-" * 50)
    
    try:
        response = requests.post(url, json=payload, headers=headers, stream=True, timeout=30)
        
        if response.status_code == 200:
            print("✅ Connection successful! Starting stream...")
            print("-" * 50)
            
            # Read stream line by line
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    print(f"📦 Raw line: {decoded_line}")
                    
                    if decoded_line.startswith('data: '):
                        try:
                            # Parse JSON data
                            json_data = decoded_line[6:]  # Remove 'data: ' prefix
                            data = json.loads(json_data)
                            
                            # Print formatted output
                            output_type = data.get('type', 'unknown')
                            output_line = data.get('line', '')
                            
                            if output_type == 'stdout':
                                print(f"📤 STDOUT: {output_line}")
                            elif output_type == 'stderr':
                                print(f"❌ STDERR: {output_line}")
                            elif output_type == 'error':
                                print(f"💥 ERROR: {output_line}")
                            else:
                                print(f"❓ UNKNOWN: {data}")
                                
                        except json.JSONDecodeError as e:
                            print(f"⚠️  JSON Parse Error: {e}")
                            print(f"Raw data: {decoded_line}")
                    else:
                        print(f"📄 Non-data line: {decoded_line}")
                        
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

def test_backend_streaming():
    """Test Backend API streaming endpoint with redirect approach"""
    
    # First get authentication token
    login_url = "http://localhost:6600/api/auth/login"
    login_payload = {
        "username": "testuser",
        "password": "testpass"
    }
    
    print("🔐 Getting authentication token...")
    
    try:
        login_response = requests.post(login_url, json=login_payload)
        if login_response.status_code == 200:
            token_data = login_response.json()
            token = token_data.get('token')
            print(f"✅ Token obtained: {token[:20]}...")
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            return
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    # Test redirect endpoint
    url = "http://localhost:6600/api/code/execute_streaming"
    
    test_code = '''
import time
print("Backend redirect test...")
for i in range(3):
    print(f"Backend Count: {i}")
    time.sleep(3)
print("Backend test done!")
'''
    
    payload = {
        "code": test_code.strip()
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    print("\n🚀 Testing Backend redirect endpoint...")
    print(f"URL: {url}")
    print(f"Code: {test_code.strip()}")
    print("-" * 50)
    
    try:
        # First call to get redirect info
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            redirect_info = response.json()
            print("✅ Backend redirect info received!")
            print(f"📋 Redirect URL: {redirect_info['redirect_url']}")
            print(f"📋 Method: {redirect_info['method']}")
            print(f"📋 Payload: {redirect_info['payload']}")
            print("-" * 50)
            
            # Now make direct call to CodeManager
            print("🔄 Making direct call to CodeManager...")
            direct_response = requests.post(
                redirect_info['redirect_url'],
                json=redirect_info['payload'],
                headers=redirect_info['headers'],
                stream=True,
                timeout=30
            )
            
            if direct_response.status_code == 200:
                print("✅ Direct CodeManager connection successful! Starting stream...")
                print("-" * 50)
                
                # Read stream line by line
                for line in direct_response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        print(f"📦 Direct Raw: {decoded_line}")
                        
                        if decoded_line.startswith('data: '):
                            try:
                                json_data = decoded_line[6:]
                                data = json.loads(json_data)
                                
                                output_type = data.get('type', 'unknown')
                                output_line = data.get('line', '')
                                
                                if output_type == 'stdout':
                                    print(f"📤 DIRECT STDOUT: {output_line}")
                                elif output_type == 'stderr':
                                    print(f"❌ DIRECT STDERR: {output_line}")
                                elif output_type == 'error':
                                    print(f"💥 DIRECT ERROR: {output_line}")
                                else:
                                    print(f"❓ DIRECT UNKNOWN: {data}")
                                    
                            except json.JSONDecodeError as e:
                                print(f"⚠️  Direct JSON Parse Error: {e}")
                                print(f"Raw data: {decoded_line}")
                        else:
                            print(f"📄 Direct Non-data line: {decoded_line}")
            else:
                print(f"❌ Direct CodeManager HTTP Error: {direct_response.status_code}")
                print(f"Response: {direct_response.text}")
                        
        else:
            print(f"❌ Backend HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend Request Error: {e}")
    except Exception as e:
        print(f"❌ Backend Unexpected Error: {e}")

if __name__ == "__main__":
    print("🧪 Streaming Test Suite")
    print("=" * 60)
    
    # Test CodeManager directly
    test_code_manager_streaming()
    
    print("\n" + "=" * 60)
    
    # Test Backend API
    test_backend_streaming()
    
    print("\n🏁 Test completed!")
