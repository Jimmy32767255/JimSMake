#!/usr/bin/env python3
"""
自动翻译 zh_CN.ts 文件
由于 zh_CN 是程序原生语言，所有未翻译的条目直接将 source 复制到 translation
"""

import re
import sys

def auto_translate_zh_cn(ts_file_path):
    """自动翻译 zh_CN.ts 文件"""

    with open(ts_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 匹配 message 块
    # 格式：
    # <message>
    #     <location .../>
    #     <source>...</source>
    #     <translation type="unfinished"></translation>
    # </message>

    pattern = r'(<message>.*?<source>(.*?)</source>\s*)<translation type="unfinished"></translation>'

    def replace_unfinished(match):
        prefix = match.group(1)
        source_text = match.group(2)
        # 将 source 复制到 translation
        return f'{prefix}<translation>{source_text}</translation>'

    # 替换所有未翻译的条目
    new_content = re.sub(pattern, replace_unfinished, content, flags=re.DOTALL)

    # 统计替换数量
    original_unfinished = content.count('<translation type="unfinished"></translation>')
    remaining_unfinished = new_content.count('<translation type="unfinished"></translation>')
    translated_count = original_unfinished - remaining_unfinished

    # 写回文件
    with open(ts_file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"翻译完成！")
    print(f"总共处理了 {original_unfinished} 条未翻译条目")
    print(f"成功翻译 {translated_count} 条")
    print(f"剩余 {remaining_unfinished} 条未翻译")

    return translated_count

if __name__ == '__main__':
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = 'zh_CN.ts'

    auto_translate_zh_cn(file_path)
