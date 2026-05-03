#!/usr/bin/env python3
"""生成药物分类索引"""
import os
import re
from pathlib import Path

def get_title_from_file(filepath):
    """从文件中提取标题"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        match = re.search(r'^title:\s*(.+?)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        match = re.search(r'^#\s+(.+?)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
    except:
        pass
    return None

def collect_drugs():
    """收集所有药物"""
    drugs = {
        'antidepressants': {},
        'antiemetics': {},
        'antipsychotics': {},
        'chemical_materials': {},
        'dissociatives': {},
        'opioids': {},
        'others': {},
        'sedatives': {},
        '补充剂': {}
    }
    
    base_path = Path('/home/krvy/psydrugs.org/source/drugs')
    
    for category in drugs.keys():
        cat_path = base_path / category
        if cat_path.exists():
            for md_file in cat_path.glob('*.md'):
                name = md_file.stem
                title = get_title_from_file(md_file) or name
                drugs[category][name] = title
    
    return drugs

def assess_harm(name, title, category):
    """评估危害程度（用星标表示）"""
    # 高危害（5星） - 呼吸抑制、致命过量
    high_harm = ['阿片', '可待因', '吗啡', '杜冷丁', '地芬诺酯', '曲马多', '普瑞巴林']
    
    # 中高危害（4星） - 意识障碍、成瘾性强
    med_high_harm = ['氯胺酮', '右美沙芬', '替来他明', '金刚烷胺', '美金刚', '丙泊酚', 
                     '苯二氮卓', '唑吡坦', '佐匹克隆', '扎来普隆', '水合氯醛',
                     '麦角酸二乙酰胺', '一氧化二氮', '亚硝酸', '肉豆蔻']
    
    # 中危害（3星） - 代谢副作用、心电变化
    med_harm = ['喹硫平', '奥氮平', '利培酮', '阿立哌唑', '氨磺必利', 
                '丙戊酸', '拉莫三嗪', '加巴喷丁', '依托咪酯', '双氢麦角毒碱']
    
    # 轻中危害（2星） - 常见副作用但相对可控
    light_harm = ['托莫西汀', '安非他酮', '哌醋甲酯', '苯海拉明', '苯海索', 
                  '异丙嗪', '地芬尼多', '茶苯海明', '槟榔碱', '吡拉西坦',
                  '咖啡因', '茶碱', '苏糖酸镁', '巴氯芬', 'TPM', '乙醇']
    
    # 轻危害（1星） - 最小风险
    light_harm_min = ['茶氨酸', '茶', '补充剂', '酶抑制剂', '血清素再摄取抑制剂', 'Z药', '烷胺']
    
    harm_str = ''
    for drug in high_harm:
        if drug in title or drug in name:
            return '★★★★★'
    
    for drug in med_high_harm:
        if drug in title or drug in name:
            return '★★★★'
    
    for drug in med_harm:
        if drug in title or drug in name:
            return '★★★'
    
    for drug in light_harm:
        if drug in title or drug in name:
            return '★★'
    
    for drug in light_harm_min:
        if drug in title or drug in name:
            return '★'
    
    # 默认为 2 星
    if category == 'others':
        return '★★'
    elif category in ['补充剂', 'antiemetics']:
        return '★'
    elif category in ['opioids', 'dissociatives']:
        return '★★★★'
    elif category in ['sedatives']:
        return '★★★'
    elif category in ['antipsychotics', 'antidepressants']:
        return '★★'
    
    return '★★'

def main():
    drugs = collect_drugs()
    
    # 按药效分类的顺序
    category_order = [
        ('镇痛与成瘾管制', ['opioids']),
        ('解离与麻醉', ['dissociatives']),
        ('镇静催眠', ['sedatives']),
        ('抗精神病与情绪调节', ['antipsychotics']),
        ('抗抑郁与兴奋', ['antidepressants']),
        ('止吐与抗组胺', ['antiemetics']),
        ('补充与代谢调节', ['补充剂']),
        ('化学物质与设计药物', ['chemical_materials']),
        ('其他物质', ['others']),
    ]
    
    output = []
    output.append('---')
    output.append('wiki: drugs')
    output.append('layout: page')
    output.append('title: 药物分类')
    output.append('menu_id: drugs')
    output.append('comments: false')
    output.append('---')
    output.append('')
    output.append('## 药物安全导航')
    output.append('')
    output.append('欢迎来到药物板块，这里收录了常见药物的安全使用信息、风险提示与减害建议。')
    output.append('')
    output.append('### 危害程度说明')
    output.append('- ★★★★★（极高风险）：致命风险、严重成瘾性')
    output.append('- ★★★★（高风险）：呼吸抑制、意识障碍、高成瘾性')
    output.append('- ★★★（中风险）：代谢副作用、心电变化、中等成瘾性')
    output.append('- ★★（轻中风险）：常见副作用但相对可控')
    output.append('- ★（轻风险）：最小化学物质风险')
    output.append('')
    output.append('### 快速导航')
    output.append('- [导论与使用须知](/drugs/others/introduction-to-overdose/)')
    output.append('- [效应指南](/effects/)')
    output.append('')
    
    for category_name, cat_list in category_order:
        output.append(f'## {category_name}')
        output.append('')
        
        for cat in cat_list:
            if cat in drugs and drugs[cat]:
                for name in sorted(drugs[cat].keys()):
                    title = drugs[cat][name]
                    harm = assess_harm(name, title, cat)
                    
                    # 跳过索引文件
                    if name in ['index', 'introduction-to-overdose']:
                        continue
                    
                    # 处理带有子目录的文件（如右美沙芬_愈美片/HTCT5THP）
                    if '/' in name:
                        continue
                    
                    # 检查是否有子目录
                    subdir_path = Path(f'/home/krvy/psydrugs.org/source/drugs/{cat}/{name}')
                    has_subdir = subdir_path.is_dir()
                    
                    if has_subdir:
                        # 有子目录的物质
                        output.append(f'### {title} {harm}')
                        output.append(f'[{title}](/drugs/{cat}/{name}/) | ', end='')
                        output.append('')
                    else:
                        # 普通物质
                        output.append(f'- [{title}](/drugs/{cat}/{name}/) {harm}')
        
        output.append('')
    
    # 将列表转换为字符串
    content = '\n'.join(output)
    
    # 修正格式问题
    content = content.replace('| \n', '')
    
    # 添加结尾
    content += '''
> **免责声明**：本网站提供的信息仅供教育和减害目的。使用任何物质都具有潜在风险，务必在专业医师指导下进行。

'''
    
    return content

if __name__ == '__main__':
    print(main())
