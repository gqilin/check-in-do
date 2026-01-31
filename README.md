# Linux.Do 自动签到脚本

自动登录 Linux.do 论坛并完成每日签到和浏览任务的 Python 脚本。

## 功能特性

- ✅ 自动登录 Linux.do
- 📖 随机浏览10个主题帖
- 👍 随机点赞帖子
- 📱 多种推送通知支持（Gotify、Server酱³、wxpush）
- 🔄 自动重试机制
- 📊 显示Connect积分信息

## GitHub Actions 部署

### 1. Fork 本仓库到你的GitHub账号

### 2. 设置 Secrets
在你的GitHub仓库中进入 `Settings > Secrets and variables > Actions`，添加以下 Secrets：

**必需配置：**
- `LINUXDO_USERNAME`: 你的Linux.do用户名
- `LINUXDO_PASSWORD`: 你的Linux.do密码

**可选配置：**
- `BROWSE_ENABLED`: 是否启用浏览任务（true/false，默认true）
- `GOTIFY_URL`: Gotify服务器地址
- `GOTIFY_TOKEN`: Gotify应用的API Token
- `SC3_PUSH_KEY`: Server酱³的SendKey
- `WXPUSH_URL`: wxpush服务器地址
- `WXPUSH_TOKEN`: wxpush的token

### 3. 启用 Actions
1. 进入仓库的 `Actions` 标签页
2. 点击 `I understand my workflows, go ahead and enable them`

### 4. 手动测试
1. 进入 `Actions` 页面
2. 选择 `Linux.Do Daily Check-in` 工作流
3. 点击 `Run workflow` 手动触发一次测试

## 定时执行
脚本会在每天北京时间 6:00、12:00、18:00、00:00 自动执行。

## 通知配置

### Gotify
```bash
GOTIFY_URL="https://your-gotify-server.com"
GOTIFY_TOKEN="your-application-token"
```

### Server酱³
1. 访问 https://sct.ftqq.com/
2. 注册并获取SendKey
3. 配置到 `SC3_PUSH_KEY`

### wxpush
```bash
WXPUSH_URL="https://your-wxpush-server.com"
WXPUSH_TOKEN="your-authorization-token"
```

## 本地运行
```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export LINUXDO_USERNAME="your_username"
export LINUXDO_PASSWORD="your_password"

# 运行脚本
python main.py
```

## 注意事项
- 请确保密码正确，多次登录失败可能导致账号被临时锁定
- 建议开启通知功能，及时了解签到状态
- 脚本会自动处理重试和异常情况

## License
MIT License