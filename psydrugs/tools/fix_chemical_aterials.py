#!/usr/bin/env python3
"""删除 chemical_aterials 文件夹中的来源行"""
import os
import re

def fix_file(filepath):
    """删除文件开头的来源信息"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 找到需要删除的行
    new_lines = []
    skip_next_hr = False
    
    for i, line in enumerate(lines):
        # 跳过"**来源**: ..."这一行
        if line.startswith('**来源**:') or line.startswith('**来源**：'):
            skip_next_hr = True
            continue
        
        # 跳过紧随其后的"---"分隔线
        if skip_next_hr and line.strip() == '---':
            skip_next_hr = False
            # 也跳过后面的空行
            continue
        
        new_lines.append(line)
    
    # 写回文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"✓ 已处理: {os.path.basename(filepath)}")

def main():
    base_dir = '/home/krvy/psydrugs.org/source/drugs/chemical_aterials'
    
    for filename in os.listdir(base_dir):
        if filename.endswith('.md'):
            filepath = os.path.join(base_dir, filename)
            fix_file(filepath)
    
    print(f"\n处理完成！")

if __name__ == '__main__':
    main()
