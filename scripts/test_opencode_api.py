#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 OpenCode API 是否能正常接收和响应消息
模拟 Obsidian 插件的行为
"""

import requests
import json
import sys

# Windows 编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

OPENCODE_URL = "http://127.0.0.1:14096"

def test_api_endpoints():
    """测试各个 API 端点"""

    print("=" * 60)
    print("OpenCode API 测试")
    print("=" * 60)

    # 1. 测试根路径
    print("\n[1] 测试 GET /")
    try:
        r = requests.get(f"{OPENCODE_URL}/", timeout=5)
        print(f"    Status: {r.status_code}")
        print(f"    Content-Type: {r.headers.get('Content-Type')}")
    except Exception as e:
        print(f"    Error: {e}")

    # 2. 测试创建会话
    print("\n[2] 测试 POST /session")
    try:
        payload = {
            "directory": "D:\\ajie\\study\\AI-Knowledge",
            "agent": "build"
        }
        r = requests.post(f"{OPENCODE_URL}/session", json=payload, timeout=10)
        print(f"    Status: {r.status_code}")

        if r.status_code == 200:
            session = r.json()
            session_id = session.get("id")
            print(f"    Session ID: {session_id}")
            return session_id
        else:
            print(f"    Error: {r.text[:200]}")
    except Exception as e:
        print(f"    Error: {e}")

    return None

def test_send_message(session_id):
    """测试发送消息"""

    if not session_id:
        print("\n[!] 跳过消息测试（没有 session）")
        return

    print(f"\n[3] 测试发送消息到 session: {session_id}")

    try:
        payload = {
            "content": "你好，请回复'收到'",
            "directory": "D:\\ajie\\study\\AI-Knowledge"
        }

        url = f"{OPENCODE_URL}/session/{session_id}/conversation"
        print(f"    URL: {url}")
        print(f"    Payload: {payload}")

        r = requests.post(url, json=payload, timeout=30, stream=True)
        print(f"    Status: {r.status_code}")
        print(f"    Headers: {dict(r.headers)}")

        if r.status_code == 200:
            print("\n    Response:")
            for line in r.iter_lines(decode_unicode=True):
                if line:
                    print(f"    {line[:200]}")
        else:
            print(f"    Error: {r.text[:500]}")

    except Exception as e:
        print(f"    Error: {e}")

if __name__ == '__main__':
    session_id = test_api_endpoints()
    test_send_message(session_id)

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
