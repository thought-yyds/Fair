import requests
import json

# 测试审查详情API
url = "http://localhost:8000/api/reviews/detail/4"
response = requests.get(url)

print(f"状态码: {response.status_code}")
print(f"响应头: {response.headers}")
print(f"响应内容: {response.text}")

if response.status_code == 200:
    data = response.json()
    print(f"\n解析后的JSON:")
    print(f"success: {data.get('success')}")
    if 'data' in data:
        data_content = data['data']
        print(f"data字段的键: {list(data_content.keys())}")
        print(f"article_name: {data_content.get('article_name')}")
        print(f"document_content存在: {'document_content' in data_content}")
        if 'document_content' in data_content:
            doc_content = data_content['document_content']
            print(f"document_content长度: {len(doc_content)}")
            print(f"document_content预览: {doc_content[:200]}...")
        else:
            print("document_content字段不存在！")
