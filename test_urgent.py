import requests
import json

base_url = "http://localhost:8112"

print("=" * 70)
print("测试: 订单加急处理功能")
print("=" * 70)

resp = requests.post(f"{base_url}/auth/login", 
    data={"username": "operator", "password": "operator123"})
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✅ 操作员登录成功")

resp = requests.post(f"{base_url}/auth/login", 
    data={"username": "admin", "password": "admin123"})
admin_token = resp.json()["access_token"]
admin_headers = {"Authorization": f"Bearer {admin_token}"}
print("✅ 管理员登录成功")

print("\n" + "=" * 70)
print("测试1: 查看服务项目的加急配置")
print("=" * 70)
resp = requests.get(f"{base_url}/admin/services", headers=admin_headers)
if resp.status_code == 200:
    services = resp.json()
    print(f"✅ 找到 {len(services)} 个服务项目")
    for s in services:
        print(f"   - {s['name']}: 价格={s['price']}, 加急费={s['urgent_fee']}, 加急说明={s['urgent_description']}")
else:
    print(f"❌ 错误: {resp.text}")

print("\n" + "=" * 70)
print("测试2: 创建加急订单")
print("=" * 70)
order_data = {
    "customer_name": "加急测试客户",
    "customer_phone": "13800138888",
    "store_id": 1,
    "remark": "普通备注",
    "is_urgent": True,
    "urgent_remark": "客户要求明天上午取件",
    "items": [
        {
            "service_item_id": 1,
            "service_name": "普通干洗",
            "quantity": 1,
            "unit_price": 35.0,
            "subtotal": 35.0,
            "remark": "西装一件"
        },
        {
            "service_item_id": 3,
            "service_name": "水洗",
            "quantity": 2,
            "unit_price": 20.0,
            "subtotal": 40.0,
            "remark": ""
        }
    ]
}
resp = requests.post(f"{base_url}/orders", json=order_data, headers=headers)
print(f"创建订单状态码: {resp.status_code}")
if resp.status_code == 200:
    order = resp.json()
    order_id = order["id"]
    print(f"✅ 订单号: {order['order_no']}")
    print(f"✅ 状态: {order['status']}")
    print(f"✅ is_urgent: {order['is_urgent']}")
    print(f"✅ urgent_remark: {order['urgent_remark']}")
    print(f"✅ urgent_fee: {order['urgent_fee']}")
    print(f"✅ total_amount: {order['total_amount']}")
    print(f"✅ 计算: 商品小计 35+40=75, 加急费 15+10*2=35, 总计 75+35=110")
    expected_total = 75 + 35
    if abs(order['total_amount'] - expected_total) < 0.01:
        print(f"✅ 总价计算正确！")
    else:
        print(f"❌ 总价计算错误，预期 {expected_total}，实际 {order['total_amount']}")
else:
    print(f"❌ 错误: {resp.text}")
    exit(1)

print("\n" + "=" * 70)
print("测试3: 查看加急订单的状态日志")
print("=" * 70)
last_log = order["status_logs"][-1]
print(f"最后一条日志:")
print(f"   log_type: {last_log['log_type']}")
print(f"   urgent_changed: {last_log['urgent_changed']}")
print(f"   from_urgent: {last_log['from_urgent']}")
print(f"   to_urgent: {last_log['to_urgent']}")
print(f"   urgent_remark_changed: {last_log['urgent_remark_changed']}")
print(f"   to_urgent_remark: {last_log['to_urgent_remark']}")
if last_log['urgent_changed'] and last_log['to_urgent']:
    print(f"✅ 加急标记变更已记录")
else:
    print(f"❌ 加急标记变更未正确记录")

print("\n" + "=" * 70)
print("测试4: 订单列表加急筛选")
print("=" * 70)
resp = requests.get(f"{base_url}/orders", params={"is_urgent": "true"}, headers=headers)
if resp.status_code == 200:
    urgent_orders = resp.json()
    print(f"✅ 筛选加急订单: 找到 {len(urgent_orders)} 个")
    all_urgent = all(o["is_urgent"] for o in urgent_orders)
    if all_urgent:
        print(f"✅ 所有筛选结果都是加急订单")
    else:
        print(f"❌ 筛选结果包含非加急订单")
else:
    print(f"❌ 错误: {resp.text}")

resp = requests.get(f"{base_url}/orders", params={"is_urgent": "false"}, headers=headers)
if resp.status_code == 200:
    normal_orders = resp.json()
    print(f"✅ 筛选非加急订单: 找到 {len(normal_orders)} 个")
    all_normal = all(not o["is_urgent"] for o in normal_orders)
    if all_normal:
        print(f"✅ 所有筛选结果都是非加急订单")
    else:
        print(f"❌ 筛选结果包含加急订单")
else:
    print(f"❌ 错误: {resp.text}")

print("\n" + "=" * 70)
print("测试5: 管理员接口加急筛选")
print("=" * 70)
resp = requests.get(f"{base_url}/admin/orders", params={"is_urgent": "true"}, headers=admin_headers)
if resp.status_code == 200:
    admin_urgent = resp.json()
    print(f"✅ 管理员筛选加急订单: 找到 {len(admin_urgent)} 个")
    all_urgent = all(o["is_urgent"] for o in admin_urgent)
    if all_urgent:
        print(f"✅ 所有筛选结果都是加急订单")
    else:
        print(f"❌ 筛选结果包含非加急订单")
else:
    print(f"❌ 错误: {resp.text}")

print("\n" + "=" * 70)
print("测试6: 更新订单 - 取消加急")
print("=" * 70)
update_data = {
    "is_urgent": False,
    "urgent_remark": ""
}
resp = requests.put(f"{base_url}/orders/{order_id}", json=update_data, headers=headers)
if resp.status_code == 200:
    updated = resp.json()
    print(f"✅ 更新成功")
    print(f"   is_urgent: {updated['is_urgent']}")
    print(f"   urgent_fee: {updated['urgent_fee']}")
    print(f"   total_amount: {updated['total_amount']}")
    expected_total = 75
    if abs(updated['total_amount'] - expected_total) < 0.01:
        print(f"✅ 取消加急后总价正确（已扣除加急费）")
    else:
        print(f"❌ 总价计算错误，预期 {expected_total}，实际 {updated['total_amount']}")
    
    last_log = updated["status_logs"][-1]
    print(f"   最后一条日志类型: {last_log['log_type']}")
    print(f"   urgent_changed: {last_log['urgent_changed']}")
    print(f"   from_urgent: {last_log['from_urgent']}")
    print(f"   to_urgent: {last_log['to_urgent']}")
    if last_log['log_type'] == 'urgent_change' and last_log['urgent_changed'] and not last_log['to_urgent']:
        print(f"✅ 取消加急的变更已正确记录到日志")
    else:
        print(f"❌ 取消加急的变更未正确记录")
else:
    print(f"❌ 错误: {resp.text}")

print("\n" + "=" * 70)
print("测试7: 更新订单 - 重新标记加急")
print("=" * 70)
update_data2 = {
    "is_urgent": True,
    "urgent_remark": "客户又要求加急了，今天下午取"
}
resp = requests.put(f"{base_url}/orders/{order_id}", json=update_data2, headers=headers)
if resp.status_code == 200:
    updated2 = resp.json()
    print(f"✅ 更新成功")
    print(f"   is_urgent: {updated2['is_urgent']}")
    print(f"   urgent_remark: {updated2['urgent_remark']}")
    print(f"   urgent_fee: {updated2['urgent_fee']}")
    print(f"   total_amount: {updated2['total_amount']}")
    expected_total = 75 + 35
    if abs(updated2['total_amount'] - expected_total) < 0.01:
        print(f"✅ 重新加急后总价正确")
    else:
        print(f"❌ 总价计算错误，预期 {expected_total}，实际 {updated2['total_amount']}")
    
    last_log = updated2["status_logs"][-1]
    print(f"   最后一条日志类型: {last_log['log_type']}")
    print(f"   urgent_changed: {last_log['urgent_changed']}")
    print(f"   from_urgent: {last_log['from_urgent']}")
    print(f"   to_urgent: {last_log['to_urgent']}")
    print(f"   to_urgent_remark: {last_log['to_urgent_remark']}")
    if last_log['log_type'] == 'urgent_change' and last_log['urgent_changed'] and last_log['to_urgent']:
        print(f"✅ 重新加急的变更已正确记录到日志")
    else:
        print(f"❌ 重新加急的变更未正确记录")
else:
    print(f"❌ 错误: {resp.text}")

print("\n" + "=" * 70)
print("测试8: 更新订单 - 仅修改加急备注")
print("=" * 70)
update_data3 = {
    "urgent_remark": "客户改为明天上午10点前取"
}
resp = requests.put(f"{base_url}/orders/{order_id}", json=update_data3, headers=headers)
if resp.status_code == 200:
    updated3 = resp.json()
    print(f"✅ 更新成功")
    print(f"   urgent_remark: {updated3['urgent_remark']}")
    
    last_log = updated3["status_logs"][-1]
    print(f"   最后一条日志类型: {last_log['log_type']}")
    print(f"   urgent_remark_changed: {last_log['urgent_remark_changed']}")
    print(f"   from_urgent_remark: {last_log['from_urgent_remark']}")
    print(f"   to_urgent_remark: {last_log['to_urgent_remark']}")
    if last_log['log_type'] == 'urgent_change' and last_log['urgent_remark_changed']:
        print(f"✅ 加急备注变更已正确记录到日志")
    else:
        print(f"❌ 加急备注变更未正确记录")
else:
    print(f"❌ 错误: {resp.text}")

print("\n" + "=" * 70)
print("测试9: 管理员更新服务项目加急配置")
print("=" * 70)
service_update = {
    "urgent_fee": 20.0,
    "urgent_description": "加急费20元，4小时内取件"
}
resp = requests.put(f"{base_url}/admin/services/1", json=service_update, headers=admin_headers)
if resp.status_code == 200:
    updated_service = resp.json()
    print(f"✅ 更新服务项目加急配置成功")
    print(f"   urgent_fee: {updated_service['urgent_fee']}")
    print(f"   urgent_description: {updated_service['urgent_description']}")
else:
    print(f"❌ 错误: {resp.text}")

print("\n" + "=" * 70)
print("测试10: 管理员更新门店加急默认配置")
print("=" * 70)
store_update = {
    "default_urgent_fee": 15.0,
    "default_urgent_description": "门店默认加急费15元，24小时内取件"
}
resp = requests.put(f"{base_url}/admin/stores/1", json=store_update, headers=admin_headers)
if resp.status_code == 200:
    updated_store = resp.json()
    print(f"✅ 更新门店加急配置成功")
    print(f"   default_urgent_fee: {updated_store['default_urgent_fee']}")
    print(f"   default_urgent_description: {updated_store['default_urgent_description']}")
else:
    print(f"❌ 错误: {resp.text}")

print("\n" + "=" * 70)
print("测试11: 创建非加急订单验证默认值")
print("=" * 70)
order_data2 = {
    "customer_name": "普通客户",
    "customer_phone": "13900139999",
    "store_id": 1,
    "remark": "普通订单",
    "items": [
        {
            "service_item_id": 1,
            "service_name": "普通干洗",
            "quantity": 1,
            "unit_price": 35.0,
            "subtotal": 35.0,
            "remark": ""
        }
    ]
}
resp = requests.post(f"{base_url}/orders", json=order_data2, headers=headers)
if resp.status_code == 200:
    order2 = resp.json()
    print(f"✅ 订单创建成功")
    print(f"   is_urgent: {order2['is_urgent']}")
    print(f"   urgent_fee: {order2['urgent_fee']}")
    print(f"   total_amount: {order2['total_amount']}")
    if not order2['is_urgent'] and order2['urgent_fee'] == 0 and order2['total_amount'] == 35:
        print(f"✅ 非加急订单默认值正确")
    else:
        print(f"❌ 非加急订单默认值错误")
else:
    print(f"❌ 错误: {resp.text}")

print("\n" + "=" * 70)
print("🎉 所有加急功能测试完成！")
print("=" * 70)
