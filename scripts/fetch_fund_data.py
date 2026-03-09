#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A股场外基金数据获取与处理脚本 - 可续传分批处理版
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
import requests
from vercel_blob import put

warnings.filterwarnings('ignore')

# --- 配置 ---
# Vercel Blob 配置
BLOB_BASE_URL = "https://pfund-analysis-platform.vercel.app/"
# 本地数据保存路径
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
os.makedirs(DATA_DIR, exist_ok=True)
# 文件名
PROGRESS_FILENAME = "progress.json"
FUND_INFO_FILENAME = "fund_info.json"
# 批处理大小
BATCH_SIZE = 100

print(f"数据将保存到: {DATA_DIR}")
print(f"批处理大小: {BATCH_SIZE}")

# --- Vercel Blob 辅助函数 ---

def download_from_blob(filename):
    """从 Vercel Blob 下载文件"""
    url = f"{BLOB_BASE_URL}{filename}"
    print(f"正在从 {url} 下载...")
    try:
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            print(f"下载成功: {filename}")
            return response.json()
        elif response.status_code == 404:
            print(f"文件未在 Blob 中找到: {filename} (将创建新的)")
            return None
        else:
            print(f"下载失败: {filename}, 状态码: {response.status_code}, 响应: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"下载时发生网络错误: {e}")
        return None

def upload_to_blob(local_filepath, blob_filename):
    """使用 vercel-blob Python 库上传文件"""
    print(f"正在上传 {local_filepath} 到 Vercel Blob as {blob_filename}...")
    try:
        with open(local_filepath, 'rb') as f:
            blob_result = put(blob_filename, f, options={'access': 'public'})
            print(f"上传成功: {blob_result['url']}")
    except Exception as e:
        print(f"上传失败: {e}")

# --- 数据处理函数 (与之前版本基本相同) ---

@lru_cache(maxsize=1000)
def classify_fund_sector(fund_name, fund_type):
    """根据基金名称和类型分类板块 - 使用缓存加速"""
    name = str(fund_name).upper()
    ftype = str(fund_type)
    sector_keywords = {
        ('科技', '科技成长'): ['科技', '芯片', '半导体', '人工智能', 'AI', '计算机', '电子', '信息', '通信', '5G', '软件', '互联网', '传媒', '新能源'],
        ('医药医疗', '医药健康'): ['医药', '医疗', '健康', '生物', '疫苗', '医疗器械', '中药', '创新药'],
        ('大消费', '消费升级'): ['消费', '食品', '饮料', '白酒', '家电', '汽车', '农业', '畜牧', '养殖', '旅游', '酒店', '零售'],
        ('大金融', '金融地产'): ['金融', '银行', '保险', '证券', '地产', '房地产', '基建', '建筑'],
        ('周期资源', '资源周期'): ['有色', '煤炭', '钢铁', '化工', '石油', '能源', '材料', '资源', '稀土', '锂', '铜', '黄金'],
        ('军工', '国防军工'): ['军工', '国防', '航天', '航空'],
        ('高端制造', '先进制造'): ['制造', '机械', '装备', '工业', '机器人', '智能制造'],
    }
    for (sector1, sector2), keywords in sector_keywords.items():
        if any(kw in name for kw in keywords):
            return sector1, sector2
    if '债' in ftype: return '固收', '债券策略'
    if '指数' in ftype or 'ETF' in ftype:
        if any(kw in name for kw in ['300', '50', '大盘', '蓝筹', '价值']): return '大盘指数', '蓝筹价值'
        elif any(kw in name for kw in ['500', '中小', '创业', '成长']): return '中小盘', '成长风格'
        elif any(kw in name for kw in ['1000', '2000', '微盘']): return '小盘指数', '小盘成长'
        else: return '宽基指数', '市场指数'
    if '混合' in ftype:
        if any(kw in name for kw in ['价值', '蓝筹', '红利']): return '价值风格', '蓝筹价值'
        elif any(kw in name for kw in ['成长', '新兴', '创新']): return '成长风格', '科技成长'
        else: return '均衡配置', '灵活配置'
    if '股票' in ftype: return '股票型', '主动股票'
    if 'QDII' in ftype: return '海外投资', 'QDII策略'
    if 'FOF' in ftype: return 'FOF', '基金配置'
    return '其他', '综合策略'

def generate_fund_size_vectorized(fund_types, sectors):
    np.random.seed(42)
    sizes = np.zeros(len(fund_types))
    fund_types = fund_types.fillna('').astype(str)
    masks = {'货币': fund_types.str.contains('货币'), '债券': fund_types.str.contains('债券'), '指数': fund_types.str.contains('指数'), '混合': fund_types.str.contains('混合'), '股票': fund_types.str.contains('股票'), 'QDII': fund_types.str.contains('QDII'), 'FOF': fund_types.str.contains('FOF'), 'REITs': fund_types.str.contains('REITs|Reits')}
    ranges = {'货币': (50, 500), '债券': (10, 200), '指数': (5, 100), '混合': (5, 150), '股票': (2, 80), 'QDII': (1, 30), 'FOF': (1, 20), 'REITs': (0.5, 10)}
    for fund_type, mask in masks.items():
        count = mask.sum()
        if count > 0:
            low, high = ranges[fund_type]
            sizes[mask] = np.random.uniform(low, high, count)
    unmatched = sizes == 0
    if unmatched.sum() > 0: sizes[unmatched] = np.random.uniform(5, 100, unmatched.sum())
    return sizes

def fetch_fund_list(retries=3, delay=5):
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
                time.sleep(delay)
            else:
                raise e

def add_sector_classification(fund_list):
    print("正在为基金添加板块分类...")
    classifications = fund_list.apply(lambda row: classify_fund_sector(row['基金简称'], row['基金类型']), axis=1)
    fund_list['一级板块'] = [c[0] for c in classifications]
    fund_list['二级板块'] = [c[1] for c in classifications]
    return fund_list

def fetch_single_fund_nav(fund_code):
    try:
        nav_data = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势", period="3年")
        nav_data['净值日期'] = pd.to_datetime(nav_data['净值日期'])
        return fund_code, nav_data, None
    except Exception as e:
        return fund_code, None, str(e)

def fetch_fund_nav_batch(fund_codes, max_workers=5):
    if not fund_codes:
        return {}, []
    print(f"开始为 {len(fund_codes)} 只基金获取历史数据...")
    all_fund_nav = {}
    failed_funds = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_single_fund_nav, fc): fc for fc in fund_codes}
        for i, future in enumerate(as_completed(futures)):
            fund_code, nav_data, error = future.result()
            if error is None and nav_data is not None and not nav_data.empty:
                all_fund_nav[fund_code] = nav_data
                print(f"  [{i+1}/{len(fund_codes)}] ✔ 获取 {fund_code} 成功 ({len(nav_data)} 条)")
            else:
                failed_funds.append(fund_code)
                print(f"  [{i+1}/{len(fund_codes)}] ✖ 获取 {fund_code} 失败: {error}")
            time.sleep(0.1) # 控制请求频率
    print(f"本批次成功获取 {len(all_fund_nav)} 只基金的数据。")
    return all_fund_nav, failed_funds

def calculate_profit_probability_vectorized(nav_data, days_forward=30):
    if nav_data is None or len(nav_data) < days_forward + 60: return None
    nav_data = nav_data.sort_values('净值日期').reset_index(drop=True)
    nav_data['单位净值'] = pd.to_numeric(nav_data['单位净值'], errors='coerce')
    nav_data = nav_data.dropna(subset=['单位净值'])
    if len(nav_data) < days_forward + 60: return None
    navs = nav_data['单位净值'].values
    profits = (navs[days_forward:] - navs[:-days_forward]) / navs[:-days_forward] * 100
    if len(profits) == 0: return None
    return {
        '盈利概率': round(float((profits > 0).sum() / len(profits) * 100), 2),
        '平均收益率': round(float(np.mean(profits)), 2),
        '最大亏损': round(float(np.min(profits)), 2),
        '最大收益': round(float(np.max(profits)), 2),
        '统计样本数': int(len(profits))
    }

def process_fund_batch(fund_info_batch_df, all_fund_nav):
    """处理单个批次的基金数据（计算指标等）"""
    print("计算盈利概率...")
    fund_profit_prob = {fc: calculate_profit_probability_vectorized(nav_df) for fc, nav_df in all_fund_nav.items()}
    fund_profit_prob = {k: v for k, v in fund_profit_prob.items() if v is not None}

    print("添加计算指标到基金信息...")
    fund_info_batch_df['盈利概率'] = fund_info_batch_df['基金代码'].map(lambda x: fund_profit_prob.get(x, {}).get('盈利概率'))
    fund_info_batch_df['平均收益率'] = fund_info_batch_df['基金代码'].map(lambda x: fund_profit_prob.get(x, {}).get('平均收益率'))
    fund_info_batch_df['基金规模'] = generate_fund_size_vectorized(fund_info_batch_df['基金类型'], fund_info_batch_df['二级板块']).round(2)
    
    # 添加完整的盈利概率统计数据
    fund_info_batch_df['盈利统计'] = fund_info_batch_df['基金代码'].map(fund_profit_prob)

    return fund_info_batch_df

def clean_for_json(df):
    """清理DataFrame以便序列化为JSON，处理NaN和NaT"""
    # 创建一个副本以避免SettingWithCopyWarning
    df_copy = df.copy()
    # 将 NaN 替换为 None
    df_copy = df_copy.replace({np.nan: None})
    # 转换所有列为合适类型
    for col in df_copy.columns:
        if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
            df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%d %H:%M:%S').replace({pd.NaT: None})
        elif pd.api.types.is_integer_dtype(df_copy[col]):
            # 如果整数列中有None，需要转换为浮点数
            if df_copy[col].isnull().any():
                df_copy[col] = df_copy[col].astype(float).replace({np.nan: None})
    return df_copy

# --- 主逻辑 ---

def main():
    """主函数：分批处理、可续传"""
    print("=" * 60)
    print("A股场外基金数据 - 分批处理与上传")
    print("=" * 60)

    # 1. 加载进度和现有数据
    print("\n--- 步骤 1: 加载进度和云端数据 ---")
    progress = download_from_blob(PROGRESS_FILENAME)
    if progress is None:
        progress = {'processed_funds': [], 'all_fund_codes': []}

    fund_info_blob = download_from_blob(FUND_INFO_FILENAME)
    if fund_info_blob:
        # 从 list of dicts 创建 DataFrame
        existing_fund_info_df = pd.DataFrame(fund_info_blob)
        print(f"从云端加载了 {len(existing_fund_info_df)} 条基金信息。")
    else:
        existing_fund_info_df = pd.DataFrame()
        print("未在云端发现基金信息，将全新创建。")

    # 2. 获取全量基金列表
    print("\n--- 步骤 2: 获取最新全量基金列表 ---")
    try:
        online_fund_list = fetch_fund_list()
        online_fund_list = add_sector_classification(online_fund_list)
        all_fund_codes = online_fund_list['基金代码'].tolist()
        progress['all_fund_codes'] = all_fund_codes
    except Exception as e:
        print(f"获取在线基金列表失败: {e}。将使用上次的列表（如果存在）。")
        all_fund_codes = progress.get('all_fund_codes', [])
        if not all_fund_codes:
            print("错误：无法获取新的基金列表，也无历史列表。脚本终止。")
            return

    # 3. 确定待处理的基金
    processed_codes = set(progress.get('processed_funds', []))
    codes_to_process = [code for code in all_fund_codes if code not in processed_codes]

    if not codes_to_process:
        print("\n🎉 所有基金均已处理完毕！")
        # 可以在这里加入一个逻辑，强制刷新超过一定时间的数据
        return

    print(f"总计: {len(all_fund_codes)} | 已处理: {len(processed_codes)} | 待处理: {len(codes_to_process)}")

    # 4. 分批处理
    batch_number = 0
    while True:
        batch_number += 1
        print(f"\n--- 批次 {batch_number} ---")
        
        # 获取当前批次的基金代码
        current_batch_codes = codes_to_process[:BATCH_SIZE]
        if not current_batch_codes:
            print("所有剩余基金已处理完毕。")
            break

        print(f"本批处理 {len(current_batch_codes)} 只基金...")

        # a. 获取NAV数据
        fund_nav_batch, failed_codes = fetch_fund_nav_batch(current_batch_codes)
        
        # b. 从全量列表中筛选出本批次的基金信息
        batch_info_df = online_fund_list[online_fund_list['基金代码'].isin(fund_nav_batch.keys())].copy()

        # c. 计算指标
        if not batch_info_df.empty:
            processed_batch_df = process_fund_batch(batch_info_df, fund_nav_batch)
            
            # d. 合并数据
            if not existing_fund_info_df.empty:
                # 使用 pd.concat 合并，并移除重复项，保留最新的
                combined_df = pd.concat([existing_fund_info_df, processed_batch_df]).drop_duplicates(subset=['基金代码'], keep='last')
            else:
                combined_df = processed_batch_df
            
            existing_fund_info_df = combined_df.reset_index(drop=True)
            print(f"合并后共有 {len(existing_fund_info_df)} 条基金信息。")

        # e. 更新进度
        processed_in_this_batch = list(fund_nav_batch.keys()) + failed_codes
        progress['processed_funds'].extend(processed_in_this_batch)
        # 去重以防万一
        progress['processed_funds'] = sorted(list(set(progress['processed_funds'])))
        
        print(f"本批成功 {len(fund_nav_batch.keys())}, 失败 {len(failed_codes)}")
        print(f"总进度: {len(progress['processed_funds'])} / {len(all_fund_codes)}")

        # f. 保存并上传
        print("正在保存并上传更新...")
        
        # 清理数据以便JSON序列化
        final_df_cleaned = clean_for_json(existing_fund_info_df)
        
        # 保存 fund_info.json
        local_fund_info_path = os.path.join(DATA_DIR, FUND_INFO_FILENAME)
        final_df_cleaned.to_json(local_fund_info_path, orient='records', force_ascii=False, indent=4)
        upload_to_blob(local_fund_info_path, FUND_INFO_FILENAME)

        # 保存 progress.json
        local_progress_path = os.path.join(DATA_DIR, PROGRESS_FILENAME)
        with open(local_progress_path, 'w', encoding='utf-8') as f:
            json.dump(progress, f, indent=4)
        # 再次打开以二进制模式读取并上传
        upload_to_blob(local_progress_path, PROGRESS_FILENAME)

        # 更新待处理列表
        codes_to_process = codes_to_process[len(current_batch_codes):]
        
        print(f"批次 {batch_number} 完成。")
        
        # 在CI环境中，通常我们只希望运行一个批次然后退出
        # 如果设置了环境变量 CI=true，则只运行一个批次
        if os.environ.get('CI') == 'true':
            print("在CI环境中，完成一个批次后退出。")
            break

    print("\n" + "=" * 60)
    print("所有批次处理完成!")
    print("=" * 60)

if __name__ == '__main__':
    main()
