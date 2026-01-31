#!/usr/bin/env python3
"""
临时测试脚本 - 使用环境变量或默认值
"""

import os

# 临时设置（仅用于测试！）
# 在GitHub Actions中，这些会被secrets覆盖
os.environ.setdefault('LINUXDO_USERNAME', 'your_username_here')
os.environ.setdefault('LINUXDO_PASSWORD', 'your_password_here')

# 导入并运行主脚本
from main import LinuxDoBrowser

if __name__ == "__main__":
    l = LinuxDoBrowser()
    l.run()