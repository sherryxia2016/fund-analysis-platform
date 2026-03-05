#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股场外基金数据获取与处理脚本 - 优化版
"""

import akshare as ak
import pandas as pd
import numpy as np
import json
import os
import time
from datetime import datetime, timedelta
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

warnings.filterwarnings('ignore')

# 数据保存路径
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

print(f"数据将保存到: {DATA_DIR}")

# 测试模式配置
TEST_MODE = True  # 设置为 False 进行完整运行
TEST_FUND_COUNT = 3  # 测试模式下的基金数量

@lru_cache(maxsize=1000)
def classify_fund_sector(fund_name, fund_type):
    """根据基金名称和类型分类板块 - 使用缓存加速"""
    name = str(fund_name).upper()
    ftype = str(fund_type)

    # 使用字典映射替代多个if判断，提升性能
    sector_keywords = {
        ('科技', '科技成长'): ['科技', '芯片', '半导体', '人工智能', 'AI', '计算机', '电子', 
                                '信息', '通信', '5G', '软件', '互联网', '传媒', '新能源'],
        ('医药医疗', '医药健康'): ['医药', '医疗', '健康', '生物', '疫苗', '医疗器械', '中药', '创新药'],
        ('大消费', '消费升级'): ['消费', '食品', '饮料', '白酒', '家电', '汽车', '农业', 
                                  '畜牧', '养殖', '旅游', '酒店', '零售'],
        ('大金融', '金融地产'): ['金融', '银行', '保险', '证券', '地产', '房地产', '基建', '建筑'],
        ('周期资源', '资源周期'): ['有色', '煤炭', '钢铁', '化工', '石油', '能源', '材料', 
                                    '资源', '稀土', '锂', '铜', '黄金'],
        ('军工', '国防军工'): ['军工', '国防', '航天', '航空'],
        ('高端制造', '先进制造'): ['制造', '机械', '装备', '工业', '机器人', '智能制造'],
    }
    
    for (sector1, sector2), keywords in sector_keywords.items():
        if any(kw in name for kw in keywords):
            return sector1, sector2

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

def generate_fund_size_vectorized(fund_types, sectors):
    """向量化生成模拟基金规模数据"""
    np.random.seed(42)
    sizes = np.zeros(len(fund_types))
    
    # 使用向量化操作替代循环
    fund_types = fund_types.fillna('').astype(str)
    
    masks = {
        '货币': fund_types.str.contains('货币'),
        '债券': fund_types.str.contains('债券'),
        '指数': fund_types.str.contains('指数'),
        '混合': fund_types.str.contains('混合'),
        '股票': fund_types.str.contains('股票'),
        'QDII': fund_types.str.contains('QDII'),
        'FOF': fund_types.str.contains('FOF'),
        'REITs': fund_types.str.contains('REITs|Reits'),
    }
    
    ranges = {
        '货币': (50, 500),
        '债券': (10, 200),
        '指数': (5, 100),
        '混合': (5, 150),
        '股票': (2, 80),
        'QDII': (1, 30),
        'FOF': (1, 20),
        'REITs': (0.5, 10),
    }
    
    for fund_type, mask in masks.items():
        count = mask.sum()
        if count > 0:
            low, high = ranges[fund_type]
            sizes[mask] = np.random.uniform(low, high, count)
    
    # 处理未匹配的类型
    unmatched = sizes == 0
    if unmatched.sum() > 0:
        sizes[unmatched] = np.random.uniform(5, 100, unmatched.sum())
    
    return sizes

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
    """为基金添加板块分类 - 向量化处理"""
    print("正在为基金添加板块分类...")
    
    # 向量化应用分类函数
    classifications = fund_list.apply(
        lambda row: classify_fund_sector(row['基金简称'], row['基金类型']), 
        axis=1
    )
    
    fund_list['一级板块'] = [c[0] for c in classifications]
    fund_list['二级板块'] = [c[1] for c in classifications]
    
    return fund_list

def fetch_single_fund_nav(fund_code, full_history=True):
    """获取单只基金的净值数据"""
    try:
        period = "3年" if full_history else "1月"
        nav_data = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势", period=period)
        nav_data['净值日期'] = pd.to_datetime(nav_data['净值日期'])
        return fund_code, nav_data, None
    except Exception as e:
        return fund_code, None, str(e)

def check_fund_has_recent_data(fund_code, daily_df):
    """检查基金是否有最新数据"""
    if daily_df is None:
        return True  # 如果无法获取批量数据，默认尝试获取
    
    if fund_code not in daily_df.index:
        return False
    
    row = daily_df.loc[fund_code]
    if isinstance(row, pd.DataFrame):
        row = row.iloc[0]
    
    nav_col = None
    for c in daily_df.columns:
        if '单位净值' in c and '前交易日' not in c:
            nav_col = c
            break
    
    if nav_col is None:
        return True
    
    nav_value = row.get(nav_col)
    return pd.notna(nav_value)

def fetch_fund_nav_for_new(new_funds_df, daily_df=None, max_workers=5):
    """为新基金并行获取完整的历史净值数据"""
    if new_funds_df.empty:
        return {}, []

    print("开始为新基金获取全量历史数据...")
    
    # 过滤掉没有最新数据的基金
    fund_codes = new_funds_df['基金代码'].tolist()
    if daily_df is not None:
        valid_codes = [fc for fc in fund_codes if check_fund_has_recent_data(fc, daily_df)]
        skipped = len(fund_codes) - len(valid_codes)
        if skipped > 0:
            print(f"跳过 {skipped} 只无最新数据的基金")
        fund_codes = valid_codes
    
    all_fund_nav = {}
    failed_funds = []
    
    # 使用线程池并行获取
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_single_fund_nav, fc, True): fc for fc in fund_codes}
        
        for i, future in enumerate(as_completed(futures)):
            fund_code, nav_data, error = future.result()
            if error is None and nav_data is not None and len(nav_data) > 0:
                all_fund_nav[fund_code] = nav_data
                print(f"[{i+1}/{len(fund_codes)}] (新) 获取基金 {fund_code}...({len(nav_data)} 条)")
            else:
                print(f"[{i+1}/{len(fund_codes)}] (新) 获取基金 {fund_code}...失败")
                failed_funds.append(fund_code)
            time.sleep(0.1)  # 控制请求频率

    print(f"\n成功为 {len(all_fund_nav)} 只新基金获取了数据")
    return all_fund_nav, failed_funds

def fetch_batch_daily_nav(retries=3, delay=5):
    """批量获取所有开放式基金的最新一日净值数据"""
    print("正在批量获取所有开放式基金最新净值...")
    for attempt in range(retries):
        try:
            daily_df = ak.fund_open_fund_daily_em()
            daily_df['基金代码'] = daily_df['基金代码'].astype(str)
            daily_df = daily_df.set_index('基金代码')
            print(f"批量获取成功，共 {len(daily_df)} 只基金的最新净值")
            return daily_df
        except Exception as e:
            print(f"批量获取失败 (尝试 {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                print(f"将在 {delay} 秒后重试...")
                time.sleep(delay)
    print("批量获取已达到最大重试次数，返回 None。")
    return None

def fetch_fund_nav_for_existing(existing_funds_df, local_fund_nav, daily_df=None):
    """为存量基金增量更新净值数据 - 优化版"""
    if existing_funds_df.empty:
        return {}, []

    print("开始为存量基金增量更新数据...")
    updated_fund_nav = {}
    failed_funds = []
    fund_codes = existing_funds_df['基金代码'].tolist()
    today = datetime.now().date()

    # 第一步：找出本地缺失NAV历史的基金
    missing_nav_codes = [fc for fc in fund_codes if fc not in local_fund_nav or not local_fund_nav[fc]]
    
    if missing_nav_codes:
        # 过滤掉没有最新数据的基金
        if daily_df is not None:
            valid_codes = [fc for fc in missing_nav_codes if check_fund_has_recent_data(fc, daily_df)]
            skipped = len(missing_nav_codes) - len(valid_codes)
            if skipped > 0:
                print(f"跳过 {skipped} 只无最新数据的存量基金")
            missing_nav_codes = valid_codes
        
        print(f"\n发现 {len(missing_nav_codes)} 只存量基金本地缺少NAV历史，并行获取...")
        
        # 使用线程池并行获取
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(fetch_single_fund_nav, fc, True): fc for fc in missing_nav_codes}
            
            for i, future in enumerate(as_completed(futures)):
                fund_code, nav_data, error = future.result()
                if error is None and nav_data is not None and len(nav_data) > 0:
                    updated_fund_nav[fund_code] = nav_data
                    print(f"[{i+1}/{len(missing_nav_codes)}] (补) 获取基金 {fund_code}...({len(nav_data)} 条)")
                else:
                    print(f"[{i+1}/{len(missing_nav_codes)}] (补) 获取基金 {fund_code}...失败")
                    failed_funds.append(fund_code)
                time.sleep(0.1)

    # 第二步：批量增量更新有本地历史的基金
    codes_with_local = [fc for fc in fund_codes if fc in local_fund_nav and local_fund_nav[fc]]
    
    if not codes_with_local or daily_df is None:
        print(f"\n成功为 {len(updated_fund_nav)} 只存量基金更新了数据")
        return updated_fund_nav, failed_funds

    # 检查本地数据最新日期
    sample_dates = []
    for fc in codes_with_local[:100]:
        last_d = max(d['净值日期'] for d in local_fund_nav[fc])
        sample_dates.append(last_d)
    most_common_last = max(set(sample_dates), key=sample_dates.count)
    last_date = datetime.strptime(most_common_last, '%Y-%m-%d').date()

    if last_date >= today - timedelta(days=1):
        print(f"本地数据最新日期为 {last_date}，已是最新，跳过批量更新。")
        print(f"\n成功为 {len(updated_fund_nav)} 只存量基金更新了数据")
        return updated_fund_nav, failed_funds

    # 向量化处理批量更新
    nav_col = None
    growth_col = None
    for c in daily_df.columns:
        if '单位净值' in c and '前交易日' not in c: nav_col = c
        if '日增长率' in c: growth_col = c
    
    if nav_col is None: nav_col = '单位净值'
    if growth_col is None: growth_col = '日增长率'

    daily_df[nav_col] = pd.to_numeric(daily_df[nav_col], errors='coerce')
    daily_df[growth_col] = pd.to_numeric(daily_df[growth_col], errors='coerce')

    batch_updated = 0
    batch_skipped = 0
    batch_no_data = 0
    nav_date = today.strftime('%Y-%m-%d')
    
    for fund_code in codes_with_local:
        if fund_code not in daily_df.index:
            batch_no_data += 1
            continue
            
        row = daily_df.loc[fund_code]
        if isinstance(row, pd.DataFrame): 
            row = row.iloc[0]
            
        nav_value = row.get(nav_col)
        growth_value = row.get(growth_col)
        
        if pd.isna(nav_value):
            batch_no_data += 1
            continue
            
        existing_records = local_fund_nav[fund_code]
        fund_last_date_str = max(d['净值日期'] for d in existing_records)
        fund_last_date = datetime.strptime(fund_last_date_str, '%Y-%m-%d').date()
        
        if fund_last_date >= today - timedelta(days=1):
            batch_skipped += 1
            continue
            
        existing_nav_df = pd.DataFrame(existing_records)
        existing_nav_df['净值日期'] = pd.to_datetime(existing_nav_df['净值日期'])
        
        new_row = pd.DataFrame([{
            '净值日期': pd.Timestamp(nav_date),
            '单位净值': float(nav_value),
            '日增长率': float(growth_value) if pd.notna(growth_value) else 0.0
        }])
        
        combined = pd.concat([existing_nav_df, new_row]).drop_duplicates(subset=['净值日期'], keep='last')
        combined = combined.sort_values('净值日期').reset_index(drop=True)
        updated_fund_nav[fund_code] = combined
        batch_updated += 1

    print(f"\n批量增量更新结果：更新 {batch_updated} 只，已最新跳过 {batch_skipped} 只，无当日数据 {batch_no_data} 只")
    print(f"成功为 {len(updated_fund_nav)} 只存量基金更新了数据")
    return updated_fund_nav, failed_funds

def calculate_sector_indices_vectorized(fund_info_df, all_fund_nav):
    """计算二级板块指数 - 向量化优化版"""
    print("计算板块指数...")
    sector_indices = {}

    for sector in fund_info_df['二级板块'].unique():
        sector_funds = fund_info_df[fund_info_df['二级板块'] == sector]['基金代码'].tolist()
        
        # 收集所有有效的NAV数据
        valid_navs = []
        for fund_code in sector_funds:
            if fund_code in all_fund_nav:
                nav_df = all_fund_nav[fund_code]
                if nav_df is None or nav_df.empty or '净值日期' not in nav_df.columns:
                    continue
                nav_df = nav_df.copy()
                nav_df['净值日期'] = pd.to_datetime(nav_df['净值日期'])
                nav_df = nav_df.sort_values('净值日期')
                valid_navs.append(nav_df[['净值日期', '日增长率']])
        
        if len(valid_navs) == 0:
            continue
        
        # 合并所有数据并按日期分组计算平均收益率
        combined = pd.concat(valid_navs)
        grouped = combined.groupby('净值日期').agg({
            '日增长率': ['mean', 'count']
        }).reset_index()
        
        grouped.columns = ['日期', '日收益率', '参与基金数']
        grouped['日期'] = grouped['日期'].dt.strftime('%Y-%m-%d')
        
        sector_indices[sector] = grouped.to_dict('records')

    print(f"计算了 {len(sector_indices)} 个二级板块指数")
    return sector_indices

def calculate_primary_sector_indices_vectorized(fund_info_df, all_fund_nav):
    """计算一级板块指数 - 向量化优化版"""
    print("计算一级板块指数...")
    primary_sector_indices = {}

    for sector in fund_info_df['一级板块'].unique():
        sector_funds = fund_info_df[fund_info_df['一级板块'] == sector]['基金代码'].tolist()
        
        valid_navs = []
        for fund_code in sector_funds:
            if fund_code in all_fund_nav:
                nav_df = all_fund_nav[fund_code]
                if nav_df is None or nav_df.empty or '净值日期' not in nav_df.columns:
                    continue
                nav_df = nav_df.copy()
                nav_df['净值日期'] = pd.to_datetime(nav_df['净值日期'])
                nav_df = nav_df.sort_values('净值日期')
                valid_navs.append(nav_df[['净值日期', '日增长率']])

        if len(valid_navs) == 0:
            continue

        combined = pd.concat(valid_navs)
        grouped = combined.groupby('净值日期').agg({
            '日增长率': ['mean', 'count']
        }).reset_index()
        
        grouped.columns = ['日期', '日收益率', '参与基金数']
        grouped['日期'] = grouped['日期'].dt.strftime('%Y-%m-%d')
        
        primary_sector_indices[sector] = grouped.to_dict('records')

    print(f"计算了 {len(primary_sector_indices)} 个一级板块指数")
    return primary_sector_indices

def calculate_profit_probability_vectorized(nav_data, days_forward=30):
    """计算基金盈利概率 - 向量化版本"""
    if len(nav_data) < days_forward + 60:
        return None, None

    nav_data = nav_data.sort_values('净值日期').reset_index(drop=True)
    nav_data['单位净值'] = pd.to_numeric(nav_data['单位净值'], errors='coerce')
    nav_data = nav_data.dropna(subset=['单位净值'])

    if len(nav_data) < days_forward + 60:
        return None, None

    # 向量化计算收益率
    navs = nav_data['单位净值'].values
    current_navs = navs[:-days_forward]
    future_navs = navs[days_forward:]
    
    profits = (future_navs - current_navs) / current_navs * 100
    
    if len(profits) == 0:
        return None, None

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

def calculate_all_profit_probabilities(all_fund_nav, max_workers=10):
    """并行计算所有基金的盈利概率"""
    print("计算所有基金的盈利概率...")
    fund_profit_prob = {}

    def calc_single_prob(fund_code):
        prob, stats = calculate_profit_probability_vectorized(all_fund_nav[fund_code])
        return fund_code, prob, stats

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(calc_single_prob, fc): fc for fc in all_fund_nav.keys()}
        
        for future in as_completed(futures):
            fund_code, prob, stats = future.result()
            if prob is not None:
                fund_profit_prob[fund_code] = stats

    print(f"计算了 {len(fund_profit_prob)} 只基金的盈利概率")
    return fund_profit_prob

def calculate_sector_top5(fund_info_df, fund_profit_prob):
    """计算每个板块的Top 5基金 - 向量化优化"""
    print("计算各板块Top 5基金...")

    # 向量化添加盈利概率和规模
    fund_info_df['盈利概率'] = fund_info_df['基金代码'].map(
        lambda x: fund_profit_prob.get(x, {}).get('盈利概率', None)
    )
    fund_info_df['平均收益率'] = fund_info_df['基金代码'].map(
        lambda x: fund_profit_prob.get(x, {}).get('平均收益率', None)
    )
    
    # 向量化生成基金规模
    fund_info_df['基金规模'] = generate_fund_size_vectorized(
        fund_info_df['基金类型'], 
        fund_info_df['二级板块']
    ).round(2)

    sector_top5 = {'二级板块': {}, '一级板块': {}}

    # 二级板块Top5
    for sector in fund_info_df['二级板块'].unique():
        sector_funds = fund_info_df[fund_info_df['二级板块'] == sector].copy()
        sector_funds = sector_funds.dropna(subset=['盈利概率'])
        sector_funds = sector_funds.sort_values('盈利概率', ascending=False)
        
        top5 = sector_funds.head(5)[['基金代码', '基金简称', '基金类型', '盈利概率', '平均收益率', '基金规模']].to_dict('records')
        sector_top5['二级板块'][sector] = top5

    # 一级板块Top5
    for sector in fund_info_df['一级板块'].unique():
        sector_funds = fund_info_df[fund_info_df['一级板块'] == sector].copy()
        sector_funds = sector_funds.dropna(subset=['盈利概率'])
        sector_funds = sector_funds.sort_values('盈利概率', ascending=False)

        top5 = sector_funds.head(5)[['基金代码', '基金简称', '基金类型', '盈利概率', '平均收益率', '基金规模']].to_dict('records')
        sector_top5['一级板块'][sector] = top5

    print(f"计算了 {len(sector_top5['二级板块'])} 个二级板块和 {len(sector_top5['一级板块'])} 个一级板块的Top 5")
    return sector_top5, fund_info_df

def save_data(fund_info_df, all_fund_nav, sector_indices, primary_sector_indices, sector_top5, fund_profit_prob):
    """保存所有数据到文件"""
    print("保存所有数据...")

    fund_info_df.to_csv(os.path.join(DATA_DIR, 'fund_info_with_prob.csv'), index=False, encoding='utf-8-sig')
    print(" - fund_info_with_prob.csv")

    fund_nav_dict = {}
    for fund_code, nav_df in all_fund_nav.items():
        records = nav_df.copy()
        if records is None or records.empty or '净值日期' not in records.columns:
            continue
        records['净值日期'] = records['净值日期'].dt.strftime('%Y-%m-%d')
        fund_nav_dict[fund_code] = records.to_dict('records')

    with open(os.path.join(DATA_DIR, 'fund_nav_data.json'), 'w', encoding='utf-8') as f:
        json.dump(fund_nav_dict, f, ensure_ascii=False, default=str)
    print(" - fund_nav_data.json")

    with open(os.path.join(DATA_DIR, 'sector_indices.json'), 'w', encoding='utf-8') as f:
        json.dump(sector_indices, f, ensure_ascii=False)
    print(" - sector_indices.json")

    with open(os.path.join(DATA_DIR, 'primary_sector_indices.json'), 'w', encoding='utf-8') as f:
        json.dump(primary_sector_indices, f, ensure_ascii=False)
    print(" - primary_sector_indices.json")

    with open(os.path.join(DATA_DIR, 'sector_top5.json'), 'w', encoding='utf-8') as f:
        json.dump(sector_top5, f, ensure_ascii=False)
    print(" - sector_top5.json")

    with open(os.path.join(DATA_DIR, 'profit_probability.json'), 'w', encoding='utf-8') as f:
        json.dump(fund_profit_prob, f, ensure_ascii=False)
    print(" - profit_probability.json")

    print("\n所有数据已保存完成!")

def main():
    """主函数"""
    print("=" * 60)
    print("A股场外基金数据增量更新 - 优化版")
    print("=" * 60)
    print()

    # 加载本地已有数据
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

    # 获取最新基金列表
    if TEST_MODE:
        print(f"\n{'='*60}")
        print(f"运行于测试模式 - 仅处理 {TEST_FUND_COUNT} 只基金")
        print(f"{'='*60}\n")
    
    online_fund_list = fetch_fund_list()
    
    # 先获取批量日净值数据，用于筛选有效基金
    daily_df = fetch_batch_daily_nav()
    
    if TEST_MODE:
        # 测试模式：筛选出有最新数据的基金，取前N只
        if daily_df is not None:
            valid_codes = []
            for code in online_fund_list['基金代码']:
                if check_fund_has_recent_data(code, daily_df):
                    valid_codes.append(code)
                if len(valid_codes) >= TEST_FUND_COUNT:
                    break
            online_fund_list = online_fund_list[online_fund_list['基金代码'].isin(valid_codes)].copy()
            print(f"筛选出 {len(online_fund_list)} 只有最新数据的基金进行测试")
        else:
            online_fund_list = online_fund_list.head(TEST_FUND_COUNT).copy()
            print(f"无法获取批量数据，使用前 {TEST_FUND_COUNT} 只基金进行测试")
    
    online_fund_list = add_sector_classification(online_fund_list)

    # 识别新基金和存量基金
    if not local_fund_df.empty:
        new_funds_df = online_fund_list[~online_fund_list['基金代码'].isin(local_fund_df['基金代码'])].copy()
        existing_funds_df = online_fund_list[online_fund_list['基金代码'].isin(local_fund_df['基金代码'])].copy()
    else:
        new_funds_df = online_fund_list.copy()
        existing_funds_df = pd.DataFrame()

    print(f"发现 {len(new_funds_df)} 只新基金，{len(existing_funds_df)} 只存量基金。")

    # 处理新基金 (全量获取)
    new_fund_nav, failed_new = fetch_fund_nav_for_new(new_funds_df, daily_df)

    # 处理存量基金 (增量更新)
    updated_fund_nav, failed_existing = fetch_fund_nav_for_existing(existing_funds_df, local_fund_nav, daily_df)

    # 合并数据
    all_fund_nav_df = {}
    for fc, records in local_fund_nav.items():
        if isinstance(records, list):
            df = pd.DataFrame(records)
            if not df.empty and '净值日期' in df.columns:
                df['净值日期'] = pd.to_datetime(df['净值日期'])
            all_fund_nav_df[fc] = df
        else:
            all_fund_nav_df[fc] = records

    all_fund_nav = {**all_fund_nav_df, **new_fund_nav, **updated_fund_nav}
    all_fund_info_df = pd.concat([local_fund_df, new_funds_df]).drop_duplicates(subset=['基金代码'], keep='last').reset_index(drop=True)

    # 后续计算
    sector_indices = calculate_sector_indices_vectorized(all_fund_info_df, all_fund_nav)
    primary_sector_indices = calculate_primary_sector_indices_vectorized(all_fund_info_df, all_fund_nav)
    fund_profit_prob = calculate_all_profit_probabilities(all_fund_nav)
    sector_top5, final_fund_info_df = calculate_sector_top5(all_fund_info_df, fund_profit_prob)
    
    # 过滤掉没有NAV数据的无效基金信息
    final_fund_info_df = final_fund_info_df[final_fund_info_df['基金代码'].isin(all_fund_nav.keys())].reset_index(drop=True)

    save_data(final_fund_info_df, all_fund_nav, sector_indices, primary_sector_indices, sector_top5, fund_profit_prob)

    print()
    print("=" * 60)
    print("数据处理完成!")
    print(f"数据保存在: {DATA_DIR}")
    if TEST_MODE:
        print(f"提示: 当前为测试模式，如需完整运行请设置 TEST_MODE = False")
    print("=" * 60)

if __name__ == '__main__':
    main()