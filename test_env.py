#!/usr/bin/env python3
"""
测试脚本 - 用于验证环境配置
"""

import os
import sys

def test_environment():
    print("=== 环境测试 ===")
    print(f"Python版本: {sys.version}")
    
    # 检查必需的环境变量
    required_vars = ['LINUXDO_USERNAME', 'LINUXDO_PASSWORD']
    missing_vars = []
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}: 已设置")
        else:
            print(f"❌ {var}: 未设置")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"缺少必需的环境变量: {', '.join(missing_vars)}")
        return False
    
    # 测试导入依赖
    print("\n=== 依赖测试 ===")
    try:
        from DrissionPage import ChromiumOptions, Chromium
        print("✅ DrissionPage 导入成功")
    except ImportError as e:
        print(f"❌ DrissionPage 导入失败: {e}")
        return False
    
    try:
        from loguru import logger
        print("✅ loguru 导入成功")
    except ImportError as e:
        print(f"❌ loguru 导入失败: {e}")
        return False
    
    try:
        import requests
        print("✅ requests 导入成功")
    except ImportError as e:
        print(f"❌ requests 导入失败: {e}")
        return False
    
    try:
        from bs4 import BeautifulSoup
        print("✅ BeautifulSoup 导入成功")
    except ImportError as e:
        print(f"❌ BeautifulSoup 导入失败: {e}")
        return False
    
    print("\n✅ 所有测试通过!")
    return True

if __name__ == "__main__":
    success = test_environment()
    sys.exit(0 if success else 1)