import wikipedia
from markdownify import markdownify as md
from opencc import OpenCC
from bs4 import BeautifulSoup
import requests
import os
import threading
import tkinter as tk
from tkinter import messagebox
import re

# 繁体→简体转换器
cc = OpenCC('t2s')

# 正则模式
REF_HEADING_RE = re.compile(r'^#{1,6}\s*(参考文献|References)', re.IGNORECASE)
# 匹配脚注引用，如 [[7]](#cite_note-...)
CITE_RE = re.compile(r"\[\[(\d+)\]\]\(#cite_note-[^)]+\)")
# 匹配普通外部链接
LINK_RE = re.compile(r"\[([^\]]+)\]\((?!#)[^)]+\)")
# 匹配内部锚点链接（#开头）
ANCHOR_RE = re.compile(r"\[([^\]]+)\]\(#[^)]+\)")


def fetch_content(source: str, by_title: bool, lang: str):
    """按词条或URL获取页面标题和HTML内容"""
    wikipedia.set_lang(lang)
    if by_title:
        page = wikipedia.page(source)
        return page.title, page.html()
    resp = requests.get(source)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    title = soup.find(id='firstHeading').get_text()
    html = str(soup.find('div', id='mw-content-text'))
    return title, html


def process_html(title: str, html: str, lang: str, output_dir: str = 'output') -> str:
    """
    清理HTML，下载并重命名图片，转换为Markdown，处理链接与脚注
    """
    soup = BeautifulSoup(html, 'html.parser')
    for span in soup.select('.mw-editsection'):
        span.decompose()

    # 下载并本地化图片
    img_dir = os.path.join(output_dir, 'images')
    os.makedirs(img_dir, exist_ok=True)
    for idx, img in enumerate(soup.find_all('img'), start=1):
        src = img.get('src') or img.get('data-src')
        if not src:
            continue
        url = src if src.startswith('http') else (
            'https:' + src if src.startswith('//') else f'https://{lang}.wikipedia.org' + src
        )
        ext = os.path.splitext(url.split('?')[0])[1]
        new_name = f"{title.replace('/', '_')}_{idx}{ext}"
        local_rel = os.path.join('images', new_name)
        full_path = os.path.join(output_dir, local_rel)
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            with open(full_path, 'wb') as f:
                f.write(r.content)
            img['src'] = local_rel
        except Exception:
            continue

    # 转为Markdown并简体化
    text = md(str(soup))
    if lang == 'zh':
        text = cc.convert(text)

    # 分离正文与参考文献
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if REF_HEADING_RE.match(line):
            main, ref = '\n'.join(lines[:i]), '\n'.join(lines[i:])
            break
    else:
        main, ref = text, ''

    # 去除红链及“页面不存在”提示
    main = re.sub(r"\[([^\]]+)\]\([^)]*redlink=1[^)]*\)", '', main)
    main = re.sub(r"&action=edit&redlink=1[^\s]*", '', main)
    main = re.sub(r"（页面不存在）", '', main)

    # 图片链接转换为 ![[词条_序号]]
    main = re.sub(
        r"!\[([^\]]+?)\]\(images/([^\)]+?)\)",
        lambda m: f"![[{title.replace('/', '_')}_{m.group(2).split('_')[-1].split('.')[0]}]]",
        main
    )
    # 脚注引用转换，如 [[7]](...) -> $^{7}$
    main = CITE_RE.sub(lambda m: f"$^{{{m.group(1)}}}$", main)
    # 移除所有内部锚点链接，转换为加粗文本
    main = ANCHOR_RE.sub(lambda m: f"**{m.group(1)}**", main)
    # 外部链接转换为加粗文本
    main = LINK_RE.sub(lambda m: f"**{m.group(1)}**", main)

    # 参考文献区块处理
    if ref:
        ref = re.sub(r"\[([^\]]+)\]\([^)]*redlink=1[^)]*\)", '', ref)
        ref = CITE_RE.sub(lambda m: f"$^{{{m.group(1)}}}$", ref)
        ref = ANCHOR_RE.sub(lambda m: f"**{m.group(1)}**", ref)
        ref = LINK_RE.sub(lambda m: f"**{m.group(1)}**", ref)

    # 写入Markdown文件
    safe_title = title.replace('/', '_')
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"{safe_title}.md")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f"# {title}\n\n{main}\n{ref}")
    return path


def run_export(entry: str, mode: str, lang: str):
    """
    启动导出流程
    """
    by_title = (mode == 'title')
    title, html = fetch_content(entry, by_title, lang)
    return process_html(title, html, lang)


def on_fetch():
    """GUI 触发：读取输入并启动后台任务"""
    entry = entry_input.get().strip()
    if not entry:
        messagebox.showwarning('输入错误', '请填写词条或URL。')
        return
    btn_fetch.config(state='disabled')
    status_label.config(text='⏳ 处理中…')

    def update_status(status: str):
        """在主线程更新GUI状态"""
        status_label.config(text=status)
        btn_fetch.config(state='normal')

    def task():
        try:
            out = run_export(entry, mode_var.get(), lang_var.get())
            status = f'✅ 成功：{out}'
        except Exception as e:
            status = f'❌ 错误：{e}'
        root.after(0, lambda: update_status(status))

    threading.Thread(target=task, daemon=True).start()

# GUI 界面初始化
root = tk.Tk()
root.title('维基导出工具')
root.geometry('500x260')
root.resizable(False, False)

frame = tk.Frame(root, padx=15, pady=15)
frame.pack(fill=tk.BOTH, expand=True)

mode_var = tk.StringVar(value='title')
tk.Radiobutton(frame, text='按词条搜索', variable=mode_var, value='title').grid(row=0, column=0, sticky='w')
tk.Radiobutton(frame, text='按页面URL', variable=mode_var, value='url').grid(row=0, column=1, sticky='w')

tk.Label(frame, text='词条或URL：').grid(row=1, column=0, pady=8, sticky='e')
entry_input = tk.Entry(frame, width=40)
entry_input.grid(row=1, column=1, columnspan=2, pady=8)

lang_var = tk.StringVar(value='zh')
tk.Label(frame, text='语言：').grid(row=2, column=0, sticky='e')
tk.Radiobutton(frame, text='中文', variable=lang_var, value='zh').grid(row=2, column=1)
tk.Radiobutton(frame, text='English', variable=lang_var, value='en').grid(row=2, column=2)

btn_fetch = tk.Button(frame, text='开始导出', width=12, command=on_fetch)
btn_fetch.grid(row=3, column=1, pady=15)
status_label = tk.Label(frame, text='', wraplength=460, justify='left')
status_label.grid(row=4, column=0, columnspan=3)

root.mainloop()
