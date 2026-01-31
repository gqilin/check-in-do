#!/usr/bin/env python3
"""
随机延迟执行脚本
在指定时间范围内随机延迟执行主程序
"""
import os
import random
import time
import signal
import sys
from datetime import datetime, timedelta

# 全局超时设置
SCRIPT_TIMEOUT = 600  # 10分钟总超时

def get_random_delay():
    """根据当前小时返回随机延迟时间（分钟）"""
    now = datetime.now()
    hour = now.hour
    
    # 在CI/CD环境中，使用更短的延迟时间
    # GitHub Actions有超时限制，避免长时间等待
    delay_ranges = {
        # UTC时间对应的北京时间 - 生产环境缩短延迟
        1: (0, 5),     # 9:00-11:00 北京时间
        7: (0, 5),     # 15:00-17:00 北京时间  
        9: (0, 5),     # 17:00-19:00 北京时间
        13: (0, 5),    # 21:00-23:00 北京时间
        19: (0, 5),    # 3:00-5:00 北京时间
    }
    
    delay_range = delay_ranges.get(hour, (1, 3))
    return random.randint(*delay_range)

def main():
    print("🔧 初始化随机延迟脚本...")
    
    delay_minutes = get_random_delay()
    delay_seconds = delay_minutes * 60
    
    print(f"🕐 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️  随机延迟: {delay_minutes} 分钟")
    print(f"⏰ 预计执行时间: {(datetime.now() + timedelta(seconds=delay_seconds)).strftime('%Y-%m-%d %H:%M:%S')}")
    
    if delay_minutes > 0:
        print(f"💤 等待 {delay_minutes} 分钟后执行...")
        time.sleep(delay_seconds)
    
    print("🚀 开始执行签到脚本...")
    
    try:
        # 导入并运行主脚本
        print("📦 导入主模块...")
        from main import LinuxDoBrowser
        
        print("🌐 初始化浏览器...")
        l = LinuxDoBrowser()
        
        print("▶️  开始执行签到...")
        l.run()
        
        print("✅ 脚本执行完成")
    except Exception as e:
        print(f"❌ 脚本执行失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()