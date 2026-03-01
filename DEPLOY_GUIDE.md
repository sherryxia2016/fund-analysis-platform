# 生产环境部署指南

本文档提供将基金分析平台部署到生产环境的详细步骤。

## 部署流程概览

部署分为两个独立的部分：

1.  **后端数据更新**：设置一个定时任务，每日自动从外部数据源拉取最新的基金数据，并进行处理。
2.  **前端应用部署**：将前端的 React 应用打包成静态文件，并由一个 Web 服务器托管。

---

## 1. 后端数据更新部署

后端数据更新是通过运行 `scripts/fetch_fund_data.py` 脚本来完成的。我们推荐使用 Linux 服务器上的 `cron` 来实现每日自动化运行。

### 步骤：

1.  **上传项目文件**:
    将整个 `fund_analysis_package` 项目目录上传到您的生产服务器。例如，上传到 `/home/your_user/fund_analysis_package`。

2.  **安装依赖**:
    在服务器上，进入 `scripts` 目录，并安装所需的 Python 库。
    ```bash
    cd /home/your_user/fund_analysis_package/scripts
    pip3 install pandas akshare
    ```

3.  **获取绝对路径**:
    您需要 Python 解释器和数据抓取脚本的绝对路径。
    *   运行 `which python3` 获取 Python 路径 (例如: `/usr/bin/python3`)。
    *   `fetch_fund_data.py` 的绝对路径为 `/home/your_user/fund_analysis_package/scripts/fetch_fund_data.py`。

4.  **设置 Cron 定时任务**:
    *   在服务器终端运行 `crontab -e` 来编辑定时任务列表。
    *   在文件末尾添加以下一行，并根据您的实际路径进行修改：

    ```cron
    # 每天中国时间凌晨 00:00 运行数据更新脚本
    0 0 * * * /usr/bin/python3 /home/your_user/fund_analysis_package/scripts/fetch_fund_data.py >> /home/your_user/fund_analysis_package/logs/cron.log 2>&1
    ```

    *   **解释**:
        *   `0 0 * * *`: 每天的 0 点 0 分执行。
        *   `>> /home/your_user/fund_analysis_package/logs/cron.log 2>&1`: 将脚本的所有输出（包括错误）都记录到 `cron.log` 文件中，便于日后排查问题。请确保 `logs` 目录存在。

5.  **首次数据抓取**:
    *   在设置好定时任务后，您需要**手动执行一次全量的数据抓取**。这个过程会非常耗时，建议在 `screen` 或 `tmux` 等终端会话中运行，以防 SSH 连接中断。
    ```bash
    cd /home/your_user/fund_analysis_package/scripts
    python3 fetch_fund_data.py
    ```
    *   在此之后，`cron` 任务每天只会进行增量更新。

---

## 2. 前端应用部署

前端应用已经被构建为静态文件，位于 `frontend/dist` 目录中。您需要一个 Web 服务器（如 Nginx 或 Apache）来托管这些文件。

### 使用 Nginx 的部署示例：

1.  **上传前端文件**:
    将 `frontend/dist` 目录下的所有文件，上传到您服务器上用于存放网站文件的目录，例如 `/var/www/fund-app`。

2.  **配置 Nginx**:
    *   在 Nginx 的配置目录（通常是 `/etc/nginx/sites-available/`）中创建一个新的配置文件，例如 `fund-app.conf`。
    *   在该文件中添加以下内容：

    ```nginx
    server {
        listen 80;
        server_name your_domain.com; # 替换为您的域名

        root /var/www/fund-app; # 指向您上传文件的目录
        index index.html;

        location / {
            try_files $uri /index.html;
        }
    }
    ```

    *   **解释**:
        *   `listen 80`: 监听标准的 HTTP 端口。
        *   `server_name`: 您的网站域名。
        *   `root`: 网站文件的根目录。
        *   `location / { try_files ... }`: 这是部署单页面应用（SPA）的关键配置。它确保了无论用户访问哪个路径，最终都会由 `index.html` 来处理，从而让 React Router 能够接管路由。

3.  **启用配置并重启 Nginx**:
    ```bash
    # 创建软链接以启用该配置
    sudo ln -s /etc/nginx/sites-available/fund-app.conf /etc/nginx/sites-enabled/

    # 测试 Nginx 配置是否有语法错误
    sudo nginx -t

    # 重启 Nginx 服务以应用新配置
    sudo systemctl restart nginx
    ```

4.  **完成**:
    现在，您应该可以通过您的域名访问基金分析平台了。
