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
            
            # Test list templates
            print("\n9. Testing list templates...")
            tpl_response = requests.get(f"{API_BASE}/templates", headers=headers)
            tpl_data = tpl_response.json()
            print(f"✓ List templates: Found {len(tpl_data.get('data', []))} templates")
            
            if tpl_data.get('code') == 0 and len(tpl_data['data']) > 0:
                template_id = tpl_data['data'][0]['id']
                
                # Test get template
                print("\n10. Testing get template...")
                get_tpl_response = requests.get(f"{API_BASE}/templates/{template_id}", headers=headers)
                print(f"✓ Get template: {get_tpl_response.json()['data']['name']}")
                
                # Test create document
                print("\n11. Testing create document...")
                doc_data = {
                    "template_id": template_id,
                    "title": "测试文书",
                    "data": {
                        "applicant_name": "张三",
                        "applicant_gender": "男",
                        "applicant_id": "110101199001011234",
                        "applicant_phone": "13800000000",
                        "applicant_address": "北京市朝阳区",
                        "respondent_name": "某某公司",
                        "respondent_legal_rep": "李四",
                        "respondent_address": "北京市海淀区",
                        "respondent_phone": "010-12345678",
                        "arbitration_requests": "1. 要求支付拖欠工资10000元\n2. 要求支付经济补偿金5000元",
                        "facts_and_reasons": "本人于2023年1月入职该公司，公司拖欠工资三个月未发。",
                        "evidence_list": "1. 劳动合同\n2. 工资银行流水\n3. 考勤记录",
                        "arbitration_committee": "北京市劳动人事争议仲裁委员会",
                        "application_date": "2024年11月2日"
                    }
                }
                doc_response = requests.post(f"{API_BASE}/documents", json=doc_data, headers=headers)
                doc_result = doc_response.json()
                print(f"✓ Create document: {doc_result['data']['id']}")
                
                if doc_result.get('code') == 0:
                    doc_id = doc_result['data']['id']
                    
                    # Test list documents
                    print("\n12. Testing list documents...")
                    list_doc_response = requests.get(f"{API_BASE}/documents", headers=headers)
                    print(f"✓ List documents: Found {len(list_doc_response.json()['data'])} documents")
            
            # Test create order
            print("\n13. Testing create order...")
            order_data = {
                "product_type": "consultation",
                "amount": 99.00,
                "payment_method": "wechat"
            }
            order_response = requests.post(f"{API_BASE}/orders/create", json=order_data, headers=headers)
            order_result = order_response.json()
            print(f"✓ Create order: {order_result['data']['order_id']}")
            
            if order_result.get('code') == 0:
                order_id = order_result['data']['order_id']
                
                # Test simulate payment
                print("\n14. Testing simulate payment...")
                pay_response = requests.post(f"{API_BASE}/orders/{order_id}/pay", headers=headers)
                print(f"✓ Simulate payment: {pay_response.json()['data']['status']}")
                
                # Test list orders
                print("\n15. Testing list orders...")
                list_order_response = requests.get(f"{API_BASE}/orders", headers=headers)
                print(f"✓ List orders: Found {len(list_order_response.json()['data'])} orders")
            
            # Test admin endpoints
            print("\n16. Testing admin stats...")
            stats_response = requests.get(f"{API_BASE}/admin/stats", headers=headers)
            stats_data = stats_response.json()
            print(f"✓ Admin stats: {stats_data['data']}")
            
            print("\n17. Testing admin users...")
            admin_users_response = requests.get(f"{API_BASE}/admin/users", headers=headers)
            print(f"✓ Admin users: Found {len(admin_users_response.json()['data'])} users")
            
    except Exception as e:
        print(f"✗ Login or subsequent tests failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n=== All tests completed successfully! ===")

if __name__ == "__main__":
    test_api()