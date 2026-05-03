#!/usr/bin/env python3
import os
import re

# 获取所有 RP 文件并按数字排序
reports_dir = '/home/krvy/safeoverwiki/source/reports'
rp_files = []

for filename in os.listdir(reports_dir):
    if filename.startswith('RP-') and filename.endswith('.md'):
        # 提取数字
        num_match = re.search(r'RP-(\d+)\.md', filename)
        if num_match:
            num = int(num_match.group(1))
            # 转换为路径格式（去掉 .md）
            path = filename.replace('.md', '')
            rp_files.append((num, path))

# 按数字排序
rp_files.sort(key=lambda x: x[0])

# 生成 tree 列表
tree_items = ['  - emergency-overdose-treatment', '  - survivor-stories']
for num, path in rp_files:
    tree_items.append(f'  - {path}')

tree_section = 'tree:\n' + '\n'.join(tree_items)

# 读取现有的 reports.yml
reports_yml_path = '/home/krvy/safeoverwiki/source/_data/wiki/reports.yml'
with open(reports_yml_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 替换 tree 部分
content = re.sub(r'tree:.*$', tree_section.rstrip(), content, flags=re.MULTILINE | re.DOTALL)

# 写回文件
with open(reports_yml_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'已更新 reports.yml，包含 {len(rp_files)} 个 RP 文件')
print('前 5 个文件:')
for i in range(min(5, len(rp_files))):
    print(f'  - {rp_files[i][1]}')
