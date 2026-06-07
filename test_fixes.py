import requests
import json

base_url = "http://localhost:8112"

print("=" * 60)
print("测试1: 创建订单 (验证500错误修复)")
print("=" * 60)

resp = requests.post(f"{base_url}/auth/login", 
    data={"username": "operator", "password": "operator123"})
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

order_data = {
    "customer_name": "张三",
    "customer_phone": "13800138000",
    "store_id": 1,
    "remark": "测试订单",
    "items": [
        {
            "service_item_id": 1,
            "service_name": "普通干洗",
            "quantity": 2,
            "unit_price": 35.0,
            "subtotal": 70.0,
            "remark": "西装两件"
        }
    ]
}
resp = requests.post(f"{base_url}/orders", json=order_data, headers=headers)
print(f"创建订单状态码: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"✅ 创建成功，订单号: {data['order_no']}")
    print(f"  状态: {data['status']}")
    print(f"  状态日志数: {len(data['status_logs'])}")
    if data['status_logs']:
        print(f"  第一条日志操作人: {data['status_logs'][0]['operator_name']}")
    order_id = data['id']
else:
    print(f"❌ 错误: {resp.text}")
    exit(1)

print("\n" + "=" * 60)
print("测试2: 操作员正常流转订单")
print("=" * 60)

resp = requests.post(f"{base_url}/orders/{order_id}/receive", 
    params={"remark": "确认收件"}, headers=headers)
print(f"确认收件: {resp.status_code}", end="")
if resp.status_code == 200:
    print(f" ✅ -> {resp.json()['status']}")
else:
    print(f" ❌ {resp.text}")

resp = requests.post(f"{base_url}/orders/{order_id}/process", 
    params={"remark": "开始清洗"}, headers=headers)
print(f"开始处理: {resp.status_code}", end="")
if resp.status_code == 200:
    print(f" ✅ -> {resp.json()['status']}")
else:
    print(f" ❌ {resp.text}")

resp = requests.post(f"{base_url}/orders/{order_id}/to-inspection", 
    params={"remark": "清洗完成待质检"}, headers=headers)
print(f"提交质检: {resp.status_code}", end="")
if resp.status_code == 200:
    print(f" ✅ -> {resp.json()['status']}")
else:
    print(f" ❌ {resp.text}")

print("\n" + "=" * 60)
print("测试3: 审核员质检退回 (验证质检退回功能)")
print("=" * 60)

resp = requests.post(f"{base_url}/auth/login", 
    data={"username": "inspector", "password": "inspector123"})
inspector_token = resp.json()["access_token"]
inspector_headers = {"Authorization": f"Bearer {inspector_token}"}

resp = requests.post(f"{base_url}/orders/{order_id}/inspect-reject", 
    params={"remark": "领口有污渍未洗净"}, headers=inspector_headers)
print(f"质检退回: {resp.status_code}", end="")
if resp.status_code == 200:
    data = resp.json()
    print(f" ✅ -> {data['status']}")
else:
    print(f" ❌ {resp.text}")

print("\n" + "=" * 60)
print("测试4: 操作员重新处理退回的订单 (验证退回后能回到处理中)")
print("=" * 60)

resp = requests.post(f"{base_url}/orders/{order_id}/reprocess", 
    params={"remark": "重新清洗领口污渍"}, headers=headers)
print(f"重新处理: {resp.status_code}", end="")
if resp.status_code == 200:
    data = resp.json()
    print(f" ✅ -> {data['status']}")
    print(f"  ✅ 质检退回后成功回到处理中状态！")
else:
    print(f" ❌ {resp.text}")

print("\n" + "=" * 60)
print("测试5: 审核员权限边界 - 尝试修改非质检阶段订单")
print("=" * 60)

resp = requests.post(f"{base_url}/orders/{order_id}/to-inspection", 
    params={"remark": "再次提交质检"}, headers=headers)
current_status = resp.json()['status']
print(f"先将订单提交质检: {current_status}")

# 创建一个新订单，处于待收件状态，让审核员尝试操作
order_data2 = {
    "customer_name": "李四",
    "customer_phone": "13900139000",
    "store_id": 1,
    "remark": "权限测试订单",
    "items": [
        {
            "service_item_id": 2,
            "service_name": "水洗",
            "quantity": 1,
            "unit_price": 20.0,
            "subtotal": 20.0,
            "remark": ""
        }
    ]
}
resp = requests.post(f"{base_url}/orders", json=order_data2, headers=headers)
test_order_id = resp.json()['id']
print(f"创建测试订单 (待收件状态), ID={test_order_id}")

# 审核员尝试确认收件（应该被拒绝）
resp = requests.post(f"{base_url}/orders/{test_order_id}/receive", 
    params={"remark": "审核员尝试收件"}, headers=inspector_headers)
print(f"审核员尝试确认收件: {resp.status_code}", end="")
if resp.status_code == 403:
    print(f" ✅ 正确拒绝！错误信息: {resp.json()['detail']}")
else:
    print(f" ❌ 应该被拒绝但没有！")

# 审核员尝试用通用/status接口修改非质检阶段状态
resp = requests.post(f"{base_url}/orders/{test_order_id}/status", 
    json={"target_status": "received"}, headers=inspector_headers)
print(f"审核员尝试用/status改状态: {resp.status_code}", end="")
if resp.status_code == 403:
    print(f" ✅ 正确拒绝！错误信息: {resp.json()['detail']}")
else:
    print(f" ❌ 应该被拒绝但没有！")

print("\n" + "=" * 60)
print("🎉 所有修复测试完成！")
print("=" * 60)
