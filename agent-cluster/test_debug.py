import requests
url = "http://127.0.0.1:8890/api/dingtalk/callback"
data = {"text": {"content": "确认部署 wf-20260315-185705-webhook-test"}, "conversation_id": "test123", "sender_id": "user123"}
response = requests.post(url, json=data, timeout=10)
print(f"状态码：{response.status_code}")
print(f"响应：{response.text}")
