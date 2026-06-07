import requests
import json

base_url = "http://localhost:8112"

print("=" * 70)
print("测试: 加急功能修复验证")
print("=" * 70)

resp = requests.post(f"{base_url}/auth/login", 
    data={"username": "operator", "password": "operator123"})
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✅ 操作员登录成功")

print("\n" + "=" * 70)
print("修复1验证: 非加急订单不能填写加急备注")
print("=" * 70)

order_data = {
    "customer_name": "测试修复1",
    "customer_phone": "13800000001",
    "store_id": 1,
    "remark": "普通备注",
    "is_urgent": False,
    "urgent_remark": "这是加急备注",
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
resp = requests.post(f"{base_url}/orders", json=order_data, headers=headers)
print(f"尝试非加急订单填写加急备注: 状态码={resp.status_code}")
if resp.status_code == 400:
    print(f"✅ 正确拒绝！错误信息: {resp.json()['detail']}")
else:
    print(f"❌ 应该被拒绝但没有！状态码: {resp.status_code}, 响应: {resp.text}")

print("\n" + "=" * 70)
print("修复2验证: 不存在的服务项目不能下单")
print("=" * 70)

order_data2 = {
    "customer_name": "测试修复2",
    "customer_phone": "13800000002",
    "store_id": 1,
    "remark": "",
    "items": [
        {
            "service_item_id": 9999,
            "service_name": "不存在的服务",
            "quantity": 1,
            "unit_price": 100.0,
            "subtotal": 100.0,
            "remark": ""
        }
    ]
}
resp = requests.post(f"{base_url}/orders", json=order_data2, headers=headers)
print(f"尝试使用不存在的服务项目下单: 状态码={resp.status_code}")
if resp.status_code == 404:
    print(f"✅ 正确拒绝！错误信息: {resp.json()['detail']}")
else:
    print(f"❌ 应该被拒绝但没有！状态码: {resp.status_code}, 响应: {resp.text}")

print("\n" + "=" * 70)
print("修复3验证: 取消加急后加急备注自动清空")
print("=" * 70)

order_data3 = {
    "customer_name": "测试修复3",
    "customer_phone": "13800000003",
    "store_id": 1,
    "remark": "",
    "is_urgent": True,
    "urgent_remark": "明天上午取",
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
resp = requests.post(f"{base_url}/orders", json=order_data3, headers=headers)
if resp.status_code == 200:
    order = resp.json()
    order_id = order["id"]
    print(f"✅ 创建加急订单成功")
    print(f"   is_urgent: {order['is_urgent']}")
    print(f"   urgent_remark: {order['urgent_remark']}")
    print(f"   urgent_fee: {order['urgent_fee']}")
    
    update_data = {
        "is_urgent": False
    }
    resp = requests.put(f"{base_url}/orders/{order_id}", json=update_data, headers=headers)
    if resp.status_code == 200:
        updated = resp.json()
        print(f"✅ 取消加急成功")
        print(f"   is_urgent: {updated['is_urgent']}")
        print(f"   urgent_remark: {updated['urgent_remark']}")
        print(f"   urgent_fee: {updated['urgent_fee']}")
        if not updated['is_urgent'] and updated['urgent_remark'] is None and updated['urgent_fee'] == 0:
            print(f"✅ 取消加急后，加急备注已自动清空，加急费已归零")
        else:
            print(f"❌ 取消加急后数据不正确")
    else:
        print(f"❌ 取消加急失败: {resp.text}")
else:
    print(f"❌ 创建加急订单失败: {resp.text}")

print("\n" + "=" * 70)
print("额外测试: 更新时非加急订单填加急备注应拒绝")
print("=" * 70)

order_data4 = {
    "customer_name": "测试修复4",
    "customer_phone": "13800000004",
    "store_id": 1,
    "remark": "",
    "is_urgent": False,
    "items": [
        {
            "service_item_id": 2,
            "service_name": "高档西装干洗",
            "quantity": 1,
            "unit_price": 88.0,
            "subtotal": 88.0,
            "remark": ""
        }
    ]
}
resp = requests.post(f"{base_url}/orders", json=order_data4, headers=headers)
if resp.status_code == 200:
    order4 = resp.json()
    order4_id = order4["id"]
    print(f"✅ 创建非加急订单成功")
    
    update_data4 = {
        "urgent_remark": "我要加急备注"
    }
    resp = requests.put(f"{base_url}/orders/{order4_id}", json=update_data4, headers=headers)
    print(f"尝试给非加急订单填加急备注: 状态码={resp.status_code}")
    if resp.status_code == 400:
        print(f"✅ 正确拒绝！错误信息: {resp.json()['detail']}")
    else:
        print(f"❌ 应该被拒绝但没有！状态码: {resp.status_code}, 响应: {resp.text}")
else:
    print(f"❌ 创建非加急订单失败: {resp.text}")

print("\n" + "=" * 70)
print("额外测试: 同时取消加急并填加急备注")
print("=" * 70)

order_data5 = {
    "customer_name": "测试修复5",
    "customer_phone": "13800000005",
    "store_id": 1,
    "remark": "",
    "is_urgent": True,
    "urgent_remark": "原始加急备注",
    "items": [
        {
            "service_item_id": 3,
            "service_name": "水洗",
            "quantity": 1,
            "unit_price": 20.0,
            "subtotal": 20.0,
            "remark": ""
        }
    ]
}
resp = requests.post(f"{base_url}/orders", json=order_data5, headers=headers)
if resp.status_code == 200:
    order5 = resp.json()
    order5_id = order5["id"]
    print(f"✅ 创建加急订单成功")
    
    update_data5 = {
        "is_urgent": False,
        "urgent_remark": "这是新的加急备注"
    }
    resp = requests.put(f"{base_url}/orders/{order5_id}", json=update_data5, headers=headers)
    print(f"同时取消加急并填加急备注: 状态码={resp.status_code}")
    if resp.status_code == 400:
        print(f"✅ 正确拒绝！错误信息: {resp.json()['detail']}")
    else:
        print(f"❌ 应该被拒绝但没有！状态码: {resp.status_code}, 响应: {resp.text}")
else:
    print(f"❌ 创建加急订单失败: {resp.text}")

print("\n" + "=" * 70)
print("🎉 所有修复验证测试完成！")
print("=" * 70)
