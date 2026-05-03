#!/usr/bin/env python3
import os
import re
from datetime import datetime

def convert_frontmatter(content, filename):
    # 提取原始 front-matter
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
    if not match:
        return content
    
    frontmatter = match.group(1)
    body = match.group(2)
    
    # 解析字段
    title = re.search(r'title:\s*(.+)', frontmatter)
    date = re.search(r'date:\s*(.+)', frontmatter)
    updated = re.search(r'updated:\s*(.+)', frontmatter)
    
    title_text = title.group(1).strip() if title else filename.replace('.md', '')
    date_text = date.group(1).strip() if date else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    updated_text = updated.group(1).strip() if updated else date_text
    
    # 构建新的 front-matter - 模仿 reports 目录格式
    new_frontmatter = f'''---
layout: page
title: {title_text}
date: {date_text}
updated: {updated_text}
categories: [报告]
tags:
  - 案例分析
  - 用户报告
menu_id: reports
wiki: reports
---
'''
    
    return new_frontmatter + '\n' + body

# 处理所有 RP 文件
rp_dir = '/home/krvy/safeoverwiki/RP'
count = 0
for filename in sorted(os.listdir(rp_dir)):
    if filename.endswith('.md'):
        filepath = os.path.join(rp_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content = convert_frontmatter(content, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        count += 1
        if count <= 5 or count % 20 == 0:  # 只显示前5个和每20个
            print(f'已转换: {filename}')

print(f'\n转换完成！共处理 {count} 个文件')
