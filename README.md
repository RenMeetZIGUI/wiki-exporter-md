# 项目自述

## 功能概述

本程序是一款基于 **Python** 的 **维基百科文章导出工具**，支持：

1. **按词条搜索** 或 **按页面 URL** 两种模式抓取内容。
2. 将抓取到的 HTML 内容转换为 **Markdown (`.md`)** 格式。
3. 针对中文页面，自动进行 **繁体→简体** 转换。
4. 删除页面上的编辑按钮，并将 **内部维基链接** 转换为 `[[…]]` 双链。
5. 排除多余的媒体文件链接，保留纯文本。
6. 对所有其他外部链接，替换为 **粗体文本**。
7. 将脚注格式 `[[1]](#cite_note-1)` 转换为 `$^1$`。
8. 保留目录中的内部锚点链接（例如 `[1 历史发展](#历史发展)`）。
9. 自动下载页面中所有图片，保存在 `output/images/` 目录，并在 Markdown 中使用相对路径引用。

## 环境与依赖

* **Python 版本**：建议使用 Python **3.7+**。
* **第三方库**：

  * `wikipedia`             （抓取维基 API）
  * `markdownify`           （HTML→Markdown）
  * `opencc-python-reimplemented` （繁体→简体）
  * `beautifulsoup4`        （HTML 解析）
  * `requests`              （网络请求）
  * `tkinter` （标准库，自带 GUI）

### 安装命令

```bash
python -m pip install wikipedia markdownify opencc-python-reimplemented beautifulsoup4 requests
```

## 使用说明

1. 将本脚本保存为 **`wiki_gui.py`**。
2. 在命令行（PowerShell、Terminal 等）中，进入脚本所在目录。
3. 确保已安装上述依赖。
4. 运行：

   ```bash
   python wiki_gui.py
   ```
5. 在弹出的窗口中：

   * 选择 **模式**：

     * `按词条搜索`：输入词条名称（中文或英文）。
     * `按页面 URL`：粘贴完整维基百科页面链接。
   * 选择 **语言**：`中文` 或 `English`。
   * 点击 **开始导出**。
6. 导出完成后，查看 **output/** 目录，获取生成的 `.md` 文件及 `images/` 子目录。

## 注意事项

* **网络连接**：程序需要联网访问维基百科及下载图片。
* **防重名**：若多次导出同一词条，会覆盖已有文件。
* **长页面**：对于大页面，转换过程可能稍慢，请耐心等待。
* **脚注与参考文献**：仅对可识别的脚注做转换，复杂引用样式可能需人工调整。

## 制作者

* **脚本撰写**：ChatGPT （OpenAI o4-mini）
* **需求及优化**：vyen

---

欢迎反馈及改进！

