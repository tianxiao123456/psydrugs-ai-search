#!/usr/bin/env python3
"""
更新 source/drugs/索引.md 中的所有链接为 /drugs/中文分类/文件名 格式
"""
import os
import re
from pathlib import Path

# 获取实际文件结构的映射
def scan_drugs_directory(base_path):
    """
    扫描 /source/drugs/ 目录，创建药物名称到路径的映射
    返回: {药物名称: 相对路径}
    """
    drugs_map = {}
    drugs_dir = Path(base_path) / 'source' / 'drugs'
    
    # 遍历所有分类目录
    for category_dir in drugs_dir.iterdir():
        if not category_dir.is_dir():
            continue
        if category_dir.name in ['index.md', '索引.md', '药物作用.md']:
            continue
            
        # 扫描该分类下的所有文件和子目录
        for root, dirs, files in os.walk(category_dir):
            for file in files:
                if file.endswith('.md') and file not in ['index.md', 'README.md']:
                    # 获取完整路径
                    full_path = Path(root) / file
                    # 计算相对于 source/drugs/ 的路径
                    rel_path = full_path.relative_to(drugs_dir)
                    # 去除 .md 后缀
                    path_without_ext = str(rel_path)[:-3]
                    # 提取药物名称（文件名去除 .md）
                    drug_name = file[:-3]
                    
                    # 存储映射（如果重复，保留第一个）
                    if drug_name not in drugs_map:
                        drugs_map[drug_name] = path_without_ext
    
    return drugs_map

def extract_link_text(line):
    """从 Markdown 链接中提取显示文本和URL"""
    # 匹配 [文本](URL) 格式
    match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', line)
    if match:
        return match.group(1), match.group(2), match.group(0)
    return None, None, None

def update_links_in_index(index_path, drugs_map, base_path):
    """更新索引文件中的所有链接"""
    with open(index_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    updated_lines = []
    changes_count = 0
    
    for line in lines:
        original_line = line
        
        # 检查是否包含链接
        if '[' in line and '](' in line:
            display_text, url, full_match = extract_link_text(line)
            
            if display_text and url:
                # 检查是否是绝对 URL（https://psydrugs.org/...）
                if url.startswith('https://psydrugs.org/drugs/'):
                    # 提取可能的药物名称
                    # 从 URL 中提取最后一部分作为可能的药物名
                    url_parts = url.rstrip('/').split('/')
                    possible_name = url_parts[-1]
                    
                    # URL 解码
                    import urllib.parse
                    possible_name = urllib.parse.unquote(possible_name)
                    
                    # 在映射中查找
                    if possible_name in drugs_map:
                        new_url = f"/drugs/{drugs_map[possible_name]}"
                        new_link = f"[{display_text}]({new_url})"
                        line = line.replace(full_match, new_link)
                        changes_count += 1
                        print(f"✓ 更新: {possible_name}")
                        print(f"  旧: {url}")
                        print(f"  新: {new_url}")
                    else:
                        # 尝试从显示文本中提取药物名
                        # 处理如 "右美沙芬/愈美片" 的情况
                        name_parts = display_text.split('/')
                        found = False
                        for part in name_parts:
                            clean_name = part.strip()
                            if clean_name in drugs_map:
                                new_url = f"/drugs/{drugs_map[clean_name]}"
                                new_link = f"[{display_text}]({new_url})"
                                line = line.replace(full_match, new_link)
                                changes_count += 1
                                print(f"✓ 更新: {clean_name} (从显示文本)")
                                print(f"  旧: {url}")
                                print(f"  新: {new_url}")
                                found = True
                                break
                        
                        if not found:
                            print(f"⚠ 未找到: {display_text} ({possible_name})")
                
                # 检查是否已经是相对链接但格式不正确
                elif url.startswith('/drugs/') and 'psydrugs.org' not in url:
                    # 已经是相对链接，检查是否需要更新
                    # 提取路径部分
                    path_part = url[7:]  # 去除 '/drugs/'
                    # 提取文件名部分
                    file_name = path_part.split('/')[-1]
                    
                    # 检查文件是否存在于正确位置
                    if file_name in drugs_map and drugs_map[file_name] != path_part:
                        new_url = f"/drugs/{drugs_map[file_name]}"
                        new_link = f"[{display_text}]({new_url})"
                        line = line.replace(full_match, new_link)
                        changes_count += 1
                        print(f"✓ 修正路径: {file_name}")
                        print(f"  旧: {url}")
                        print(f"  新: {new_url}")
        
        updated_lines.append(line)
    
    # 写回文件
    with open(index_path, 'w', encoding='utf-8') as f:
        f.writelines(updated_lines)
    
    return changes_count

def main():
    # 基础路径
    base_path = '/home/krvy/psydrugs.org'
    index_path = os.path.join(base_path, 'source', 'drugs', '索引.md')
    
    print("正在扫描 drugs 目录结构...")
    drugs_map = scan_drugs_directory(base_path)
    print(f"找到 {len(drugs_map)} 个药物文件\n")
    
    print("开始更新索引链接...\n")
    changes = update_links_in_index(index_path, drugs_map, base_path)
    
    print(f"\n完成! 共更新了 {changes} 个链接")

if __name__ == '__main__':
    main()
