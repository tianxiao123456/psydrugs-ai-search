#!/usr/bin/env python3
"""为 others 目录中的新文件添加 YAML front matter 并删除来源"""
import os
import re
from datetime import datetime

def fix_file(filepath):
    """为文件添加 YAML front matter 并删除来源"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 跳过已有 front matter 的文件
    if content.startswith('---'):
        return False
    
    # 提取标题
    match = re.search(r'^# (.+)$', content, re.MULTILINE)
    title = match.group(1).strip() if match else "Unknown"
    
    # 删除来源行和 --- 分隔线
    lines = content.split('\n')
    new_lines = []
    skip_next_hr = False
    
    for i, line in enumerate(lines):
        # 跳过"**来源**: ..."这一行
        if line.startswith('**来源**') or line.startswith('**来源'):
            skip_next_hr = True
            continue
        
        # 跳过紧随其后的"---"分隔线和空行
        if skip_next_hr and line.strip() == '---':
            skip_next_hr = False
            # 也跳过后面的空行
            continue
        
        new_lines.append(line)
    
    content_without_source = '\n'.join(new_lines)
    
    # 生成 front matter
    frontmatter = f"""---
layout: page
title: {title}
date: {datetime.now().isoformat()}
updated: {datetime.now().isoformat()}
categories:
  - "[药物]"
tags: []
wiki: drugs
article:
  type: story
---

"""
    
    # 写入文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(frontmatter + content_without_source)
    
    return True

def main():
    base_dir = '/home/krvy/psydrugs.org/source/drugs/others'
    files_to_fix = [
        '1,4-丁二醇.md',
        '3-羟基芬纳西泮.md',
        '一氧化二氮.md',
        '亚硝酸叔丁酯.md',
        '依托咪酯.md',
        '双氢麦角毒碱.md',
        '噻加宾.md',
        '大麻二酚.md',
        '巴氯芬.md',
        '甲溴喹酮.md',
        '维加巴特林.md',
        '肉豆蔻醚.md',
        '苏糖酸镁.md',
        '茶氨酸.md',
        '鸦片.md',
        '麦角酸二乙酰胺.md',
    ]
    
    count = 0
    for filename in files_to_fix:
        filepath = os.path.join(base_dir, filename)
        if os.path.exists(filepath):
            if fix_file(filepath):
                print(f"✓ 已处理: {filename}")
                count += 1
    
    print(f"\n处理完成！共处理 {count} 个文件")

if __name__ == '__main__':
    main()
