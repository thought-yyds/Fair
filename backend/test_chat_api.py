"""
聊天API测试脚本
"""
import requests
import json

# 测试配置
BASE_URL = "http://localhost:8000"
CHAT_API_BASE = f"{BASE_URL}/api/chat"

def test_chat_api():
    """测试聊天API功能"""
    print("开始测试聊天API...")
    
    # 1. 测试创建会话
    print("\n1. 测试创建会话...")
    create_session_data = {
        "title": "测试会话",
        "user_id": "test_user_001"
    }
    
    try:
        response = requests.post(f"{CHAT_API_BASE}/conversations", json=create_session_data)
        if response.status_code == 200:
            session = response.json()
            session_id = session["session_id"]
            print(f"✅ 会话创建成功: {session_id}")
        else:
            print(f"❌ 会话创建失败: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ 会话创建异常: {e}")
        return
    
    # 2. 测试发送消息
    print("\n2. 测试发送消息...")
    message_data = {
        "message": "你好，请介绍一下你自己",
        "session_id": session_id,
        "user_id": "test_user_001"
    }
    
    try:
        response = requests.post(f"{CHAT_API_BASE}/message", json=message_data)
        if response.status_code == 200:
            chat_response = response.json()
            print(f"✅ 消息发送成功: {chat_response['message']}")
        else:
            print(f"❌ 消息发送失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 消息发送异常: {e}")
    
    # 3. 测试获取会话列表
    print("\n3. 测试获取会话列表...")
    try:
        response = requests.get(f"{CHAT_API_BASE}/conversations?user_id=test_user_001")
        if response.status_code == 200:
            sessions = response.json()
            print(f"✅ 获取会话列表成功，共 {len(sessions)} 个会话")
            for session in sessions:
                print(f"   - {session['title']} ({session['session_id'][:8]}...)")
        else:
            print(f"❌ 获取会话列表失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 获取会话列表异常: {e}")
    
    # 4. 测试获取会话消息
    print("\n4. 测试获取会话消息...")
    try:
        response = requests.get(f"{CHAT_API_BASE}/conversations/{session_id}/messages")
        if response.status_code == 200:
            messages = response.json()
            print(f"✅ 获取消息列表成功，共 {len(messages)} 条消息")
            for msg in messages:
                role_name = "用户" if msg["role"] == "user" else "AI助手"
                print(f"   - [{role_name}] {msg['content'][:50]}...")
        else:
            print(f"❌ 获取消息列表失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 获取消息列表异常: {e}")
    
    # 5. 测试流式响应
    print("\n5. 测试流式响应...")
    stream_data = {
        "message": "请详细介绍一下你的功能",
        "session_id": session_id,
        "user_id": "test_user_001"
    }
    
    try:
        response = requests.post(f"{CHAT_API_BASE}/stream", json=stream_data, stream=True)
        if response.status_code == 200:
            print("✅ 流式响应开始:")
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        if data_str == '[DONE]':
                            print("\n✅ 流式响应结束")
                            break
                        try:
                            data = json.loads(data_str)
                            print(data.get('content', ''), end='', flush=True)
                        except:
                            pass
        else:
            print(f"❌ 流式响应失败: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 流式响应异常: {e}")
    
    print("\n聊天API测试完成！")

if __name__ == "__main__":
    test_chat_api()
