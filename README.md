# A股场外基金分析平台

基于React + TypeScript + Python的A股场外基金分析平台，提供基金净值查询、板块指数、盈利概率回测等功能。

## ✨ 功能特性

- 📊 **基金列表**：展示234只场外基金的详细信息
- 🏷️ **板块分类**：一级板块19个，二级板块17个
- 📈 **板块指数**：基于基金净值计算的板块收益指数
- 🎯 **盈利概率**：基于3年历史数据回测的30天盈利概率
- 💰 **基金规模**：显示和筛选基金规模
- 📅 **时间范围**：支持1月/3月/6月/1年/1.5年/2年/3年/全部历史筛选
- 🔄 **自动刷新**：每5分钟自动更新数据

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Node.js 18+

### 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装Node依赖
cd frontend
npm install
```

### 获取数据

```bash
cd scripts
python fetch_fund_data.py
```

### 启动开发服务器

```bash
cd frontend
npm run dev
```

访问 http://localhost:5173

### 构建生产版本

```bash
npm run build
```

## 📁 项目结构

```
├── data/              # 数据文件
├── frontend/          # React前端
├── scripts/           # Python数据脚本
└── docs/              # 文档
```

## 📖 详细文档

查看 [DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) 获取完整部署指南。

## ⚠️ 免责声明

数据仅供参考，不构成投资建议。投资有风险，入市需谨慎。
