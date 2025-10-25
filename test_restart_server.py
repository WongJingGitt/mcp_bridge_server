#!/usr/bin/env python3
"""
测试单独重启服务功能
"""

import requests
import json

BASE_URL = "http://localhost:3849"

def test_restart_server():
    """测试重启单个服务"""
    
    print("=== 测试单独重启服务功能 ===\n")
    
    # 1. 获取当前所有服务
    print("1. 获取当前所有服务...")
    response = requests.get(f"{BASE_URL}/tools")
    if response.status_code == 200:
        services = response.json().get("services", [])
        print(f"   当前有 {len(services)} 个服务:")
        for service in services:
            print(f"   - {service['name']}: {service['description']}")
    else:
        print(f"   获取服务列表失败: {response.status_code}")
        return
    
    if not services:
        print("   没有可用的服务")
        return
    
    # 2. 选择第一个服务进行重启测试
    target_server = services[0]['name']
    print(f"\n2. 重启服务: {target_server}")
    
    response = requests.post(
        f"{BASE_URL}/restart-server",
        json={"serverName": target_server}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ {result['message']}")
        print(f"   ✓ 工具数量: {result.get('toolCount', 0)}")
    else:
        print(f"   ✗ 重启失败: {response.status_code}")
        print(f"   错误: {response.text}")
        return
    
    # 3. 验证服务是否正常
    print(f"\n3. 验证服务是否正常...")
    response = requests.get(f"{BASE_URL}/tools?serverName={target_server}")
    if response.status_code == 200:
        tools = response.json().get("tools", [])
        print(f"   ✓ 服务正常，有 {len(tools)} 个工具")
    else:
        print(f"   ✗ 服务异常: {response.status_code}")


def test_shutdown_server():
    """测试关闭单个服务"""
    
    print("\n\n=== 测试关闭单个服务功能 ===\n")
    
    # 1. 获取当前所有服务
    print("1. 获取当前所有服务...")
    response = requests.get(f"{BASE_URL}/tools")
    if response.status_code == 200:
        services = response.json().get("services", [])
        print(f"   当前有 {len(services)} 个服务")
    else:
        print(f"   获取服务列表失败: {response.status_code}")
        return
    
    if len(services) < 2:
        print("   服务数量不足，跳过关闭测试")
        return
    
    # 2. 关闭第二个服务
    target_server = services[1]['name']
    print(f"\n2. 关闭服务: {target_server}")
    
    response = requests.post(
        f"{BASE_URL}/shutdown-server",
        json={"serverName": target_server}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ {result['message']}")
    else:
        print(f"   ✗ 关闭失败: {response.status_code}")
        print(f"   错误: {response.text}")
        return
    
    # 3. 验证服务已关闭
    print(f"\n3. 验证服务列表...")
    response = requests.get(f"{BASE_URL}/tools")
    if response.status_code == 200:
        services_after = response.json().get("services", [])
        print(f"   当前有 {len(services_after)} 个服务 (之前: {len(services)})")
        if len(services_after) == len(services) - 1:
            print(f"   ✓ 服务 {target_server} 已成功关闭")
        else:
            print(f"   ⚠ 服务数量不符合预期")


if __name__ == "__main__":
    try:
        # 先测试重启
        test_restart_server()
        
        # 再测试关闭
        # test_shutdown_server()  # 如果想测试关闭功能，取消注释
        
        print("\n\n测试完成！")
        
    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到服务器，请确保 MCP Bridge Server 正在运行")
    except Exception as e:
        print(f"测试出错: {e}")
        import traceback
        traceback.print_exc()
