# A股场外基金分析平台 - 部署指南

## 📁 项目结构

```
fund_analysis_package/
├── data/                          # 数据文件
│   ├── fund_info_with_prob.csv    # 基金信息（含盈利概率、规模）
│   ├── fund_nav_data.json         # 基金净值数据
│   ├── sector_indices.json        # 二级板块指数
│   ├── primary_sector_indices.json # 一级板块指数
│   ├── sector_top5.json           # 板块Top5基金
│   └── profit_probability.json    # 盈利概率统计
├── frontend/                      # React前端项目
│   ├── src/
│   │   ├── components/ui/         # UI组件
│   │   ├── sections/              # 页面组件
│   │   ├── hooks/                 # 自定义Hooks
│   │   ├── types/                 # TypeScript类型
│   │   ├── lib/                   # 工具函数
│   │   ├── App.tsx                # 主应用组件
│   │   ├── App.css                # 应用样式
│   │   ├── main.tsx               # 入口文件
│   │   └── index.css              # 全局样式
│   ├── package.json               # 依赖配置
│   ├── tsconfig.json              # TypeScript配置
│   ├── vite.config.ts             # Vite配置
│   ├── tailwind.config.js         # Tailwind配置
│   ├── postcss.config.js          # PostCSS配置
│   └── index.html                 # HTML模板
├── scripts/                       # Python脚本
│   └── fetch_fund_data.py         # 数据获取脚本
└── docs/                          # 文档
    └── DEPLOYMENT_GUIDE.md        # 本文件
```

---

## 🚀 快速部署步骤

### 第一步：环境准备

确保您的系统已安装：

1. **Python 3.8+**
2. **Node.js 18+**
3. **npm** 或 **yarn**

### 第二步：安装Python依赖

```bash
# 安装akshare和其他依赖
pip install akshare pandas numpy
```

### 第三步：获取基金数据

```bash
# 进入scripts目录
cd scripts

# 运行数据获取脚本
python fetch_fund_data.py
```

**脚本功能说明：**
- 获取A股场外基金列表（约25000+只）
- 为基金分类板块（一级板块19个，二级板块17个）
- 获取过去3年的每日净值数据
- 计算板块指数
- 回测计算30天盈利概率
- 生成模拟基金规模数据
- 保存所有数据到 `data/` 目录

**运行时间：** 约10-15分钟（取决于网络速度）

### 第四步：安装前端依赖

```bash
# 进入frontend目录
cd ../frontend

# 安装依赖
npm install
```

### 第五步：复制数据到前端

```bash
# 将数据文件复制到前端的public目录
mkdir -p public/data
cp ../data/*.json public/data/
cp ../data/*.csv public/data/
```

### 第六步：启动开发服务器

```bash
# 启动开发服务器
npm run dev
```

访问 http://localhost:5173 查看网站

### 第七步：构建生产版本

```bash
# 构建生产版本
npm run build

# 构建输出在 dist/ 目录
```

### 第八步：部署到服务器

将 `dist/` 目录下的所有文件部署到您的Web服务器：

```bash
# 示例：复制到Nginx目录
sudo cp -r dist/* /var/www/html/

# 或使用scp上传到远程服务器
scp -r dist/* user@your-server:/var/www/html/
```

---

## 📊 数据更新

### 自动更新（推荐）

前端已内置定时刷新机制：
- 页面加载时自动获取最新数据
- 每5分钟自动刷新数据
- 添加时间戳避免浏览器缓存

### 手动更新数据

```bash
# 重新运行数据获取脚本
cd scripts
python fetch_fund_data.py

# 复制新数据到前端
cp ../data/* ../frontend/public/data/

# 重新构建
cd ../frontend
npm run build
```

---

## 🔧 配置说明

### 修改基金样本数量

编辑 `scripts/fetch_fund_data.py`：

```python
# 第200行左右，修改样本数量
fund_sample = select_sample_funds(fund_list, sample_size=500, funds_per_sector=30)

# 第205行左右，修改获取的最大基金数
all_fund_nav, failed_funds = fetch_fund_nav_data(fund_sample, max_funds=250)
```

### 修改回测天数

编辑 `scripts/fetch_fund_data.py`：

```python
# 第290行左右，修改回测天数
def calculate_profit_probability(fund_code, nav_data, days_forward=30):
```

### 修改自动刷新间隔

编辑 `frontend/src/hooks/useFundData.ts`：

```typescript
// 第85行左右，修改刷新间隔（毫秒）
const interval = setInterval(loadData, 5 * 60 * 1000); // 默认5分钟
```

---

## 🐛 常见问题

### 问题1：Python脚本运行失败

**解决方案：**
```bash
# 确保akshare已安装
pip install --upgrade akshare

# 检查网络连接（需要访问东方财富网）
ping fund.eastmoney.com
```

### 问题2：npm install 失败

**解决方案：**
```bash
# 使用淘宝镜像
npm config set registry https://registry.npmmirror.com

# 或使用yarn
npm install -g yarn
yarn install
```

### 问题3：构建失败

**解决方案：**
```bash
# 删除node_modules重新安装
rm -rf node_modules package-lock.json
npm install

# 确保TypeScript版本兼容
npm install typescript@~5.9.3 --save-dev
```

### 问题4：数据文件找不到

**解决方案：**
```bash
# 确保数据文件在正确位置
ls frontend/public/data/

# 应该包含以下文件：
# - fund_info_with_prob.csv
# - fund_nav_data.json
# - sector_indices.json
# - primary_sector_indices.json
# - sector_top5.json
# - profit_probability.json
```

---

## 📱 部署到不同平台

### 部署到Vercel

```bash
# 安装Vercel CLI
npm install -g vercel

# 部署
cd frontend
vercel --prod
```

### 部署到Netlify

```bash
# 安装Netlify CLI
npm install -g netlify-cli

# 部署
cd frontend
netlify deploy --prod --dir=dist
```

### 部署到GitHub Pages

```bash
# 安装gh-pages
npm install -g gh-pages

# 部署
cd frontend
npm run build
gh-pages -d dist
```

### 使用Docker部署

创建 `Dockerfile`：

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY --from=builder /app/public/data /usr/share/nginx/html/data
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

构建并运行：

```bash
docker build -t fund-analysis .
docker run -p 80:80 fund-analysis
```

---

## 🔐 环境变量

如需配置API代理或其他环境变量，创建 `.env` 文件：

```env
# 开发环境
VITE_API_BASE_URL=http://localhost:3000

# 生产环境
VITE_API_BASE_URL=https://your-api-domain.com
```

---

## 📞 技术支持

如有问题，请检查：
1. 所有依赖是否正确安装
2. 数据文件是否完整
3. 网络连接是否正常
4. 浏览器控制台是否有错误信息

---

## 📄 许可证

本项目仅供学习和研究使用，数据来源于公开渠道，不构成投资建议。
