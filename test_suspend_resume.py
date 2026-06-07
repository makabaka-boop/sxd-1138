import requests
import json

base_url = "http://localhost:8112"

print("=" * 70)
print("测试: 订单异常挂起与恢复功能")
print("=" * 70)

# 登录操作员
resp = requests.post(f"{base_url}/auth/login", 
    data={"username": "operator", "password": "operator123"})
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✅ 操作员登录成功")

# 创建订单
order_data = {
    "customer_name": "测试客户",
    "customer_phone": "13800138000",
    "store_id": 1,
    "remark": "挂起测试订单",
    "items": [
        {
            "service_item_id": 1,
            "service_name": "普通干洗",
            "quantity": 1,
            "unit_price": 35.0,
            "subtotal": 35.0,
            "remark": "西装一件"
        }
    ]
}
resp = requests.post(f"{base_url}/orders", json=order_data, headers=headers)
print(f"\n1. 创建订单: {resp.status_code}")
if resp.status_code == 200:
    order = resp.json()
    order_id = order["id"]
    print(f"   ✅ 订单号: {order['order_no']}, 状态: {order['status']}")
    print(f"   ✅ is_suspended: {order['is_suspended']}")
else:
    print(f"   ❌ 错误: {resp.text}")
    exit(1)

# 测试1: 挂起订单 - 客户补充说明
print("\n" + "=" * 70)
print("测试1: 挂起订单（原因：客户补充说明）")
print("=" * 70)
suspend_data = {
    "reason": "customer_supplement",
    "remark": "客户需要补充衣物清洗说明"
}
resp = requests.post(f"{base_url}/orders/{order_id}/suspend", json=suspend_data, headers=headers)
print(f"挂起请求状态码: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"✅ 挂起成功！")
    print(f"   状态: {data['status']}")
    print(f"   is_suspended: {data['is_suspended']}")
    print(f"   挂起原因: {data['suspend_reason']}")
    print(f"   挂起备注: {data['suspend_remark']}")
    print(f"   挂起人ID: {data['suspended_by']}")
    print(f"   挂起时间: {data['suspended_at']}")
    print(f"   挂起前状态: {data['previous_status']}")
    
    # 检查状态日志
    last_log = data["status_logs"][-1]
    print(f"   最后一条日志类型: {last_log['log_type']}")
    print(f"   日志挂起原因: {last_log['suspend_reason']}")
else:
    print(f"❌ 错误: {resp.text}")

# 测试2: 挂起状态下尝试流转订单（应该失败）
print("\n" + "=" * 70)
print("测试2: 挂起状态下尝试流转订单（应失败）")
print("=" * 70)
resp = requests.post(f"{base_url}/orders/{order_id}/receive", headers=headers)
print(f"尝试确认收件: {resp.status_code}")
if resp.status_code == 400:
    print(f"✅ 正确拒绝！错误信息: {resp.json()['detail']}")
else:
    print(f"❌ 应该被拒绝但没有！状态码: {resp.status_code}, 响应: {resp.text}")

# 测试3: 查看可流转状态（挂起时应该为空）
print("\n" + "=" * 70)
print("测试3: 挂起状态下查看可流转状态")
print("=" * 70)
resp = requests.get(f"{base_url}/orders/{order_id}/transitions", headers=headers)
if resp.status_code == 200:
    data = resp.json()
    print(f"当前状态: {data['current_status']}")
    print(f"可前进状态: {data['forward']}")
    print(f"可回退状态: {data['rollback']}")
    if len(data["forward"]) == 0 and len(data["rollback"]) == 0:
        print("✅ 挂起状态下无可流转状态，正确！")
    else:
        print("❌ 挂起状态下不应该有可流转状态！")

# 测试4: 非原挂起人尝试恢复（普通操作员尝试恢复自己挂起的应该可以）
print("\n" + "=" * 70)
print("测试4: 恢复订单（原挂起操作员）")
print("=" * 70)

# 先登录另一个操作员测试权限？不，先让当前操作员恢复自己挂起的
resume_data = {
    "result": "客户已补充说明，可继续处理",
    "remark": "已收到客户补充的清洗要求"
}
resp = requests.post(f"{base_url}/orders/{order_id}/resume", json=resume_data, headers=headers)
print(f"恢复请求状态码: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"✅ 恢复成功！")
    print(f"   状态: {data['status']}")
    print(f"   is_suspended: {data['is_suspended']}")
    print(f"   previous_status (应为空): {data['previous_status']}")
    print(f"   suspend_reason (应为空): {data['suspend_reason']}")
    
    # 检查状态日志
    last_log = data["status_logs"][-1]
    print(f"   最后一条日志类型: {last_log['log_type']}")
    print(f"   日志恢复结果: {last_log['resume_result']}")
else:
    print(f"❌ 错误: {resp.text}")

# 测试5: 恢复后可以正常流转
print("\n" + "=" * 70)
print("测试5: 恢复后正常流转订单")
print("=" * 70)
resp = requests.post(f"{base_url}/orders/{order_id}/receive", headers=headers)
print(f"确认收件: {resp.status_code}", end="")
if resp.status_code == 200:
    print(f" ✅ -> {resp.json()['status']}")
else:
    print(f" ❌ {resp.text}")

# 测试6: 已收件状态挂起
print("\n" + "=" * 70)
print("测试6: 已收件状态挂起（原因：衣物破损）")
print("=" * 70)
suspend_data = {
    "reason": "clothes_damage",
    "remark": "收件时发现衣物有破损，需要客户确认"
}
resp = requests.post(f"{base_url}/orders/{order_id}/suspend", json=suspend_data, headers=headers)
print(f"挂起请求: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"✅ 挂起成功！状态: {data['status']}, 原因: {data['suspend_reason']}")
else:
    print(f"❌ 错误: {resp.text}")

# 测试7: 管理员恢复订单
print("\n" + "=" * 70)
print("测试7: 管理员恢复订单")
print("=" * 70)
resp = requests.post(f"{base_url}/auth/login", 
    data={"username": "admin", "password": "admin123"})
admin_token = resp.json()["access_token"]
admin_headers = {"Authorization": f"Bearer {admin_token}"}
print("✅ 管理员登录成功")

resume_data = {
    "result": "客户已确认破损，照常清洗",
    "remark": "客户已知情并同意继续处理"
}
resp = requests.post(f"{base_url}/orders/{order_id}/resume", json=resume_data, headers=admin_headers)
print(f"管理员恢复: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"✅ 管理员恢复成功！状态: {data['status']}")
else:
    print(f"❌ 错误: {resp.text}")

# 测试8: 管理员筛选异常订单
print("\n" + "=" * 70)
print("测试8: 管理员筛选异常订单")
print("=" * 70)

# 先创建一个新订单并挂起，用于测试筛选
order_data2 = {
    "customer_name": "异常测试客户",
    "customer_phone": "13900139000",
    "store_id": 1,
    "remark": "",
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
resp = requests.post(f"{base_url}/orders", json=order_data2, headers=admin_headers)
order2_id = resp.json()["id"]
print(f"创建测试订单2: ID={order2_id}")

suspend_data2 = {
    "reason": "price_dispute",
    "remark": "客户对价格有异议"
}
resp = requests.post(f"{base_url}/orders/{order2_id}/suspend", json=suspend_data2, headers=admin_headers)
print(f"挂起订单2: {resp.status_code}")

# 测试管理员获取所有挂起订单
resp = requests.get(f"{base_url}/admin/orders/suspended", headers=admin_headers)
print(f"\n管理员获取挂起订单: {resp.status_code}")
if resp.status_code == 200:
    suspended_orders = resp.json()
    print(f"✅ 找到 {len(suspended_orders)} 个挂起订单")
    for o in suspended_orders:
        print(f"   - 订单 {o['order_no']}: 原因={o['suspend_reason']}, 挂起人={o['suspended_by_name']}")
else:
    print(f"❌ 错误: {resp.text}")

# 测试 is_suspended 筛选
resp = requests.get(f"{base_url}/admin/orders", params={"is_suspended": "true"}, headers=admin_headers)
print(f"\n管理员筛选 is_suspended=true: {resp.status_code}")
if resp.status_code == 200:
    filtered = resp.json()
    print(f"✅ 筛选结果: {len(filtered)} 个订单")
    all_suspended = all(o["is_suspended"] for o in filtered)
    if all_suspended:
        print(f"✅ 所有筛选结果都是挂起状态")
    else:
        print(f"❌ 筛选结果包含非挂起订单")

# 测试订单列表的 is_suspended 筛选
print("\n" + "=" * 70)
print("测试9: 订单列表支持 is_suspended 筛选")
print("=" * 70)
resp = requests.get(f"{base_url}/orders", params={"is_suspended": "false"}, headers=headers)
print(f"筛选 is_suspended=false: {resp.status_code}", end="")
if resp.status_code == 200:
    data = resp.json()
    print(f" ✅ 共 {len(data)} 个非挂起订单")
else:
    print(f" ❌ {resp.text}")

# 测试10: 不允许挂起的状态尝试挂起
print("\n" + "=" * 70)
print("测试10: 不允许挂起的状态尝试挂起（应失败）")
print("=" * 70)

# 先将订单流转到待取件（不在可挂起状态列表中）
# 先把 order_id 流转到待取件
resp = requests.post(f"{base_url}/orders/{order_id}/process", headers=headers)
print(f"开始处理: {resp.status_code}")
resp = requests.post(f"{base_url}/orders/{order_id}/to-inspection", headers=headers)
print(f"提交质检: {resp.status_code}")

# 登录审核员
resp = requests.post(f"{base_url}/auth/login", 
    data={"username": "inspector", "password": "inspector123"})
inspector_token = resp.json()["access_token"]
inspector_headers = {"Authorization": f"Bearer {inspector_token}"}

resp = requests.post(f"{base_url}/orders/{order_id}/inspect-pass", headers=inspector_headers)
print(f"质检通过: {resp.status_code} -> {resp.json()['status']}")

# 尝试在待取件状态挂起
suspend_data = {"reason": "other", "remark": "测试"}
resp = requests.post(f"{base_url}/orders/{order_id}/suspend", json=suspend_data, headers=inspector_headers)
print(f"待取件状态尝试挂起: {resp.status_code}")
if resp.status_code == 400:
    print(f"✅ 正确拒绝！错误信息: {resp.json()['detail']}")
else:
    print(f"❌ 应该被拒绝但没有！")

print("\n" + "=" * 70)
print("🎉 所有挂起与恢复功能测试完成！")
print("=" * 70)
