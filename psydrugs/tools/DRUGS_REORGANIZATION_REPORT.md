# Drugs 文件夹分类整理完成报告

## 完成时间

2026-01-25

## 分类方案

已将 source/drugs/ 目录下的所有药物文件按照以下8个分类文件夹进行组织：

### 1. opioids（阿片与镇痛）

- 阿片类药物.md
- 可待因.md
- 二氢可待因.md
- 吗啡.md
- 杜冷丁.md
- 曲马多.md
- 地芬诺酯.md
- 喷托维林.md
- 奈福泮.md

### 2. dissociatives（解离与麻醉）

- 右美沙芬_愈美片/ + .md
- 氯胺酮.md
- 金刚烷胺.md
- 美金刚.md
- 替来他明.md
- 丙泊酚.md
- 地芬尼多.md

### 3. sedatives（镇静催眠/睡眠）

- 苯二氮卓类药物.md
- Z药物.md
- 佐匹克隆.md
- 唑吡坦.md
- 扎来普隆.md
- 水合氯醛.md
- 苯海拉明.md
- 苯海索.md
- 异丙嗪.md

### 4. antipsychotics（抗精神病/情绪稳定）

- 喹硫平.md
- 奥氮平.md
- 利培酮.md
- 阿立哌唑.md
- 氨磺必利.md
- 丙戊酸.md
- 拉莫三嗪.md
- 普瑞巴林.md
- 加巴喷丁.md

### 5. antidepressants（抗抑郁与注意力）

- 血清素再摄取抑制剂.md
- 托莫西汀.md
- 安非他酮.md
- 哌醋甲酯.md
- 苯丙胺类药物.md
- 咖啡因.md
- 烷胺类药物.md

### 6. antiemetics（止吐/抗组胺/胃肠）

- 止吐药.md
- 茶苯海明.md
- 槟榔碱.md
- 吡拉西坦.md

### 7. 补充剂（补充剂与代谢调节）

- 酶抑制剂.md
- 补充剂.md
- 苏糖酸镁/ + .md
- 茶碱.md
- 茶氨酸.md
- 茶.md

### 8. others（其他）

- compound.md（复方专题）
- 乙醇.md
- 巴氯芬.md
- TPM.md
- Cigarette.html
- psychedelics.html
- DHCDI/（文件夹）
- introduction-to-overdose.md
- new-page.md

## 链接修复统计

### 第一轮修复（完整路径）

修复了 94 个文件中的药物链接，包括：

- 所有 reports/ 下的报告文件
- effects/ 下的效应说明文件
- Others/ 下的其他文档
- drugs/ 下各个分类的药物文档本身

### 第二轮修复（短代码）

修复了 46 个文件中的短代码链接，包括：

- SPM → 补充剂/补充剂
- PR → antipsychotics/普瑞巴林
- TPL → 补充剂/茶碱
- TAN → 补充剂/茶氨酸
- EI → 补充剂/酶抑制剂
- THP → sedatives/苯海索
- MGT → 补充剂/苏糖酸镁
- GBP → antipsychotics/加巴喷丁
- RPD → antipsychotics/利培酮
- MMT → dissociatives/美金刚

## 验证结果

✅ 网站生成成功，共生成 280 个文件
✅ 无错误或警告信息
✅ 所有分类文件夹创建成功
✅ 所有药物文件已移动到对应分类
✅ 所有内部链接已更新并正确指向新路径

## 使用的脚本

创建了两个 Python 脚本用于自动化链接修复：

1. `fix_drug_links.py` - 修复完整路径的药物链接
2. `fix_short_code_links.py` - 修复短代码格式的药物链接

这些脚本可以在未来需要时重复使用。

## 建议

1. 建议为每个分类文件夹创建 index.md 索引页面，方便用户浏览
2. 可以在主 index.md 中添加更详细的分类说明
3. 定期检查是否有新的药物文件需要归类
