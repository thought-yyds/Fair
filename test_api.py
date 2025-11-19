#!/usr/bin/env python3
import requests
import json

# 测试API
base_url = "http://localhost:8000"

def test_api():
    """测试API连接"""
    try:
        print("🔍 测试API连接...")
        
        # 测试根路径
        response = requests.get(f"{base_url}/")
        print(f"✅ 根路径测试: {response.status_code}")
        if response.status_code == 200:
            print(f"   响应: {response.json()}")
        
        # 测试文件列表
        response = requests.get(f"{base_url}/api/files/list")
        print(f"✅ 文件列表API测试: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   文件数量: {len(data.get('data', []))}")
        
        # 测试审查详情API
        print("\n🔍 测试审查详情API...")
        response = requests.get(f"{base_url}/api/reviews/detail/1")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if 'data' in data and 'document_content' in data['data']:
                content = data['data']['document_content']
                print(f"文档内容长度: {len(content)}")
                print(f"文档内容预览: {content[:200]}...")
            else:
                print("响应中没有document_content字段")
        else:
            print(f"错误响应: {response.text}")
            
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    test_api()
