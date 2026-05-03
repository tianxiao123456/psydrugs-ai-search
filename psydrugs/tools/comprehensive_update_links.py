#!/usr/bin/env python3
"""
完整更新索引中的所有链接
"""
import re
import urllib.parse

def main():
    index_path = '/home/krvy/psydrugs.org/source/drugs/索引.md'
    
    # URL映射表 - 根据实际文件位置和上下文确定
    url_mapping = {
        # 基础规则：从旧的英文路径映射到新的中文路径
        '/drugs/opioids/': '/drugs/止痛药/',
        '/drugs/antipsychotics/': '/drugs/抗精神病药/',
        '/drugs/dissociatives/': '/drugs/解离剂/',
        '/drugs/sedatives/': '/drugs/镇静剂/',
        '/drugs/antidepressants/': '/drugs/抗抑郁药/',
        '/drugs/antiemetics/': '/drugs/补充剂/',
        '/drugs/chemical_materials/': '/drugs/兴奋剂/',
        '/drugs/others/': '/drugs/',
        '/drugs/补充剂/': '/drugs/补充剂/',
    }
    
    # 特殊映射 - 需要更具体路径的药物
    special_mapping = {
        '普瑞巴林': '/drugs/镇静剂/加巴喷丁类药物/普瑞巴林',
        '加巴喷丁': '/drugs/镇静剂/加巴喷丁类药物/加巴喷丁',
        '佐匹克隆': '/drugs/镇静剂/Z类药物_ZDrugs/佐匹克隆',
        '唑吡坦': '/drugs/镇静剂/Z类药物_ZDrugs/唑吡坦',
        '扎来普隆': '/drugs/镇静剂/Z类药物_ZDrugs/扎来普隆',
        '苯海拉明': '/drugs/镇静剂/其他药物/苯海拉明',
        '苯海索': '/drugs/镇静剂/其他药物/苯海索',
        '异丙嗪': '/drugs/镇静剂/其他药物/异丙嗪',
        '水合氯醛': '/drugs/镇静剂/其他药物/水合氯醛',
        '巴氯芬': '/drugs/镇静剂/其他药物/巴氯芬',
        '依托咪酯': '/drugs/镇静剂/其他药物/依托咪酯',
        '1,4-丁二醇': '/drugs/镇静剂/其他药物/1,4-丁二醇',
        '乙醇': '/drugs/镇静剂/其他药物/乙醇',
        '甲溴喹酮': '/drugs/镇静剂/其他药物/甲溴喹酮',
        '加波沙朵': '/drugs/镇静剂/其他药物/加波沙朵',
        '卡利普多': '/drugs/镇静剂/其他药物/卡利普多',
        '右美沙芬': '/drugs/解离剂/右美沙芬_愈美片',
        '右美沙芬_愈美片': '/drugs/解离剂/右美沙芬_愈美片',
        '氯胺酮': '/drugs/解离剂/氯胺酮',
        '替来他明': '/drugs/解离剂/替来他明',
        '金刚烷胺': '/drugs/解离剂/金刚烷胺',
        '美金刚': '/drugs/解离剂/美金刚',
        '丙泊酚': '/drugs/解离剂/丙泊酚',
        '地芬尼多': '/drugs/解离剂/地芬尼多',
        '一氧化二氮': '/drugs/解离剂/一氧化二氮',
        '3-羟基芬纳西泮': '/drugs/解离剂/3-羟基芬纳西泮',
        '哌甲酯': '/drugs/抗ADHD药物/哌甲酯',
        '安非他酮': '/drugs/抗ADHD药物/安非他酮',
        '托莫西汀': '/drugs/抗ADHD药物/托莫西汀',
        '咖啡因': '/drugs/兴奋剂/非苯丙胺类兴奋剂/咖啡因',
        '槟榔碱': '/drugs/兴奋剂/非苯丙胺类兴奋剂/槟榔碱',
        '噻奈普汀': '/drugs/兴奋剂/非苯丙胺类兴奋剂/噻奈普汀',
        '二甲卡因': '/drugs/兴奋剂/非苯丙胺类兴奋剂/二甲卡因',
        '二氢可待因': '/drugs/止咳药/二氢可待因',
        '喷托维林': '/drugs/止咳药/喷托维林',
        '可待因': '/drugs/止痛药/可待因',
        '吗啡': '/drugs/止痛药/吗啡',
        '杜冷丁': '/drugs/止痛药/杜冷丁',
        '地芬诺酯': '/drugs/止痛药/地芬诺酯',
        '曲马多': '/drugs/止痛药/曲马多',
        '奈福泮': '/drugs/止痛药/奈福泮',
        '阿片类药物': '/drugs/止痛药/阿片类药物',
        '喹硫平': '/drugs/抗精神病药/喹硫平',
        '利培酮': '/drugs/抗精神病药/利培酮',
        '奥氮平': '/drugs/抗精神病药/奥氮平',
        '氨磺必利': '/drugs/抗精神病药/氨磺必利',
        '阿立哌唑': '/drugs/抗精神病药/阿立哌唑',
        '丙戊酸': '/drugs/情绪稳定剂/丙戊酸',
        '噻加宾': '/drugs/抗癫痫药/噻加宾',
        '托吡酯': '/drugs/抗癫痫药/托吡酯',
        '维加巴特林': '/drugs/抗癫痫药/维加巴特林',
        '大麻二酚': '/drugs/迷幻剂/大麻二酚',
        '麦角酸二乙酰胺': '/drugs/迷幻剂/麦角酸二乙酰胺',
        '肉豆蔻醚': '/drugs/迷幻剂/肉豆蔻醚',
        '鸦片': '/drugs/谵妄剂/鸦片',
        '茶苯海明': '/drugs/谵妄剂/茶苯海明',
        '茶氨酸': '/drugs/补充剂/茶氨酸',
        '吡拉西坦': '/drugs/补充剂/吡拉西坦',
        '止吐药': '/drugs/其他药物/止吐药',
        '血清素再摄取抑制剂': '/drugs/抗抑郁药/血清素再摄取抑制剂',
        '苯二氮卓类药物': '/drugs/镇静剂/苯二氮卓类药物',
        'Z类药物': '/drugs/镇静剂/Z类药物_ZDrugs',
        '苯丙胺类兴奋剂': '/drugs/兴奋剂/苯丙胺类兴奋剂',
        '索引': '/drugs/索引',
    }
    
    # 处理所有化学材料链接
    chem_materials = [
        ('PMEA', 'N-乙基-1-(4-甲氧基苯基)丙-2-胺(PMEA)'),
        ('5-甲氧基亚甲酮', '5-甲氧基亚甲酮'),
        ('硫化丙胺', '硫代丙胺'),
        ('1-(噻吩-3-基)丙-2-胺', '1-(噻吩-3-基)丙-2-胺'),
        ('NEP', 'NEP)'),
        ('3-Me-BZP', '3-Me-BZP'),
        ('D2PM', 'D2PM'),
        ('MDBZP', 'MDBZP'),
        ('2-AT', '2-AT'),
        ('Desoxy-D2PM', 'Desoxy-D2PM'),
        ('4-AcO-MET', '4-AcO-MET'),
        ('4-AcO-MiPT', '4-AcO-MiPT'),
        ('4-HO-DET', '4-HO-DET'),
        ('α,N,N-三甲基色胺', 'α,N,N-三甲基色胺'),
        ('N,N-二丙基色胺', 'N,N-二丙基色胺'),
        ('乙基麦司卡林', '乙基麦司卡林'),
        ('异丙斯卡林', '异丙斯卡林'),
        ('普鲁斯卡林', '普鲁斯卡林'),
        ('N-异丙基色胺', 'N-异丙基色胺'),
        ('4-O-去甲基麦司卡林', '4-O-去甲基麦司卡林'),
    ]
    
    for display_name, file_name in chem_materials:
        if display_name in ['4-AcO-MET', '4-AcO-MiPT', '4-HO-DET', 'α,N,N-三甲基色胺', 'N,N-二丙基色胺',
                            '乙基麦司卡林', '异丙斯卡林', '普鲁斯卡林', 'N-异丙基色胺', '4-O-去甲基麦司卡林']:
            special_mapping[display_name] = f'/drugs/迷幻剂/{file_name}'
        else:
            if '苯' in display_name or 'NEP' in display_name or '硫' in display_name or '噻' in display_name or 'PMEA' in display_name or '甲酮' in display_name:
                special_mapping[display_name] = f'/drugs/兴奋剂/苯丙胺类兴奋剂/{file_name}'
            else:
                special_mapping[display_name] = f'/drugs/兴奋剂/非苯丙胺类兴奋剂/{file_name}'
    
    # 读取文件
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 函数：更新单个链接
    def update_link(match):
        display_text = match.group(1)
        url = match.group(2)
        stars = match.group(3) if len(match.groups()) >= 3 else ''
        
        # 如果不是psydrugs.org的链接，跳过
        if not url.startswith('https://psydrugs.org/drugs/'):
            return match.group(0)
        
        # URL解码
        decoded_url = urllib.parse.unquote(url)
        
        # 提取药物名（从URL最后部分或显示文本）
        url_drug_name = decoded_url.split('/')[-2] if decoded_url.endswith('/') else decoded_url.split('/')[-1]
        
        # 从显示文本中提取可能的药物名
        display_names = [display_text]
        if '/' in display_text:
            display_names.extend([x.strip() for x in display_text.split('/')])
        
        # 查找匹配
        new_url = None
        for name in display_names + [url_drug_name]:
            if name in special_mapping:
                new_url = special_mapping[name]
                break
        
        if new_url:
            return f'[{display_text}]({new_url}){stars}'
        
        return match.group(0)
    
    # 使用正则表达式替换所有链接
    # 匹配格式: [文本](https://psydrugs.org/drugs/...) 可选的星级
    pattern = r'\[([^\]]+)\]\((https://psydrugs\.org/drugs/[^)]+)\)(\s*★+)?'
    updated_content = re.sub(pattern, update_link, content)
    
    # 计算变更数
    changes = len(re.findall(r'https://psydrugs\.org/drugs/', content)) - len(re.findall(r'https://psydrugs\.org/drugs/', updated_content))
    
    # 写回文件
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f'完成！更新了 {changes} 个链接')
    
    # 显示剩余的psydrugs链接
    remaining = re.findall(r'https://psydrugs\.org/drugs/[^\s)]+', updated_content)
    if remaining:
        print(f'\n还剩余 {len(remaining)} 个链接未更新:')
        for link in set(remaining)[:10]:
            print(f'  - {link}')

if __name__ == '__main__':
    main()
