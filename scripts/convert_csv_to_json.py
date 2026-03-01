
import pandas as pd
import json
import numpy as np

# 读取CSV文件，并指定编码为GBK
df = pd.read_csv('../data/fund_info_with_prob.csv', encoding='utf-8', on_bad_lines='skip')

# 将 '基金代码' 列转换为字符串，并用 '0' 补齐至6位
df['基金代码'] = df['基金代码'].astype(str).str.zfill(6)

# 将DataFrame中的NaN值替换为None，以便生成有效的JSON
df = df.replace({np.nan: None})

# 将处理后的数据转换为JSON格式
data = df.to_dict(orient='records')

# 将JSON数据写入文件
with open('../frontend/public/data/fund_info.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Successfully converted fund_info_with_prob.csv to fund_info.json")
