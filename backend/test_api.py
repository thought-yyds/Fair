#!/usr/bin/env python3
"""
简单的API测试脚本
"""
import requests
import json

def test_api():
    base_url = "http://localhost:8000"
    
    print("🔍 测试API连接...")
    
    # 测试根路径
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ 根路径测试: {response.status_code}")
        print(f"   响应: {response.json()}")
    except Exception as e:
        print(f"❌ 根路径测试失败: {e}")
        return
    
    # 测试文件列表API
    try:
        response = requests.get(f"{base_url}/api/files/list")
        print(f"✅ 文件列表API测试: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   文件数量: {len(data)}")
        else:
            print(f"   错误: {response.text}")
    except Exception as e:
        print(f"❌ 文件列表API测试失败: {e}")
    
    # 测试API文档
    try:
        response = requests.get(f"{base_url}/docs")
        print(f"✅ API文档测试: {response.status_code}")
    except Exception as e:
        print(f"❌ API文档测试失败: {e}")

if __name__ == "__main__":
    test_api()
