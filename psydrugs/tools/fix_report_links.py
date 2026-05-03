#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复报告中的药物链接引用
"""

import os
import re
from pathlib import Path

# 短代码映射
SHORT_CODE_MAPPING = {
    'ZPO': 'sedatives/扎来普隆',
    'DPH': 'sedatives/苯海拉明',
    'NFP': 'opioids/奈福泮',
    'QTP': 'antipsychotics/喹硫平',
    'PMZ': 'sedatives/异丙嗪',
    'VPA': 'antipsychotics/丙戊酸',
    'ZPC': 'sedatives/佐匹克隆',
    'APP': 'antipsychotics/阿立哌唑',
    'OZP': 'antipsychotics/奥氮平',
    'ZPD': 'sedatives/唑吡坦',
    'PR': 'antipsychotics/普瑞巴林',
    'DXM': 'dissociatives/右美沙芬_愈美片',
    'SRIs': 'antidepressants/血清素再摄取抑制剂',
}

def fix_report_links(file_path):
    """修复报告文件中的链接"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        modified = False
        
        # 1. 修复 /zh/drugs/ 前缀，改为 /drugs/
        if '/zh/drugs/' in content:
            # 提取 /zh/drugs/XXX 的代码
            pattern = r'\[([^\]]+)\]\(/zh/drugs/([^/)]+)(/[^)]*)?\)'
            
            def replace_zh_prefix(match):
                nonlocal modified
                link_text = match.group(1)
                short_code = match.group(2)
                suffix = match.group(3) or ''
                
                if short_code in SHORT_CODE_MAPPING:
                    new_path = SHORT_CODE_MAPPING[short_code]
                    modified = True
                    return f'[{link_text}](/drugs/{new_path}{suffix})'
                else:
                    modified = True
                    return f'[{link_text}](/drugs/{short_code}{suffix})'
            
            content = re.sub(pattern, replace_zh_prefix, content)
        
        # 2. 修复不完整的短代码链接 /drugs/XXX（没有分类前缀）
        pattern = r'\[([^\]]+)\]\(/drugs/([A-Z]{2,5})(/[^)]*)?\)'
        
        def replace_short_code(match):
            nonlocal modified
            link_text = match.group(1)
            short_code = match.group(2)
            suffix = match.group(3) or ''
            
            if short_code in SHORT_CODE_MAPPING:
                new_path = SHORT_CODE_MAPPING[short_code]
                modified = True
                return f'[{link_text}](/drugs/{new_path}{suffix})'
            else:
                return match.group(0)
        
        content = re.sub(pattern, replace_short_code, content)
        
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, file_path
        return False, None
        
    except Exception as e:
        print(f"处理文件时出错 {file_path}: {e}")
        return False, None

def main():
    """主函数"""
    reports_dir = Path('/home/krvy/psydrugs.org/source/reports')
    
    modified_files = []
    
    # 遍历所有报告文件
    for file_path in reports_dir.glob('*.md'):
        was_modified, path = fix_report_links(file_path)
        if was_modified:
            modified_files.append(path)
    
    print(f"\n修复完成！共修改了 {len(modified_files)} 个报告文件：")
    for file in sorted(modified_files):
        print(f"  - {file.name}")

if __name__ == '__main__':
    main()
