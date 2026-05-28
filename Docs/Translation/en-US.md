# Internationalization Support

[Back](../../README.md)

This program uses the QTranslator translation support framework.

#### Updating Translations:

1. Generate translation files:
   
   ```bash
   # First remove the old Chinese translation, then regenerate it
   rm ./Translation/zh_CN.ts
   # Use pylupdate5 to automatically process translation file generation and updates
   pylupdate5 ./Translation/SMake.pro
   # Note: For zh_cn, since it is the program's native language, no translation is needed.
   # You can use this Python script to quickly complete it:
   python ./Translation/auto_translate_zh_cn.py ./Translation/zh_CN.ts
   ```

2. Use Qt Linguist or manually edit translation files other than `zh_CN`

3. Compile to generate .qm files:
   
   ```bash
   lrelease ./Translation/SMake.pro
   ```

#### Adding a New Language:

1. Add the name of the new translation file to the "TRANSLATIONS" list in `./Translation/SMake.pro`

2. Update translations as described above
