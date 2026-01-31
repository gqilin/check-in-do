#!/usr/bin/env python3
"""
随机延迟执行脚本
在指定时间范围内随机延迟执行主程序
"""
import os
import random
import time
from datetime import datetime, timedelta

def get_random_delay():
    """根据当前小时返回随机延迟时间（分钟）"""
    now = datetime.now()
    hour = now.hour
    
    # 定义不同时间段的延迟范围（分钟）
    delay_ranges = {
        # UTC时间对应的北京时间
        1: (0, 120),   # 9:00-11:00 北京时间
        7: (0, 120),   # 15:00-17:00 北京时间  
        9: (0, 120),   # 17:00-19:00 北京时间
        13: (0, 120),  # 21:00-23:00 北京时间
        19: (0, 120),  # 3:00-5:00 北京时间
    }
    
    delay_range = delay_ranges.get(hour, (30, 60))
    return random.randint(*delay_range)

def main():
    delay_minutes = get_random_delay()
    delay_seconds = delay_minutes * 60
    
    print(f"🕐 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️  随机延迟: {delay_minutes} 分钟")
    print(f"⏰ 预计执行时间: {(datetime.now() + timedelta(seconds=delay_seconds)).strftime('%Y-%m-%d %H:%M:%S')}")
    
    if delay_minutes > 0:
        print(f"💤 等待 {delay_minutes} 分钟后执行...")
        time.sleep(delay_seconds)
    
    print("🚀 开始执行签到脚本...")
    
    # 导入并运行主脚本
    from main import LinuxDoBrowser
    
    l = LinuxDoBrowser()
    l.run()

if __name__ == "__main__":
    main()