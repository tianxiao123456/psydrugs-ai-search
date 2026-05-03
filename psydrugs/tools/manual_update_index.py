#!/usr/bin/env python3
"""
手动更新索引链接 - 根据上下文选择正确的分类
"""
import re

def main():
    index_path = '/home/krvy/psydrugs.org/source/drugs/索引.md'
    
    # 读取文件
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 定义所有需要替换的映射 (旧URL -> 新URL)
    replacements = [
        # 常见od药物部分
        ('https://psydrugs.org/drugs/antipsychotics/%E6%99%AE%E7%91%9E%E5%B7%B4%E6%9E%97/', '/drugs/镇静剂/加巴喷丁类药物/普瑞巴林'),
        ('https://psydrugs.org/drugs/opioids/%E4%BA%8C%E6%B0%A2%E5%8F%AF%E5%BE%85%E5%9B%A0/', '/drugs/止痛药/二氢可待因'),
        ('https://psydrugs.org/drugs/dissociatives/%E9%87%91%E5%88%9A%E7%83%B7%E8%83%BA/', '/drugs/解离剂/金刚烷胺'),
        
        # 镇静剂 - 阿片类
        ('https://psydrugs.org/drugs/opioids/%E9%98%BF%E7%89%87%E7%B1%BB%E8%8D%AF%E7%89%A9/', '/drugs/止痛药/阿片类药物'),
        ('https://psydrugs.org/drugs/opioids/%E5%90%97%E5%95%A1/', '/drugs/止痛药/吗啡'),
        ('https://psydrugs.org/drugs/opioids/%E5%8F%AF%E5%BE%85%E5%9B%A0/', '/drugs/止痛药/可待因'),
        ('https://psydrugs.org/drugs/opioids/%E6%9D%9C%E5%86%B7%E4%B8%81/', '/drugs/止痛药/杜冷丁'),
        ('https://psydrugs.org/drugs/opioids/%E5%9C%B0%E8%8A%AC%E8%AF%BA%E9%85%AF/', '/drugs/止痛药/地芬诺酯'),
        ('https://psydrugs.org/drugs/opioids/%E6%9B%B2%E9%A9%AC%E5%A4%9A/', '/drugs/止痛药/曲马多'),
        ('https://psydrugs.org/drugs/others/%E9%B8%A6%E7%89%87/', '/drugs/谵妄剂/鸦片'),
        
        # 镇静剂 - 苯二氮卓类
        ('https://psydrugs.org/drugs/sedatives/%E8%8B%AF%E4%BA%8C%E6%B0%AE%E5%8D%93%E7%B1%BB%E8%8D%AF%E7%89%A9/', '/drugs/镇静剂/苯二氮卓类药物'),
        
        # 镇静剂 - Z类药物
        ('https://psydrugs.org/drugs/sedatives/Z%E8%8D%AF%E7%89%A9/', '/drugs/镇静剂/Z类药物_ZDrugs'),
        ('https://psydrugs.org/drugs/sedatives/%E4%BD%90%E5%8C%B9%E5%85%8B%E9%9A%86/', '/drugs/镇静剂/Z类药物_ZDrugs/佐匹克隆'),
        ('https://psydrugs.org/drugs/sedatives/%E5%94%91%E5%90%A1%E5%9D%A6/', '/drugs/镇静剂/Z类药物_ZDrugs/唑吡坦'),
        ('https://psydrugs.org/drugs/sedatives/%E6%89%8E%E6%9D%A5%E6%99%AE%E9%9A%86/', '/drugs/镇静剂/Z类药物_ZDrugs/扎来普隆'),
        
        # 镇静剂 - 加巴喷丁类
        ('https://psydrugs.org/drugs/antipsychotics/%E5%8A%A0%E5%B7%B4%E5%96%B7%E4%B8%81/', '/drugs/镇静剂/加巴喷丁类药物/加巴喷丁'),
        
        # 镇静剂 - 抗精神病药
        ('https://psydrugs.org/drugs/antipsychotics/%E5%96%B9%E7%A1%AB%E5%B9%B3/', '/drugs/抗精神病药/喹硫平'),
        ('https://psydrugs.org/drugs/antipsychotics/%E5%88%A9%E5%9F%B9%E9%85%AE/', '/drugs/抗精神病药/利培酮'),
        ('https://psydrugs.org/drugs/antipsychotics/%E5%A5%A5%E6%B0%AE%E5%B9%B3/', '/drugs/抗精神病药/奥氮平'),
        ('https://psydrugs.org/drugs/sedatives/%E5%BC%82%E4%B8%99%E5%97%AA/', '/drugs/镇静剂/其他药物/异丙嗪'),
        ('https://psydrugs.org/drugs/antipsychotics/%E6%B0%A8%E7%A3%BA%E5%BF%85%E5%88%A9/', '/drugs/抗精神病药/氨磺必利'),
        ('https://psydrugs.org/drugs/antipsychotics/%E9%98%BF%E7%AB%8B%E5%93%8C%E5%94%91/', '/drugs/抗精神病药/阿立哌唑'),
        
        # 镇静剂 - 其他药物
        ('https://psydrugs.org/drugs/dissociatives/%E4%B8%99%E6%B3%8A%E9%85%9A/', '/drugs/解离剂/丙泊酚'),
        ('https://psydrugs.org/drugs/sedatives/%E6%B0%B4%E5%90%88%E6%B0%AF%E9%86%9B/', '/drugs/镇静剂/其他药物/水合氯醛'),
        ('https://psydrugs.org/drugs/sedatives/%E8%8B%AF%E6%B5%B7%E6%8B%89%E6%98%8E/', '/drugs/镇静剂/其他药物/苯海拉明'),
        ('https://psydrugs.org/drugs/sedatives/%E8%8B%AF%E6%B5%B7%E7%B4%A2/', '/drugs/镇静剂/其他药物/苯海索'),
        ('https://psydrugs.org/drugs/opioids/%E5%96%B7%E6%89%98%E7%BB%B4%E6%9E%97/', '/drugs/止咳药/喷托维林'),
        ('https://psydrugs.org/drugs/dissociatives/%E5%9C%B0%E8%8A%AC%E5%B0%BC%E5%A4%9A/', '/drugs/解离剂/地芬尼多'),
        ('https://psydrugs.org/drugs/others/%E5%99%BB%E5%8A%A0%E5%AE%BE/', '/drugs/抗癫痫药/噻加宾'),
        ('https://psydrugs.org/drugs/antipsychotics/%E4%B8%99%E6%88%8A%E9%85%B8/', '/drugs/情绪稳定剂/丙戊酸'),
        ('https://psydrugs.org/drugs/%E7%B4%A2%E5%BC%95/', '/drugs/索引'),
        ('https://psydrugs.org/drugs/others/%E5%B7%B4%E6%B0%AF%E8%8A%AC/', '/drugs/镇静剂/其他药物/巴氯芬'),
        ('https://psydrugs.org/drugs/others/TPM/', '/drugs/抗癫痫药/托吡酯'),
        ('https://psydrugs.org/drugs/others/%E4%BE%9D%E6%89%98%E5%92%AA%E9%85%AF/', '/drugs/镇静剂/其他药物/依托咪酯'),
        
        # 镇静剂 - 其他物质
        ('https://psydrugs.org/drugs/others/%E5%A4%A7%E9%BA%BB%E4%BA%8C%E9%85%9A/', '/drugs/迷幻剂/大麻二酚'),
        ('https://psydrugs.org/drugs/others/%E7%94%B2%E6%BA%B4%E5%96%B9%E9%85%AE/', '/drugs/镇静剂/其他药物/甲溴喹酮'),
        ('https://psydrugs.org/drugs/chemical_materials/%E5%99%BB%E5%A5%88%E6%99%AE%E6%B1%80/', '/drugs/兴奋剂/非苯丙胺类兴奋剂/噻奈普汀'),
        ('https://psydrugs.org/drugs/others/%E7%BB%B4%E5%8A%A0%E5%B7%B4%E7%89%B9%E6%9E%97/', '/drugs/抗癫痫药/维加巴特林'),
        ('https://psydrugs.org/drugs/others/1,4-%E4%B8%81%E4%BA%8C%E9%86%87/', '/drugs/镇静剂/其他药物/1,4-丁二醇'),
        ('https://psydrugs.org/drugs/others/%E4%B9%99%E9%86%87/', '/drugs/镇静剂/其他药物/乙醇'),
        ('https://psydrugs.org/drugs/补充剂/%E8%8C%B6%E6%B0%A8%E9%85%B8/', '/drugs/补充剂/茶氨酸'),
        ('https://psydrugs.org/drugs/chemical_materials/%E5%8A%A0%E6%B3%A2%E6%B2%99%E6%9C%B5%EF%BC%88Gaboxadol%EF%BC%89%20-%20GABA%E7%B1%BB%E5%8C%96%E5%90%88%E7%89%A9%E7%A7%91%E6%99%AE/', '/drugs/镇静剂/其他药物/加波沙朵'),
        ('https://psydrugs.org/drugs/chemical_materials/%E5%8D%A1%E7%AB%8B%E6%99%AE%E5%A4%9A%EF%BC%88Carisoprodol%EF%BC%89%20-%20%E8%82%8C%E8%82%89%E6%9D%BE%E5%BC%9B%E5%89%82%E7%A7%91%E6%99%AE/', '/drugs/镇静剂/其他药物/卡利普多'),
        
        # 兴奋剂 - 苯丙胺类
        ('https://psydrugs.org/drugs/antidepressants/%E8%8B%AF%E4%B8%99%E8%83%BA%E7%B1%BB%E8%8D%AF%E7%89%A9/', '/drugs/兴奋剂/苯丙胺类兴奋剂'),
        ('https://psydrugs.org/drugs/antidepressants/%E5%93%8C%E9%86%8B%E7%94%B2%E9%85%AF/', '/drugs/抗ADHD药物/哌甲酯'),
        ('https://psydrugs.org/drugs/chemical_materials/N-%E4%B9%99%E5%9F%BA-1-(4-%E7%94%B2%E6%B0%A7%E5%9F%BA%E8%8B%AF%E5%9F%BA)%E4%B8%99-2-%E8%83%BA(PMEA)/', '/drugs/兴奋剂/苯丙胺类兴奋剂/PMEA'),
        ('https://psydrugs.org/drugs/antidepressants/%E5%AE%89%E9%9D%9E%E4%BB%96%E9%85%AE/', '/drugs/抗ADHD药物/安非他酮'),
        ('https://psydrugs.org/drugs/chemical_materials/5-%E7%94%B2%E6%B0%A7%E5%9F%BA%E4%BA%9A%E7%94%B2%E9%85%AE/', '/drugs/兴奋剂/苯丙胺类兴奋剂/5-甲氧基亚甲酮'),
        ('https://psydrugs.org/drugs/chemical_materials/%E7%A1%AB%E4%BB%A3%E4%B8%99%E8%83%BA/', '/drugs/兴奋剂/苯丙胺类兴奋剂/硫化丙胺'),
        ('https://psydrugs.org/drugs/chemical_materials/1-(%E5%99%BB%E5%90%A9-3-%E5%9F%BA)%E4%B8%99-2-%E8%83%BA/', '/drugs/兴奋剂/苯丙胺类兴奋剂/1-(噻吩-3-基)丙-2-胺'),
        ('https://psydrugs.org/drugs/chemical_materials/N-%E4%B9%99%E5%9F%BA%E6%88%8A%E9%85%AE%EF%BC%88NEP%EF%BC%89/', '/drugs/兴奋剂/苯丙胺类兴奋剂/NEP)'),
        
        # 兴奋剂 - 非苯丙胺类
        ('https://psydrugs.org/drugs/antiemetics/%E6%A7%9F%E6%A6%94%E7%A2%B1/', '/drugs/兴奋剂/非苯丙胺类兴奋剂/槟榔碱'),
        ('https://psydrugs.org/drugs/antidepressants/%E5%92%96%E5%95%A1%E5%9B%A0/', '/drugs/兴奋剂/非苯丙胺类兴奋剂/咖啡因'),
        ('https://psydrugs.org/drugs/antidepressants/%E6%89%98%E8%8E%AB%E8%A5%BF%E6%B1%80/', '/drugs/抗ADHD药物/托莫西汀'),
        ('https://psydrugs.org/drugs/chemical_materials/1-(3-%E7%94%B2%E5%9F%BA%E8%8B%AF%E7%94%B2%E5%9F%BA)%E5%93%8C%E5%97%AA%EF%BC%883-Me-BZP%EF%BC%89/', '/drugs/兴奋剂/非苯丙胺类兴奋剂/3-Me-BZP'),
        ('https://psydrugs.org/drugs/chemical_materials/D2PM%EF%BC%88%E4%BA%8C%E8%8B%AF%E5%9F%BA%E8%84%AF%E6%B0%A8%E9%86%87%EF%BC%89/', '/drugs/兴奋剂/非苯丙胺类兴奋剂/D2PM'),
        ('https://psydrugs.org/drugs/chemical_materials/1-%E8%83%A1%E6%A4%92%E5%9F%BA%E5%93%8C%E5%97%AA%EF%BC%88MDBZP%EF%BC%89/', '/drugs/兴奋剂/非苯丙胺类兴奋剂/MDBZP'),
        ('https://psydrugs.org/drugs/chemical_materials/2-AT%EF%BC%881,2,3,4-%E5%9B%9B%E6%B0%A2%E8%90%98-2-%E8%83%BA%EF%BC%89/', '/drugs/兴奋剂/非苯丙胺类兴奋剂/2-AT'),
        ('https://psydrugs.org/drugs/chemical_materials/2-%E4%BA%8C%E8%8B%AF%E7%94%B2%E5%9F%BA%E5%90%A1%E5%92%AF%E7%83%B7%EF%BC%88Desoxy-D2PM%EF%BC%89/', '/drugs/兴奋剂/非苯丙胺类兴奋剂/Desoxy-D2PM'),
        ('https://psydrugs.org/drugs/chemical_materials/%E4%BA%8C%E7%94%B2%E5%8D%A1%E5%9B%A0/', '/drugs/兴奋剂/非苯丙胺类兴奋剂/二甲卡因'),
        
        # 解离剂
        ('https://psydrugs.org/drugs/dissociatives/%E6%B0%AF%E8%83%BA%E9%85%AE/', '/drugs/解离剂/氯胺酮'),
        ('https://psydrugs.org/drugs/dissociatives/%E5%8F%B3%E7%BE%8E%E6%B2%99%E8%8A%AC_%E6%84%88%E7%BE%8E%E7%89%87/', '/drugs/解离剂/右美沙芬_愈美片'),
        ('https://psydrugs.org/drugs/dissociatives/%E6%9B%BF%E6%9D%A5%E4%BB%96%E6%98%8E/', '/drugs/解离剂/替来他明'),
        ('https://psydrugs.org/drugs/dissociatives/%E7%BE%8E%E9%87%91%E5%88%9A/', '/drugs/解离剂/美金刚'),
        ('https://psydrugs.org/drugs/others/%E4%B8%80%E6%B0%A7%E5%8C%96%E4%BA%8C%E6%B0%AE/', '/drugs/解离剂/一氧化二氮'),
        ('https://psydrugs.org/drugs/others/3-%E7%BE%9F%E5%9F%BA%E8%8A%AC%E7%BA%B3%E8%A5%BF%E6%B3%AE/', '/drugs/解离剂/3-羟基芬纳西泮'),
        
        # 迷幻剂
        ('https://psydrugs.org/drugs/chemical_materials/4-AcO-MET/', '/drugs/迷幻剂/4-AcO-MET'),
        ('https://psydrugs.org/drugs/chemical_materials/4-AcO-MiPT/', '/drugs/迷幻剂/4-AcO-MiPT'),
        ('https://psydrugs.org/drugs/chemical_materials/4-HO-DET/', '/drugs/迷幻剂/4-HO-DET'),
        ('https://psydrugs.org/drugs/chemical_materials/%CE%B1,N,N-%E4%B8%89%E7%94%B2%E5%9F%BA%E8%89%B2%E8%83%BA/', '/drugs/迷幻剂/α,N,N-三甲基色胺'),
        ('https://psydrugs.org/drugs/chemical_materials/N,N-%E4%BA%8C%E4%B8%99%E5%9F%BA%E8%89%B2%E8%83%BA/', '/drugs/迷幻剂/N,N-二丙基色胺'),
        ('https://psydrugs.org/drugs/chemical_materials/%E4%B9%99%E5%9F%BA%E9%BA%A6%E5%8F%B8%E5%8D%A1%E6%9E%97%EF%BC%88Escaline%EF%BC%89%20-%20%E5%90%88%E6%88%90%E8%BF%B7%E5%B9%BB%E7%89%A9%E8%B4%A8%E7%A7%91%E6%99%AE/', '/drugs/迷幻剂/乙基麦司卡林'),
        ('https://psydrugs.org/drugs/chemical_materials/%E5%BC%82%E4%B8%99%E6%96%AF%E5%8D%A1%E6%9E%97%EF%BC%88Isoproscaline%EF%BC%89%20-%20%E8%8B%AF%E4%B9%99%E8%83%BA%E7%B1%BB%E5%8C%96%E5%90%88%E7%89%A9%E7%A7%91%E6%99%AE/', '/drugs/迷幻剂/异丙斯卡林'),
        ('https://psydrugs.org/drugs/chemical_materials/%E6%99%AE%E9%B2%81%E6%96%AF%E5%8D%A1%E6%9E%97%EF%BC%88%E6%99%AE%E7%BD%97%E5%8F%B8%E5%8D%A1%E6%9E%97%EF%BC%89%20-%20%E8%87%B4%E5%B9%BB%E8%8D%AF%E7%89%A9%E7%A7%91%E6%99%AE/', '/drugs/迷幻剂/普鲁斯卡林'),
        ('https://psydrugs.org/drugs/chemical_materials/N-%E5%BC%82%E4%B8%99%E5%9F%BA%E8%89%B2%E8%83%BA/', '/drugs/迷幻剂/N-异丙基色胺'),
        ('https://psydrugs.org/drugs/chemical_materials/4-O-%E5%8E%BB%E7%94%B2%E5%9F%BA%E9%BA%A6%E5%8F%B8%E5%8D%A1%E6%9E%97%20-%20%E8%8B%AF%E4%B9%99%E8%83%BA%E7%B1%BB%E7%94%9F%E7%89%A9%E7%A2%B1%E7%A7%91%E6%99%AE/', '/drugs/迷幻剂/4-O-去甲基麦司卡林'),
        ('https://psydrugs.org/drugs/others/%E9%BA%A6%E8%A7%92%E9%85%B8%E4%BA%8C%E4%B9%99%E9%85%B0%E8%83%BA/', '/drugs/迷幻剂/麦角酸二乙酰胺'),
        ('https://psydrugs.org/drugs/others/%E8%82%89%E8%B1%86%E8%94%BB%E9%86%9A/', '/drugs/迷幻剂/肉豆蔻醚'),
        
        # 谵妄剂
        ('https://psydrugs.org/drugs/antiemetics/%E8%8C%B6%E8%8B%AF%E6%B5%B7%E6%98%8E/', '/drugs/谵妄剂/茶苯海明'),
        
        # 抗抑郁药
        ('https://psydrugs.org/drugs/antidepressants/%E8%A1%80%E6%B8%85%E7%B4%A0%E5%86%8D%E6%91%84%E5%8F%96%E6%8A%91%E5%88%B6%E5%89%82/', '/drugs/抗抑郁药/血清素再摄取抑制剂'),
        
        # 减害与补充
        ('https://psydrugs.org/drugs/antiemetics/%E5%90%A1%E6%8B%89%E8%A5%BF%E5%9D%A6/', '/drugs/补充剂/吡拉西坦'),
        ('https://psydrugs.org/drugs/antiemetics/%E6%AD%A2%E5%90%90%E8%8D%AF/', '/drugs/补充剂/止吐药'),
        
        # 止痛药
        ('https://psydrugs.org/drugs/opioids/%E5%A5%88%E7%A6%8F%E6%B3%AE/', '/drugs/止痛药/奈福泮'),
    ]
    
    # 执行替换
    changes_count = 0
    for old_url, new_url in replacements:
        if old_url in content:
            content = content.replace(old_url, new_url)
            changes_count += 1
            print(f"✓ 更新: {old_url.split('/')[-1]}")
    
    # 写回文件
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n完成! 共更新了 {changes_count} 个链接")

if __name__ == '__main__':
    main()
