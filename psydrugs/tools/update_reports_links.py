#!/usr/bin/env python3
"""
更新reports中的所有英文分类路径为中文路径
"""
import os
import re
from pathlib import Path

def main():
    reports_dir = Path('/home/krvy/psydrugs.org/source/reports')
    
    # 映射表：英文路径 -> 中文路径
    path_mappings = {
        '/drugs/antidepressants/': '/drugs/抗抑郁药/',
        '/drugs/dissociatives/': '/drugs/解离剂/',
        '/drugs/antiemetics/': '/drugs/supplement/',
        '/drugs/antipsychotics/': '/drugs/抗精神病药/',
        '/drugs/opioids/': '/drugs/止痛药/',
        '/drugs/others/': '/drugs/',
        '/drugs/chemical_materials/': '/drugs/兴奋剂/',
        '/drugs/sedatives/': '/drugs/镇静剂/',
        '/drugs/补充剂/': '/drugs/补充剂/',
    }
    
    # 特殊药物映射（从旧路径到新路径）
    special_mappings = {
        '咖啡因': '兴奋剂/非苯丙胺类兴奋剂/咖啡因',
        '安非他酮': '抗ADHD药物/安非他酮',
        '右美沙芬_愈美片': '解离剂/右美沙芬_愈美片',
        '右美沙芬': '解离剂/右美沙芬_愈美片',
        '金刚烷胺': '解离剂/金刚烷胺',
        '茶苯海明': '谵妄剂/茶苯海明',
        '复方甘草片': '止咳药/复方甘草片',
        '氟伏沙明': '抗抑郁药/血清素再摄取抑制剂',
        '舍曲林': '抗抑郁药/血清素再摄取抑制剂',
        '乙醇': '镇静剂/其他药物/乙醇',
        '普瑞巴林': '镇静剂/加巴喷丁类药物/普瑞巴林',
        '奥氮平': '抗精神病药/奥氮平',
        '二氢可待因': '止咳药/二氢可待因',
        '白兔BRON': '止咳药/二氢可待因',
        'compound': '止咳药/复方甘草片',
        '血清素再摄取抑制剂': '抗抑郁药/血清素再摄取抑制剂',
    }
    
    changes_count = 0
    
    # 遍历所有markdown文件
    for md_file in reports_dir.rglob('*.md'):
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 1. 先处理特殊映射的精确匹配
        for old_name, new_path in special_mappings.items():
            # 处理形如 [药名](/drugs/oldpath/药名) 的链接
            pattern = f'\\[([^\\]]*{re.escape(old_name)}[^\\]]*)\\]\\(/drugs/[^/)]*/{re.escape(old_name)}\\)'
            replacement = f'[\\1](/drugs/{new_path})'
            content = re.sub(pattern, replacement, content)
            
            # 处理形如 [其他文本](/drugs/oldpath/药名) 的链接
            pattern = f'\\[([^\\]]*)\\]\\(/drugs/[^/)]*/{re.escape(old_name)}\\)'
            replacement = f'[\\1](/drugs/{new_path})'
            content = re.sub(pattern, replacement, content)
        
        # 2. 处理通用路径映射
        for old_path, new_path in path_mappings.items():
            # 只处理没有被特殊映射覆盖的链接
            pattern = f'\\[([^\\]]*)\\]\\({re.escape(old_path)}([^)]+)\\)'
            replacement = f'[\\1]({new_path}\\2)'
            content = re.sub(pattern, replacement, content)
        
        # 计算变更
        if content != original_content:
            changes_count += 1
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ 更新: {md_file.relative_to(reports_dir)}")
    
    print(f"\n完成! 更新了 {changes_count} 个文件")

if __name__ == '__main__':
    main()
