#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股场外基金数据获取与处理脚本
"""

import akshare as ak
import pandas as pd
import numpy as np
import json
import os
import time
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

print(f"数据将保存到: {DATA_DIR}")


def classify_fund_sector(fund_name, fund_type):
    """根据基金名称和类型分类板块"""
    name = str(fund_name).upper()
    ftype = str(fund_type)
    
    if any(kw in name for kw in ['科技', '芯片', '半导体', '人工智能', 'AI', '计算机', '电子', '信息', '通信', '5G', '软件', '互联网', '传媒', '新能源', '光伏', '电动车', '新能源汽车']):
        return '科技', '科技成长'
    
    if any(kw in name for kw in ['医药', '医疗', '健康', '生物', '疫苗', '医疗器械', '中药', '创新药']):
        return '医药医疗', '医药健康'
    
    if any(kw in name for kw in ['消费', '食品', '饮料', '白酒', '家电', '汽车', '农业', '畜牧', '养殖', '旅游', '酒店', '零售']):
        return '大消费', '消费升级'
    
    if any(kw in name for kw in ['金融', '银行', '保险', '证券', '地产', '房地产', '基建', '建筑']):
        return '大金融', '金融地产'
    
    if any(kw in name for kw in ['有色', '煤炭', '钢铁', '化工', '石油', '能源', '材料', '资源', '稀土', '锂', '铜', '黄金']):
        return '周期资源', '资源周期'
    
    if any(kw in name for kw in ['军工', '国防', '航天', '航空']):
        return '军工', '国防军工'
    
    if any(kw in name for kw in ['制造', '机械', '装备', '工业', '机器人', '智能制造']):
        return '高端制造', '先进制造'
    
    if '债' in ftype:
        return '固收', '债券策略'
    
    if '指数' in ftype or 'ETF' in ftype:
        if any(kw in name for kw in ['300', '50', '大盘', '蓝筹', '价值']):
            return '大盘指数', '蓝筹价值'
        elif any(kw in name for kw in ['500', '中小', '创业', '成长']):
            return '中小盘', '成长风格'
        elif any(kw in name for kw in ['1000', '2000', '微盘']):
            return '小盘指数', '小盘成长'
        else:
            return '宽基指数', '市场指数'
    
    if '混合' in ftype:
        if any(kw in name for kw in ['价值', '蓝筹', '红利']):
            return '价值风格', '蓝筹价值'
        elif any(kw in name for kw in ['成长', '新兴', '创新']):
            return '成长风格', '科技成长'
        else:
            return '均衡配置', '灵活配置'
    
    if '股票' in ftype:
        return '股票型', '主动股票'
    
    if 'QDII' in ftype:
        return '海外投资', 'QDII策略'
    
    if 'FOF' in ftype:
        return 'FOF', '基金配置'
    
    return '其他', '综合策略'


def generate_fund_size(fund_type, sector):
    """生成模拟基金规模数据"""
    np.random.seed(42)
    fund_type = str(fund_type) if pd.notna(fund_type) else ''
    if '货币' in fund_type:
        return np.random.uniform(50, 500)
    elif '债券' in fund_type:
        return np.random.uniform(10, 200)
    elif '指数' in fund_type:
        return np.random.uniform(5, 100)
    elif '混合' in fund_type:
        return np.random.uniform(5, 150)
    elif '股票' in fund_type:
        return np.random.uniform(2, 80)
    elif 'QDII' in fund_type:
        return np.random.uniform(1, 30)
    elif 'FOF' in fund_type:
        return np.random.uniform(1, 20)
    elif 'REITs' in fund_type or 'Reits' in fund_type:
        return np.random.uniform(0.5, 10)
    else:
        return np.random.uniform(5, 100)


def fetch_fund_list(retries=3, delay=5):
    """获取场外基金列表"""
    print("正在获取场外基金列表...")
    for attempt in range(retries):
        try:
            fund_list = ak.fund_name_em()
            exclude_types = ['货币型-普通货币', '货币型-浮动净值']
            fund_list = fund_list[~fund_list['基金类型'].isin(exclude_types)].copy()
            print(f"获取到 {len(fund_list)} 只基金")
            return fund_list
        except Exception as e:
            print(f"获取基金列表失败 (尝试 {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                print(f"将在 {delay} 秒后重试...")
                time.sleep(delay)
            else:
                print("已达到最大重试次数，获取失败。")
                raise e


def add_sector_classification(fund_list):
    """为基金添加板块分类"""
    print("正在为基金添加板块分类...")
    fund_list['一级板块'] = ''
    fund_list['二级板块'] = ''
    
    for idx, row in fund_list.iterrows():
        s1, s2 = classify_fund_sector(row['基金简称'], row['基金类型'])
        fund_list.at[idx, '一级板块'] = s1
        fund_list.at[idx, '二级板块'] = s2
    
    return fund_list





def fetch_fund_nav_for_new(new_funds_df):
    """为新基金获取完整的历史净值数据"""
    if new_funds_df.empty:
        return {}, []

    print("开始为新基金获取全量历史数据...")
    all_fund_nav = {}
    failed_funds = []
    fund_codes = new_funds_df['基金代码'].tolist()

    for i, fund_code in enumerate(fund_codes):
        try:
            print(f"[{i+1}/{len(fund_codes)}] (新) 获取基金 {fund_code}...", end=' ')
            nav_data = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势", period="3年")
            nav_data['净值日期'] = pd.to_datetime(nav_data['净值日期'])
            all_fund_nav[fund_code] = nav_data
            print(f"({len(nav_data)} 条)")
            time.sleep(0.2)
        except Exception as e:
            print(f"失败")
            failed_funds.append(fund_code)
    
    print(f"\n成功为 {len(all_fund_nav)} 只新基金获取了数据")
    return all_fund_nav, failed_funds

def fetch_fund_nav_for_existing(existing_funds_df, local_fund_nav):
    """为存量基金增量更新净值数据"""
    if existing_funds_df.empty:
        return {}, []

    print("开始为存量基金增量更新数据...")
    updated_fund_nav = {}
    failed_funds = []
    fund_codes = existing_funds_df['基金代码'].tolist()
    today = datetime.now().date()

    for i, fund_code in enumerate(fund_codes):
        if fund_code not in local_fund_nav or not local_fund_nav[fund_code]:
            # 如果本地没有该基金的NAV数据，则全量获取
            try:
                print(f"[{i+1}/{len(fund_codes)}] (补) 获取基金 {fund_code}...", end=' ')
                nav_data = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势", period="3年")
                nav_data['净值日期'] = pd.to_datetime(nav_data['净值日期'])
                updated_fund_nav[fund_code] = nav_data
                print(f"({len(nav_data)} 条)")
            except Exception:
                print("失败")
                failed_funds.append(fund_code)
            time.sleep(0.2)
            continue

        # 检查最新日期
        last_date_str = max([d['净值日期'] for d in local_fund_nav[fund_code]])
        last_date = datetime.strptime(last_date_str, '%Y-%m-%d').date()

        if last_date >= today - timedelta(days=1):
            print(f"[{i+1}/{len(fund_codes)}] (跳过) 基金 {fund_code} 数据已是最新。")
            continue

        try:
            print(f"[{i+1}/{len(fund_codes)}] (增) 更新基金 {fund_code} 从 {last_date}...")
            # 增量获取最新数据
            incremental_nav = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势", period="3年")
            incremental_nav['净值日期'] = pd.to_datetime(incremental_nav['净值日期'])
            
            # 合并新旧数据
            existing_nav_df = pd.DataFrame(local_fund_nav[fund_code])
            existing_nav_df['净值日期'] = pd.to_datetime(existing_nav_df['净值日期'])
            
            # 按您的要求，刷新最近两天的数据
            cutoff_date = last_date - timedelta(days=2)
            existing_nav_df = existing_nav_df[existing_nav_df['净值日期'] < cutoff_date]

            combined_nav = pd.concat([existing_nav_df, incremental_nav]).drop_duplicates(subset=['净值日期'], keep='last')
            combined_nav = combined_nav.sort_values('净值日期').reset_index(drop=True)
            
            updated_fund_nav[fund_code] = combined_nav
            print(f"更新了 {len(incremental_nav)} 条，总计 {len(combined_nav)} 条")
            time.sleep(0.2)
        except Exception as e:
            print(f"失败: {e}")
            failed_funds.append(fund_code)

    print(f"\n成功为 {len(updated_fund_nav)} 只存量基金更新了数据")
    return updated_fund_nav, failed_funds


def calculate_sector_indices(fund_info_df, all_fund_nav):
    """计算板块指数"""
    print("计算板块指数...")
    sector_indices = {}
    
    for sector in fund_info_df['二级板块'].unique():
        sector_funds = fund_info_df[fund_info_df['二级板块'] == sector]['基金代码'].tolist()
        sector_navs = []
        for fund_code in sector_funds:
            if fund_code in all_fund_nav:
                nav_df = all_fund_nav[fund_code].copy()
                nav_df = nav_df.sort_values('净值日期')
                nav_df['净值日期'] = pd.to_datetime(nav_df['净值日期'])
                sector_navs.append(nav_df)
        
        if len(sector_navs) == 0:
            continue
        
        all_dates = set()
        for nav_df in sector_navs:
            all_dates.update(nav_df['净值日期'].tolist())
        all_dates = sorted(list(all_dates))
        
        sector_index = []
        for date in all_dates:
            daily_returns = []
            for nav_df in sector_navs:
                day_data = nav_df[nav_df['净值日期'] == date]
                if len(day_data) > 0:
                    daily_returns.append(day_data['日增长率'].values[0])
            
            if len(daily_returns) > 0:
                avg_return = np.mean(daily_returns)
                sector_index.append({
                    '日期': date.strftime('%Y-%m-%d'),
                    '日收益率': float(avg_return),
                    '参与基金数': len(daily_returns)
                })
        
        sector_indices[sector] = sector_index
    
    print(f"计算了 {len(sector_indices)} 个二级板块指数")
    return sector_indices


def calculate_primary_sector_indices(fund_info_df, all_fund_nav):
    """计算一级板块指数"""
    print("计算一级板块指数...")
    primary_sector_indices = {}
    
    for sector in fund_info_df['一级板块'].unique():
        sector_funds = fund_info_df[fund_info_df['一级板块'] == sector]['基金代码'].tolist()
        sector_navs = []
        for fund_code in sector_funds:
            if fund_code in all_fund_nav:
                nav_df = all_fund_nav[fund_code].copy()
                nav_df = nav_df.sort_values('净值日期')
                nav_df['净值日期'] = pd.to_datetime(nav_df['净值日期'])
                sector_navs.append(nav_df)
        
        if len(sector_navs) == 0:
            continue
        
        all_dates = set()
        for nav_df in sector_navs:
            all_dates.update(nav_df['净值日期'].tolist())
        all_dates = sorted(list(all_dates))
        
        sector_index = []
        for date in all_dates:
            daily_returns = []
            for nav_df in sector_navs:
                day_data = nav_df[nav_df['净值日期'] == date]
                if len(day_data) > 0:
                    daily_returns.append(day_data['日增长率'].values[0])
            
            if len(daily_returns) > 0:
                avg_return = np.mean(daily_returns)
                sector_index.append({
                    '日期': date.strftime('%Y-%m-%d'),
                    '日收益率': float(avg_return),
                    '参与基金数': len(daily_returns)
                })
        
        primary_sector_indices[sector] = sector_index
    
    print(f"计算了 {len(primary_sector_indices)} 个一级板块指数")
    return primary_sector_indices


def calculate_profit_probability(fund_code, nav_data, days_forward=30):
    """计算基金盈利概率"""
    if len(nav_data) < days_forward + 60:
        return None, None
    
    nav_data = nav_data.sort_values('净值日期').reset_index(drop=True)
    nav_data['单位净值'] = pd.to_numeric(nav_data['单位净值'], errors='coerce')
    nav_data = nav_data.dropna(subset=['单位净值'])
    
    if len(nav_data) < days_forward + 60:
        return None, None
    
    profits = []
    for i in range(len(nav_data) - days_forward):
        current_nav = nav_data.iloc[i]['单位净值']
        future_nav = nav_data.iloc[i + days_forward]['单位净值']
        profit = (future_nav - current_nav) / current_nav * 100
        profits.append(profit)
    
    if len(profits) == 0:
        return None, None
    
    profits = np.array(profits)
    profit_count = (profits > 0).sum()
    total_count = len(profits)
    profit_probability = profit_count / total_count * 100
    
    return profit_probability, {
        '盈利概率': round(float(profit_probability), 2),
        '平均收益率': round(float(np.mean(profits)), 2),
        '最大亏损': round(float(np.min(profits)), 2),
        '最大收益': round(float(np.max(profits)), 2),
        '统计样本数': int(total_count)
    }


def calculate_all_profit_probabilities(all_fund_nav):
    """计算所有基金的盈利概率"""
    print("计算所有基金的盈利概率...")
    fund_profit_prob = {}
    
    for fund_code in all_fund_nav.keys():
        prob, stats = calculate_profit_probability(fund_code, all_fund_nav[fund_code])
        if prob is not None:
            fund_profit_prob[fund_code] = stats
    
    print(f"计算了 {len(fund_profit_prob)} 只基金的盈利概率")
    return fund_profit_prob


def calculate_sector_top5(fund_info_df, fund_profit_prob):
    """计算每个板块的Top 5基金"""
    print("计算各板块Top 5基金...")
    
    fund_info_df['盈利概率'] = fund_info_df['基金代码'].map(lambda x: fund_profit_prob.get(x, {}).get('盈利概率', None))
    fund_info_df['平均收益率'] = fund_info_df['基金代码'].map(lambda x: fund_profit_prob.get(x, {}).get('平均收益率', None))
    fund_info_df['基金规模'] = fund_info_df.apply(lambda row: generate_fund_size(row['基金类型'], row['二级板块']), axis=1)
    fund_info_df['基金规模'] = fund_info_df['基金规模'].round(2)
    
    sector_top5 = {'二级板块': {}, '一级板块': {}}
    
    for sector in fund_info_df['二级板块'].unique():
        sector_funds = fund_info_df[fund_info_df['二级板块'] == sector].copy()
        sector_funds = sector_funds.dropna(subset=['盈利概率'])
        sector_funds = sector_funds.sort_values('盈利概率', ascending=False)
        
        top5 = sector_funds.head(5)[['基金代码', '基金简称', '基金类型', '盈利概率', '平均收益率', '基金规模']].to_dict('records')
        for fund in top5:
            fund['盈利概率'] = float(fund['盈利概率'])
            fund['平均收益率'] = float(fund['平均收益率'])
            fund['基金规模'] = float(fund['基金规模'])
        sector_top5['二级板块'][sector] = top5
    
    for sector in fund_info_df['一级板块'].unique():
        sector_funds = fund_info_df[fund_info_df['一级板块'] == sector].copy()
        sector_funds = sector_funds.dropna(subset=['盈利概率'])
        sector_funds = sector_funds.sort_values('盈利概率', ascending=False)
        
        top5 = sector_funds.head(5)[['基金代码', '基金简称', '基金类型', '盈利概率', '平均收益率', '基金规模']].to_dict('records')
        for fund in top5:
            fund['盈利概率'] = float(fund['盈利概率'])
            fund['平均收益率'] = float(fund['平均收益率'])
            fund['基金规模'] = float(fund['基金规模'])
        sector_top5['一级板块'][sector] = top5
    
    print(f"计算了 {len(sector_top5['二级板块'])} 个二级板块和 {len(sector_top5['一级板块'])} 个一级板块的Top 5")
    return sector_top5, fund_info_df


def save_data(fund_info_df, all_fund_nav, sector_indices, primary_sector_indices, sector_top5, fund_profit_prob):
    """保存所有数据到文件"""
    print("保存所有数据...")
    
    fund_info_df.to_csv(os.path.join(DATA_DIR, 'fund_info_with_prob.csv'), index=False, encoding='utf-8-sig')
    print(f"  - fund_info_with_prob.csv")
    
    fund_nav_dict = {}
    for fund_code, nav_df in all_fund_nav.items():
        records = nav_df.copy()
        records['净值日期'] = records['净值日期'].dt.strftime('%Y-%m-%d')
        fund_nav_dict[fund_code] = records.to_dict('records')
    
    with open(os.path.join(DATA_DIR, 'fund_nav_data.json'), 'w', encoding='utf-8') as f:
        json.dump(fund_nav_dict, f, ensure_ascii=False, default=str)
    print(f"  - fund_nav_data.json")
    
    with open(os.path.join(DATA_DIR, 'sector_indices.json'), 'w', encoding='utf-8') as f:
        json.dump(sector_indices, f, ensure_ascii=False)
    print(f"  - sector_indices.json")
    
    with open(os.path.join(DATA_DIR, 'primary_sector_indices.json'), 'w', encoding='utf-8') as f:
        json.dump(primary_sector_indices, f, ensure_ascii=False)
    print(f"  - primary_sector_indices.json")
    
    with open(os.path.join(DATA_DIR, 'sector_top5.json'), 'w', encoding='utf-8') as f:
        json.dump(sector_top5, f, ensure_ascii=False)
    print(f"  - sector_top5.json")
    
    with open(os.path.join(DATA_DIR, 'profit_probability.json'), 'w', encoding='utf-8') as f:
        json.dump(fund_profit_prob, f, ensure_ascii=False)
    print(f"  - profit_probability.json")
    
    print("\n所有数据已保存完成！")


def main():
    """主函数"""
    print("=" * 60)
    print("A股场外基金数据增量更新")
    print("=" * 60)
    print()

    # 尝试加载本地已有的基金数据
    local_fund_info_path = os.path.join(DATA_DIR, 'fund_info_with_prob.csv')
    local_fund_nav_path = os.path.join(DATA_DIR, 'fund_nav_data.json')

    if os.path.exists(local_fund_info_path):
        print("发现本地基金数据，开始增量更新...")
        local_fund_df = pd.read_csv(local_fund_info_path, dtype={'基金代码': str})
        with open(local_fund_nav_path, 'r', encoding='utf-8') as f:
            local_fund_nav = json.load(f)
    else:
        print("未发现本地基金数据，将进行全量初始化...")
        local_fund_df = pd.DataFrame()
        local_fund_nav = {}

    # 获取最新的全量基金列表
    online_fund_list = fetch_fund_list()
    online_fund_list = add_sector_classification(online_fund_list)

    # 识别新基金和存量基金
    if not local_fund_df.empty:
        new_funds_df = online_fund_list[~online_fund_list['基金代码'].isin(local_fund_df['基金代码'])].copy()
        existing_funds_df = online_fund_list[online_fund_list['基金代码'].isin(local_fund_df['基金代码'])].copy()
    else:
        new_funds_df = online_fund_list.copy()
        existing_funds_df = pd.DataFrame()

    print(f"发现 {len(new_funds_df)} 只新基金，{len(existing_funds_df)} 只存量基金。")

    # 处理新基金（全量获取）
    new_fund_nav, failed_new = fetch_fund_nav_for_new(new_funds_df)

    # 处理存量基金（增量更新）
    updated_fund_nav, failed_existing = fetch_fund_nav_for_existing(existing_funds_df, local_fund_nav)

    # 合并数据
    all_fund_nav = {**local_fund_nav, **new_fund_nav, **updated_fund_nav}
    all_fund_info_df = pd.concat([local_fund_df, new_funds_df]).drop_duplicates(subset=['基金代码'], keep='last').reset_index(drop=True)

    # 后续计算和保存
    sector_indices = calculate_sector_indices(all_fund_info_df, all_fund_nav)
    primary_sector_indices = calculate_primary_sector_indices(all_fund_info_df, all_fund_nav)
    fund_profit_prob = calculate_all_profit_probabilities(all_fund_nav)
    sector_top5, final_fund_info_df = calculate_sector_top5(all_fund_info_df, fund_profit_prob)
    final_fund_info_df = final_fund_info_df[final_fund_info_df['基金代码'].isin(all_fund_nav.keys())].reset_index(drop=True)

    save_data(final_fund_info_df, all_fund_nav, sector_indices, primary_sector_indices, sector_top5, fund_profit_prob)

    print()
    print("=" * 60)
    print("数据处理完成！")
    print(f"数据保存在: {DATA_DIR}")
    print("=" * 60)


if __name__ == '__main__':
    main()
