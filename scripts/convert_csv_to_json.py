
import pandas as pd
import json
import numpy as np
import os
import time

# --- 智能等待，确保LFS文件已下载 ---
def wait_for_lfs_file(file_path, timeout=60):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline()
                if not first_line.startswith('version https://git-lfs.github.com'):
                    print(f"LFS文件 {os.path.basename(file_path)} 已准备就绪。")
                    return True
        except (IOError, UnicodeDecodeError):
            pass
        print(f"等待LFS文件 {os.path.basename(file_path)} 下载...")
        time.sleep(5)
    print(f"错误：等待LFS文件 {os.path.basename(file_path)} 超时。")
    return False
# -------------------------------------

# 定义文件路径
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
INPUT_CSV = os.path.join(BASE_DIR, 'data', 'fund_info_with_prob.csv')
OUTPUT_JSON = os.path.join(BASE_DIR, 'frontend', 'public', 'data', 'fund_info.json')

print("开始将CSV转换为JSON...")

# 等待LFS文件下载完成
if not wait_for_lfs_file(INPUT_CSV):
    exit(1)

# 读取CSV文件
try:
    df = pd.read_csv(INPUT_CSV, encoding='utf-8', on_bad_lines='skip', dtype={'基金代码': str})
    print(f"成功读取 {len(df)} 条数据从 {os.path.basename(INPUT_CSV)}")
except Exception as e:
    print(f"错误：读取CSV文件失败: {e}")
    exit(1)

# 将 '基金代码' 列转换为字符串，并用 '0' 补齐至6位
df['基金代码'] = df['基金代码'].str.zfill(6)

# 将DataFrame中的NaN值替换为None，以便生成有效的JSON
df = df.replace({np.nan: None})

# 将处理后的数据转换为JSON格式
data = df.to_dict(orient='records')

# 将JSON数据写入文件
with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"成功将数据转换为JSON格式并保存到 {os.path.basename(OUTPUT_JSON)}")
