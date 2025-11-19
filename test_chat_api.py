#!/usr/bin/env python3
"""
测试聊天API功能
"""
import requests
import json

# API基础URL
BASE_URL = "http://localhost:8000/api/chat"

def test_chat_api():
    """测试聊天API"""
    print("🚀 开始测试聊天API...")
    
    # 1. 测试创建对话
    print("\n1. 测试创建对话...")
    response = requests.post(f"{BASE_URL}/conversations")
    if response.status_code == 200:
        conversation = response.json()
        conversation_id = conversation["id"]
        print(f"✅ 对话创建成功: {conversation_id}")
    else:
        print(f"❌ 创建对话失败: {response.status_code}")
        return
    
    # 2. 测试发送消息
    print("\n2. 测试发送消息...")
    message_data = {
        "message": "你好，请介绍一下你的功能",
        "conversation_id": conversation_id
    }
    response = requests.post(f"{BASE_URL}/message", json=message_data)
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 消息发送成功")
        print(f"AI回复: {result['message']['content'][:100]}...")
    else:
        print(f"❌ 发送消息失败: {response.status_code}")
    
    # 3. 测试获取对话列表
    print("\n3. 测试获取对话列表...")
    response = requests.get(f"{BASE_URL}/conversations")
    if response.status_code == 200:
        conversations = response.json()
        print(f"✅ 获取对话列表成功，共 {len(conversations)} 个对话")
    else:
        print(f"❌ 获取对话列表失败: {response.status_code}")
    
    # 4. 测试文件上传
    print("\n4. 测试文件上传...")
    # 创建一个测试文件
    test_content = "这是一个测试文档\n包含一些示例内容\n用于测试文件上传功能"
    files = {"file": ("test.txt", test_content, "text/plain")}
    response = requests.post(f"{BASE_URL}/upload", files=files)
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            print(f"✅ 文件上传成功: {result['attachment']['name']}")
        else:
            print(f"❌ 文件上传失败: {result['error']}")
    else:
        print(f"❌ 文件上传失败: {response.status_code}")
    
    # 5. 测试获取聊天设置
    print("\n5. 测试获取聊天设置...")
    response = requests.get(f"{BASE_URL}/settings")
    if response.status_code == 200:
        settings = response.json()
        print(f"✅ 获取设置成功: 模型={settings['model']}")
    else:
        print(f"❌ 获取设置失败: {response.status_code}")
    
    print("\n🎉 聊天API测试完成！")

if __name__ == "__main__":
    test_chat_api()
