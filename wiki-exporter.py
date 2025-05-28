import wikipedia
from markdownify import markdownify as md
from opencc import OpenCC
from bs4 import BeautifulSoup
import requests
import os
import threading
import tkinter as tk
from tkinter import messagebox
import re  # 正则库

# 初始化繁体→简体转换
cc = OpenCC('t2s')

# 正则：参考文献标题检测
REF_HEADING_RE = re.compile(r'^#{1,6}\s*(参考文献|References)', re.IGNORECASE)
# 正则：脚注引用[[1]](#cite_note-1)
CITE_RE = re.compile(r"\[\[(\d+)\]\]\(#cite_note-\d+\)")

def fetch_by_title(title, lang, output_dir='output'):
    wikipedia.set_lang(lang)
    page = wikipedia.page(title)
    return page.title, page.html()

def fetch_by_url(url):
    # 只支持 Wikipedia 页面
    resp = requests.get(url)
    resp.raise_for_status()
    page = BeautifulSoup(resp.text, 'html.parser')
    title = page.find(id='firstHeading').get_text()
    content_div = page.find('div', id='mw-content-text')
    return title, str(content_div)

def process_html(title, html_content, lang, output_dir='output'):
    # 清理编辑按钮
    soup = BeautifulSoup(html_content, 'html.parser')
    for span in soup.find_all('span', class_='mw-editsection'):
        span.decompose()

    # 图片本地化
    img_dir = os.path.join(output_dir, 'images')
    os.makedirs(img_dir, exist_ok=True)
    for img in soup.find_all('img'):
        src = img.get('src') or img.get('data-src')
        if not src:
            continue
        if src.startswith('//'):
            url = 'https:' + src
        elif src.startswith('/'):
            domain = f'https://{lang}.wikipedia.org'
            url = domain + src
        else:
            url = src
        fname = os.path.basename(url.split('?')[0])
        local_rel = os.path.join('images', fname)
        full_path = os.path.join(output_dir, local_rel)
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            with open(full_path, 'wb') as f:
                f.write(r.content)
            img['src'] = local_rel
        except:
            continue

    # 转 Markdown
    md_text = md(str(soup))
    # 繁转简
    if lang == 'zh':
        md_text = cc.convert(md_text)

    # 拆分参考文献区
    lines = md_text.splitlines()
    idx_ref = len(lines)
    for i, l in enumerate(lines):
        if REF_HEADING_RE.match(l):
            idx_ref = i
            break
    main = '\n'.join(lines[:idx_ref])
    ref = '\n'.join(lines[idx_ref:])

    # 主体链接处理
    # 媒体链接
    main = re.sub(r"\[([^\]]+)\]\(//upload\.wikimedia\.org[^)]+\)", r"\1", main)
    # 内部 Wiki 链接转 [[text]]
    main = re.sub(r"\[([^\]]+)\]\(/wiki/[^)]+(?: \"[^\"]*\")?\)", r"[[\1]]", main)
    # 去除其他链接（非 # 开头的链接），替换为粗体文本；保留锚点链接如 [1 标题](#标题)
    main = re.sub(r"\[([^\]]+)\]\((?!#)[^)]+\)", r"**\1**", main)
    # 脚注引用[[1]](#cite_note-1) 转为 $^1$
    main = CITE_RE.sub(lambda m: f"${{^{m.group(1)}}}$" , main)

    # 参考文献：去除 redlink
    if ref:
        ref = re.sub(r"\[([^\]]+)\]\([^)]*redlink=1[^)]*\)", '', ref)
        # 脚注引用在参考文献段也转换
        ref = CITE_RE.sub(lambda m: f"${{^{m.group(1)}}}$", ref)

    # 写文件
    safe = title.replace('/', '_')
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"{safe}.md")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f"# {title}\n\n")
        f.write(main + ('\n' + ref if ref else ''))
    return path

def on_fetch():
    mode = var_mode.get()
    lang = var_lang.get()
    entry_text = entry.get().strip()
    if not entry_text:
        messagebox.showwarning("输入错误", "请填写词条或URL。")
        return
    btn_fetch.config(state='disabled')
    lbl_status.config(text="⏳ 处理中…")

    def task():
        try:
            if mode == 'title':
                title, html = fetch_by_title(entry_text, lang)
            else:
                title, html = fetch_by_url(entry_text)
            out = process_html(title, html, lang)
            msg = f"✅ 成功：{out}"
        except Exception as e:
            msg = f"❌ 错误：{e}"
        lbl_status.config(text=msg)
        btn_fetch.config(state='normal')

    threading.Thread(target=task, daemon=True).start()

# GUI
root = tk.Tk()
root.title("维基导出工具")
root.geometry("500x260")
root.resizable(False, False)

frame = tk.Frame(root, padx=15, pady=15)
frame.pack(fill=tk.BOTH, expand=True)

# 模式选择
var_mode = tk.StringVar(value='title')
mode_title = tk.Radiobutton(frame, text='按词条搜索', variable=var_mode, value='title')
mode_url = tk.Radiobutton(frame, text='按页面URL', variable=var_mode, value='url')
mode_title.grid(row=0, column=0, sticky='w')
mode_url.grid(row=0, column=1, sticky='w')

# 输入
tk.Label(frame, text='词条或URL：').grid(row=1, column=0, pady=8, sticky='e')
entry = tk.Entry(frame, width=40)
entry.grid(row=1, column=1, columnspan=2, pady=8)

# 语言
var_lang = tk.StringVar(value='zh')
tk.Label(frame, text='语言：').grid(row=2, column=0, sticky='e')
lang_ch = tk.Radiobutton(frame, text='中文', variable=var_lang, value='zh')
lang_en = tk.Radiobutton(frame, text='English', variable=var_lang, value='en')
lang_ch.grid(row=2, column=1)
lang_en.grid(row=2, column=2)

# 抓取按钮
btn_fetch = tk.Button(frame, text='开始导出', width=12, command=on_fetch)
btn_fetch.grid(row=3, column=1, pady=15)

# 状态
lbl_status = tk.Label(frame, text='', wraplength=460, justify='left')
lbl_status.grid(row=4, column=0, columnspan=3)

root.mainloop()