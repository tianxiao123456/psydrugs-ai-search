#!/usr/bin/env python3
import os
import re

def add_order_to_frontmatter(content, order_num):
    # 提取原始 front-matter
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
    if not match:
        return content
    
    frontmatter = match.group(1)
    body = match.group(2)
    
    # 如果已经有 order 字段，先移除
    frontmatter = re.sub(r'order:.*\n', '', frontmatter)
    
    # 在 title 后面添加 order 字段
    lines = frontmatter.split('\n')
    new_lines = []
    for line in lines:
        new_lines.append(line)
        if line.startswith('title:'):
            new_lines.append(f'order: {order_num}')
    
    new_frontmatter = '\n'.join(new_lines)
    
    return f'---\n{new_frontmatter}\n---\n{body}'

# 处理所有 RP 文件
reports_dir = '/home/krvy/safeoverwiki/source/reports'
count = 0

# 获取所有 RP 文件并按数字排序
rp_files = []
for filename in os.listdir(reports_dir):
    if filename.startswith('RP-') and filename.endswith('.md'):
        # 提取数字
        num_match = re.search(r'RP-(\d+)\.md', filename)
        if num_match:
            num = int(num_match.group(1))
            rp_files.append((num, filename))

# 按数字排序
rp_files.sort(key=lambda x: x[0])

# 处理文件
for num, filename in rp_files:
    filepath = os.path.join(reports_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = add_order_to_frontmatter(content, num)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    count += 1
    if count <= 5 or count % 20 == 0:
        print(f'已处理: {filename} (order: {num})')

print(f'\n完成！共处理 {count} 个文件')
