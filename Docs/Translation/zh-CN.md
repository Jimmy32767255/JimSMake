# 国际化支持

[返回](../../README.md)

本程序使用 QTranslator 翻译支持框架

#### 更新翻译：

1. 生成翻译文件：
   
   ```bash
   # 先移除旧的中文翻译，以后重新生成
   rm ./Translation/zh_CN.ts
   # 使用 pylupdate5 自动处理翻译文件生成和更新
   pylupdate5 ./Translation/SMake.pro
   # 注意：对于zh_cn，由于它是程序原生语言，不需要翻译，你可以使用此脚本 Python 来快速完成它：
   python ./Translation/auto_translate_zh_cn.py ./Translation/zh_CN.ts
   ```

2. 使用 Qt Linguist 或手动编辑除`zh_CN`以外的翻译文件

3. 编译生成 .qm 文件：
   
   ```bash
   lrelease ./Translation/SMake.pro
   ```

#### 添加新语言：

1. 在`./Translation/SMake.pro`的“TRANSLATIONS”列表中添加新翻译文件的名称

2. 按上文更新翻译
