#!/usr/bin/env python3
"""
Simple test script for SalaryHelper API
"""
import requests
import json
import time

API_BASE = "http://localhost:8000/api/v1"

def test_api():
    print("=== Testing SalaryHelper API ===")
    
    # Test health check
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{API_BASE}/health")
        print(f"✓ Health check: {response.json()}")
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return
    
    # Test send SMS
    print("\n2. Testing send SMS...")
    try:
        response = requests.post(f"{API_BASE}/auth/send-sms", json={"phone": "13800000000"})
        print(f"✓ Send SMS: {response.json()}")
    except Exception as e:
        print(f"✗ Send SMS failed: {e}")
        return
    
    # Test login
    print("\n3. Testing login...")
    try:
        response = requests.post(f"{API_BASE}/auth/login", json={"phone": "13800000000", "code": "123456"})
        login_data = response.json()
        print(f"✓ Login: {login_data}")
        
        if login_data.get('code') == 0:
            token = login_data['data']['token']
            user_id = login_data['data']['user']['id']
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test create conversation
            print("\n4. Testing create conversation...")
            conv_response = requests.post(f"{API_BASE}/conversations", 
                                        json={"title": "测试会话"}, 
                                        headers=headers)
            conv_data = conv_response.json()
            print(f"✓ Create conversation: {conv_data}")
            
            if conv_data.get('code') == 0:
                conv_id = conv_data['data']['id']
                
                # Test list conversations
                print("\n5. Testing list conversations...")
                list_response = requests.get(f"{API_BASE}/conversations", headers=headers)
                print(f"✓ List conversations: {list_response.json()}")
                
                # Test send message
                print("\n6. Testing send message...")
                msg_response = requests.post(f"{API_BASE}/conversations/{conv_id}/messages",
                                           json={"text": "Hello, this is a test message"},
                                           headers=headers)
                print(f"✓ Send message: {msg_response.json()}")
                
                # Test get conversation
                print("\n7. Testing get conversation...")
                get_response = requests.get(f"{API_BASE}/conversations/{conv_id}", headers=headers)
                print(f"✓ Get conversation: {get_response.json()}")
                
            # Test get current user
            print("\n8. Testing get current user...")
            user_response = requests.get(f"{API_BASE}/auth/me", headers=headers)
            print(f"✓ Get current user: {user_response.json()}")
            
    except Exception as e:
        print(f"✗ Login or subsequent tests failed: {e}")
        return
    
    print("\n=== All tests completed! ===")

if __name__ == "__main__":
    test_api()