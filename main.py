"""
cron: 0 */6 * * *
new Env("Linux.Do 签到")
"""

import os
import random
import time
import functools
import sys
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from loguru import logger
from DrissionPage import ChromiumOptions, Chromium
from tabulate import tabulate
from curl_cffi import requests
from bs4 import BeautifulSoup


def retry_decorator(retries=3, min_delay=5, max_delay=10):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == retries - 1:  # 最后一次尝试
                        logger.error(f"函数 {func.__name__} 最终执行失败: {str(e)}")
                    logger.warning(
                        f"函数 {func.__name__} 第 {attempt + 1}/{retries} 次尝试失败: {str(e)}"
                    )
                    if attempt < retries - 1:
                        sleep_s = random.uniform(min_delay, max_delay)
                        logger.info(
                            f"将在 {sleep_s:.2f}s 后重试 ({min_delay}-{max_delay}s 随机延迟)"
                        )
                        time.sleep(sleep_s)
            return None

        return wrapper

    return decorator


os.environ.pop("DISPLAY", None)
os.environ.pop("DYLD_LIBRARY_PATH", None)

USERNAME = os.environ.get("LINUXDO_USERNAME")
PASSWORD = os.environ.get("LINUXDO_PASSWORD")
BROWSE_ENABLED = os.environ.get("BROWSE_ENABLED", "true").strip().lower() not in [
    "false",
    "0",
    "off",
]
if not USERNAME:
    USERNAME = os.environ.get("USERNAME")
if not PASSWORD:
    PASSWORD = os.environ.get("PASSWORD")
GOTIFY_URL = os.environ.get("GOTIFY_URL")  # Gotify 服务器地址
GOTIFY_TOKEN = os.environ.get("GOTIFY_TOKEN")  # Gotify 应用的 API Token
SC3_PUSH_KEY = os.environ.get("SC3_PUSH_KEY")  # Server酱³ SendKey
WXPUSH_URL = os.environ.get("WXPUSH_URL")  # wxpush 服务器地址
WXPUSH_TOKEN = os.environ.get("WXPUSH_TOKEN")  # wxpush 的 token
QQ_EMAIL = os.environ.get("QQ_EMAIL")  # 接收通知的QQ邮箱
QQ_EMAIL_SMTP_PASSWORD = os.environ.get("QQ_EMAIL_SMTP_PASSWORD")  # QQ邮箱SMTP授权码

HOME_URL = "https://linux.do/"
LOGIN_URL = "https://linux.do/login"
SESSION_URL = "https://linux.do/session"
CSRF_URL = "https://linux.do/session/csrf"


class LinuxDoBrowser:
    def __init__(self) -> None:
        from sys import platform

        if platform == "linux" or platform == "linux2":
            platformIdentifier = "X11; Linux x86_64"
        elif platform == "darwin":
            platformIdentifier = "Macintosh; Intel Mac OS X 10_15_7"
        elif platform == "win32":
            platformIdentifier = "Windows NT 10.0; Win64; x64"
        else:
            platformIdentifier = "X11; Linux x86_64"

        co = (
            ChromiumOptions()
            .headless(True)
            .incognito(True)
            .set_argument("--no-sandbox")
            .set_argument("--disable-dev-shm-usage")
            .set_argument("--disable-gpu")
            .set_argument("--disable-software-rasterizer")
            .set_argument("--disable-background-timer-throttling")
            .set_argument("--disable-backgrounding-occluded-windows")
            .set_argument("--disable-renderer-backgrounding")
            .set_argument("--disable-features=TranslateUI")
            .set_argument("--disable-ipc-flooding-protection")
            .set_argument("--disable-web-security")
            .set_argument("--disable-features=VizDisplayCompositor")
        )
        co.set_user_agent(
            f"Mozilla/5.0 ({platformIdentifier}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        )
        self.browser = Chromium(co)
        self.page = self.browser.new_tab()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Language": "zh-CN,zh;q=0.9",
            }
        )
        
        # 添加统计变量
        self.stats = {
            'total_topics': 0,
            'successful_likes': 0,
            'failed_likes': 0,
            'scroll_actions': 0,
            'browse_time': 0
        }

    def login(self):
        logger.info("开始登录")
        # Step 1: Get CSRF Token
        logger.info("获取 CSRF token...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": LOGIN_URL,
        }
        resp_csrf = self.session.get(CSRF_URL, headers=headers, impersonate="chrome136")
        csrf_data = resp_csrf.json()
        csrf_token = csrf_data.get("csrf")
        logger.info(f"CSRF Token obtained: {csrf_token[:10]}...")

        # Step 2: Login
        logger.info("正在登录...")
        headers.update(
            {
                "X-CSRF-Token": csrf_token,
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Origin": "https://linux.do",
            }
        )

        data = {
            "login": USERNAME,
            "password": PASSWORD,
            "second_factor_method": "1",
            "timezone": "Asia/Shanghai",
        }

        try:
            resp_login = self.session.post(
                SESSION_URL, data=data, impersonate="chrome136", headers=headers
            )

            if resp_login.status_code == 200:
                response_json = resp_login.json()
                if response_json.get("error"):
                    logger.error(f"登录失败: {response_json.get('error')}")
                    return False
                logger.info("登录成功!")
            else:
                logger.error(f"登录失败，状态码: {resp_login.status_code}")
                logger.error(resp_login.text)
                return False
        except Exception as e:
            logger.error(f"登录请求异常: {e}")
            return False

        self.print_connect_info()  # 打印连接信息

        # Step 3: Pass cookies to DrissionPage
        logger.info("同步 Cookie 到 DrissionPage...")

        # Convert requests cookies to DrissionPage format
        # Using standard requests.utils to parse cookiejar if possible, or manual extraction
        # requests.Session().cookies is a specialized object, but might support standard iteration

        # We can iterate over the cookies manually if dict_from_cookiejar doesn't work perfectly
        # or convert to dict first.
        # Assuming requests behaves like requests:

        cookies_dict = self.session.cookies.get_dict()

        dp_cookies = []
        for name, value in cookies_dict.items():
            dp_cookies.append(
                {
                    "name": name,
                    "value": value,
                    "domain": ".linux.do",
                    "path": "/",
                }
            )

        self.page.set.cookies(dp_cookies)

        logger.info("Cookie 设置完成，导航至 linux.do...")
        self.page.get(HOME_URL)

        time.sleep(5)
        try:
            user_ele = self.page.ele("@id=current-user")
        except Exception as e:
            logger.warning(f"登录验证失败: {str(e)}")
            return True
        if not user_ele:
            # Fallback check for avatar
            if "avatar" in self.page.html:
                logger.info("登录验证成功 (通过 avatar)")
                return True
            logger.error("登录验证失败 (未找到 current-user)")
            return False
        else:
            logger.info("登录验证成功")
            return True

    def click_topic(self):
        topic_list = self.page.ele("@id=list-area").eles(".:title")
        if not topic_list:
            logger.error("未找到主题帖")
            return False
        
        # 在CI环境中减少阅读数量，优化执行时间
        available_count = len(topic_list)
        self.stats['total_topics'] = available_count
        
        # CI环境下的阅读策略：大幅减少阅读数量
        if available_count <= 10:
            target_count = random.randint(2, min(available_count, 5))
        elif available_count <= 20:
            target_count = random.randint(3, 8)
        else:
            target_count = random.randint(5, 12)  # 最多阅读12个帖子
        
        logger.info(f"发现 {available_count} 个主题帖，随机选择 {target_count} 个进行阅读")
        selected_topics = random.sample(topic_list, target_count)
        
        # 记录实际阅读数量
        self.stats['topics_read'] = target_count
        
        # 分批处理，避免同时打开太多标签页
        batch_size = 10
        for i in range(0, len(selected_topics), batch_size):
            batch = selected_topics[i:i + batch_size]
            logger.info(f"处理第 {i//batch_size + 1} 批，共 {len(batch)} 个帖子")
            
            for topic in batch:
                self.click_one_topic(topic.attr("href"))
            
            # 每批之间短暂休息，模拟真实用户行为
            if i + batch_size < len(selected_topics):
                rest_time = random.uniform(5, 15)
                logger.info(f"批次间休息 {rest_time:.1f} 秒...")
                time.sleep(rest_time)
        
        logger.info(f"✅ 本轮完成阅读 {target_count} 个帖子")
        return True

    @retry_decorator()
    def click_one_topic(self, topic_url):
        new_page = self.browser.new_tab()
        try:
            new_page.get(topic_url)
            
            # 增加点赞概率，提升到40-60%
            like_probability = random.uniform(0.4, 0.6)
            if random.random() < like_probability:
                self.click_like(new_page)
            
            # 30%的概率进行多次点赞（如果有多个可点赞的内容）
            if random.random() < 0.3:
                time.sleep(random.uniform(2, 4))
                self.click_like(new_page)
            
            self.browse_post(new_page)
        finally:
            try:
                new_page.close()
            except Exception:
                pass

    def browse_post(self, page):
        prev_url = None
        scroll_count = 0
        
        # 在CI环境中使用更快速的浏览策略
        max_scrolls = random.randint(5, 10)  # 减少到5-10次滚动
        
        # 随机决定浏览策略 - 优化为CI环境友好
        browse_strategy = random.choice(['quick', 'fast'])
        if browse_strategy == 'quick':
            max_scrolls = random.randint(3, 6)
            wait_range = (0.5, 1.5)
        else:  # fast
            max_scrolls = random.randint(5, 10)
            wait_range = (1, 2)
        
        logger.info(f"浏览策略: {browse_strategy}, 最大滚动次数: {max_scrolls}")
        
        for scroll_count in range(max_scrolls):
            # 更大的滚动距离范围，模拟不同浏览速度
            if browse_strategy == 'quick':
                scroll_distance = random.randint(800, 1200)
            elif browse_strategy == 'normal':
                scroll_distance = random.randint(550, 650)
            else:  # deep
                scroll_distance = random.randint(300, 500)
            
            logger.info(f"向下滚动 {scroll_distance} 像素...")
            page.run_js(f"window.scrollBy(0, {scroll_distance})")
            
            # 随机向上滚动一下，模拟回看内容
            if scroll_count > 3 and random.random() < 0.15:
                up_scroll = random.randint(-200, -100)
                page.run_js(f"window.scrollBy(0, {up_scroll})")
                logger.info(f"向上滚动 {abs(up_scroll)} 像素，回看内容")

            # 降低早期退出概率，让浏览更充分
            early_exit_prob = 0.01 if browse_strategy == 'deep' else (0.02 if browse_strategy == 'normal' else 0.03)
            if random.random() < early_exit_prob:
                logger.success("随机退出浏览")
                break

            # 检查是否到达页面底部
            at_bottom = page.run_js(
                "window.scrollY + window.innerHeight >= document.body.scrollHeight - 100"
            )
            current_url = page.url
            if current_url != prev_url:
                prev_url = current_url
            elif at_bottom and prev_url == current_url:
                logger.success("已到达页面底部，退出浏览")
                break

            # 根据策略调整等待时间
            wait_time = random.uniform(*wait_range)
            self.stats['scroll_actions'] += 1
            self.stats['browse_time'] += wait_time
            
            logger.info(f"等待 {wait_time:.2f} 秒...")
            time.sleep(wait_time)
            
            # 偶尔模拟点击相关链接或展开内容
            if scroll_count > 5 and random.random() < 0.1:
                try:
                    # 尝试点击一些展开链接
                    expand_links = page.eles("text=展开", timeout=2)
                    if expand_links:
                        random.choice(expand_links).click()
                        logger.info("点击展开链接")
                        self.stats['browse_time'] += random.uniform(1, 2)
                        time.sleep(random.uniform(1, 2))
                except:
                    pass
        
        logger.info(f"帖子浏览完成，共滚动 {scroll_count + 1} 次")
        self.stats['scroll_actions'] += scroll_count + 1

    def run(self):
        import time
        start_time = time.time()
        
        try:
            logger.info("🚀 开始执行签到任务")
            login_res = self.login()
            if not login_res:  # 登录
                logger.warning("登录验证失败")

            if BROWSE_ENABLED:
                browse_start = time.time()
                click_topic_res = self.click_topic()  # 点击主题
                browse_time = time.time() - browse_start
                logger.info(f"⏱️ 浏览耗时: {browse_time:.1f} 秒")
                
                if not click_topic_res:
                    logger.error("点击主题失败，程序终止")
                    return
                logger.info("✅ 完成浏览任务")

            self.send_notifications(BROWSE_ENABLED)  # 发送通知
            
            total_time = time.time() - start_time
            logger.info(f"🏁 总执行时间: {total_time:.1f} 秒")
            
        except Exception as e:
            logger.error(f"❌ 执行过程中出错: {str(e)}")
            raise
        finally:
            try:
                self.page.close()
            except Exception:
                pass
            try:
                self.browser.quit()
            except Exception:
                pass

    def click_like(self, page):
        try:
            # 专门查找未点赞的按钮
            like_button = page.ele(".discourse-reactions-reaction-button")
            if like_button:
                logger.info("找到未点赞的帖子，准备点赞")
                like_button.click()
                self.stats['successful_likes'] += 1
                logger.info("点赞成功")
                time.sleep(random.uniform(1, 2))
            else:
                logger.info("帖子可能已经点过赞了")
                self.stats['successful_likes'] += 1  # 也算成功，因为已经点赞
        except Exception as e:
            self.stats['failed_likes'] += 1
            logger.error(f"点赞失败: {str(e)}")

    def print_connect_info(self):
        logger.info("获取连接信息")
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        }
        resp = self.session.get(
            "https://connect.linux.do/", headers=headers, impersonate="chrome136"
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.select("table tr")
        info = []

        for row in rows:
            cells = row.select("td")
            if len(cells) >= 3:
                project = cells[0].text.strip()
                current = cells[1].text.strip() if cells[1].text.strip() else "0"
                requirement = cells[2].text.strip() if cells[2].text.strip() else "0"
                info.append([project, current, requirement])

        print("--------------Connect Info-----------------")
        print(tabulate(info, headers=["项目", "当前", "要求"], tablefmt="pretty"))

    def send_notifications(self, browse_enabled):
        # 生成统计报告
        stats_report = f"\n📊 本次执行统计:\n"
        stats_report += f"📝 发现主题: {self.stats['total_topics']} 个\n"
        stats_report += f"👍 成功点赞: {self.stats['successful_likes']} 次\n"
        stats_report += f"❌ 点赞失败: {self.stats['failed_likes']} 次\n"
        stats_report += f"📜 滚动操作: {self.stats['scroll_actions']} 次\n"
        stats_report += f"⏱️ 浏览时长: {self.stats['browse_time']:.1f} 秒"
        
        logger.info(f"📊 统计信息: {stats_report}")
        
        status_msg = f"✅每日登录成功: {USERNAME}"
        if browse_enabled:
            status_msg += f" + 浏览{self.stats.get('topics_read', 0)}个帖子"
            status_msg += f" + 点赞{self.stats['successful_likes']}次"
        
        # 估算今日贡献
        daily_contribution = self.stats['successful_likes'] * 10 + self.stats['scroll_actions'] * 2
        status_msg += f"\n📈 预估贡献值: +{daily_contribution}"

        if GOTIFY_URL and GOTIFY_TOKEN:
            try:
                response = requests.post(
                    f"{GOTIFY_URL}/message",
                    params={"token": GOTIFY_TOKEN},
                    json={"title": "LINUX DO", "message": status_msg, "priority": 1},
                    timeout=10,
                )
                response.raise_for_status()
                logger.success("消息已推送至Gotify")
            except Exception as e:
                logger.error(f"Gotify推送失败: {str(e)}")
        else:
            logger.info("未配置Gotify环境变量，跳过通知发送")

        if SC3_PUSH_KEY:
            match = re.match(r"sct(\d+)t", SC3_PUSH_KEY, re.I)
            if not match:
                logger.error(
                    "❌ SC3_PUSH_KEY格式错误，未获取到UID，无法使用Server酱³推送"
                )
                return

            uid = match.group(1)
            url = f"https://{uid}.push.ft07.com/send/{SC3_PUSH_KEY}"
            params = {"title": "LINUX DO", "desp": status_msg}

            attempts = 5
            for attempt in range(attempts):
                try:
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    logger.success(f"Server酱³推送成功: {response.text}")
                    break
                except Exception as e:
                    logger.error(f"Server酱³推送失败: {str(e)}")
                    if attempt < attempts - 1:
                        sleep_time = random.randint(180, 360)
                        logger.info(f"将在 {sleep_time} 秒后重试...")
                        time.sleep(sleep_time)

        if WXPUSH_URL and WXPUSH_TOKEN:
            try:
                response = requests.post(
                    f"{WXPUSH_URL}/wxsend",
                    headers={
                        "Authorization": WXPUSH_TOKEN,
                        "Content-Type": "application/json",
                    },
                    json={"title": "LINUX DO", "content": status_msg},
                    timeout=10,
                )
                response.raise_for_status()
                logger.success(f"wxpush 推送成功: {response.text}")
            except Exception as e:
                logger.error(f"wxpush 推送失败: {str(e)}")
        else:
            logger.info("未配置 WXPUSH_URL 或 WXPUSH_TOKEN，跳过通知发送")

        if QQ_EMAIL and QQ_EMAIL_SMTP_PASSWORD:
            try:
                self.send_qq_email(status_msg, stats_report)
            except Exception as e:
                logger.error(f"QQ邮件发送失败: {str(e)}")
        else:
            logger.info("未配置 QQ_EMAIL 或 QQ_EMAIL_SMTP_PASSWORD，跳过邮件通知")

    def send_qq_email(self, status_msg, stats_report):
        """发送QQ邮件通知"""
        try:
            # 邮件内容
            subject = f"Linux.Do 自动签到报告 - {time.strftime('%Y-%m-%d %H:%M:%S')}"
            
            # 构建HTML邮件内容
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; line-height: 1.6; }}
                    .header {{ background: #4CAF50; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .stats {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                    .success {{ color: #4CAF50; }}
                    .info {{ color: #2196F3; }}
                    .footer {{ text-align: center; color: #666; padding: 20px; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🤖 Linux.Do 自动签到报告</h1>
                    <p>{time.strftime('%Y年%m月%d日 %H:%M')}</p>
                </div>
                
                <div class="content">
                    <h2 class="success">✅ 执行状态</h2>
                    <p><strong>{status_msg}</strong></p>
                    
                    <h2 class="info">📊 详细统计</h2>
                    <div class="stats">
                        <pre>{stats_report}</pre>
                    </div>
                    
                    <h2>🔧 系统信息</h2>
                    <ul>
                        <li>用户名: {USERNAME}</li>
                        <li>执行时间: {time.strftime('%Y-%m-%d %H:%M:%S')}</li>
                        <li>浏览器: Chrome Headless</li>
                        <li>平台: Linux (GitHub Actions)</li>
                    </ul>
                </div>
                
                <div class="footer">
                    <p>📧 本邮件由 Linux.Do 自动签到脚本发送</p>
                    <p>⏰ 下次执行时间: 随机时间段</p>
                </div>
            </body>
            </html>
            """
            
            # 创建邮件对象
            msg = MIMEMultipart('alternative')
            msg['From'] = Header(f"Linux.Do签到机器人 <{QQ_EMAIL.split('@')[0]}@qq.com>")
            msg['To'] = Header(f"用户 <{QQ_EMAIL}>")
            msg['Subject'] = Header(subject, 'utf-8')
            
            # 添加HTML内容
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # 连接QQ邮箱SMTP服务器
            smtp = smtplib.SMTP_SSL('smtp.qq.com', 465)
            smtp.set_debuglevel(0)  # 设置为1可查看SMTP交互日志
            
            # 登录SMTP服务器
            smtp.login(QQ_EMAIL.split('@')[0] + '@qq.com', QQ_EMAIL_SMTP_PASSWORD)
            
            # 发送邮件
            smtp.sendmail(QQ_EMAIL, QQ_EMAIL, msg.as_string())
            smtp.quit()
            
            logger.success("QQ邮件发送成功!")
            
        except Exception as e:
            logger.error(f"发送QQ邮件时出错: {str(e)}")
            raise


if __name__ == "__main__":
    if not USERNAME or not PASSWORD:
        print("Please set USERNAME and PASSWORD")
        exit(1)
    l = LinuxDoBrowser()
    l.run()
